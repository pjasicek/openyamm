#!/usr/bin/env python3
"""Trace a bare tree's branch skeleton from its sprite (work/dead_<id>/skeleton.json, skeleton.png).

The MM7 bare trees draw every limb, so the model follows the drawing: the sprite's opaque mask (alpha >= 96, pin
holes filled) is thinned (Zhang-Suen), the thin lines become a graph (junction clusters, tips, segments between them;
short spurs pruned, pass-through nodes dissolved), rooted at the lowest tip (the trunk foot, extended to the ground).
Branches that cross in the drawing close loops: the shortest-path tree from the root keeps one way round, and every
other segment is split at its middle into two dangling twigs. Axes then follow the botany: at every fork the child
that is thickest and best aligned continues the parent's axis, the others start new axes (level + 1).
Radius per point = the distance transform there (pixels -> metres), with the junction bulge near forks replaced by
the radius just beyond it, median-smoothed, never growing toward the tip.
Output (metres, x right, z up, origin on the ground under the trunk foot): axes [{points [[x, z]], radii, parent,
level}], children listed after their parents. Usage: trace_skeleton.py <id>"""
import heapq, json, math, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import dead_common as dc

spec = dc.load(); W = spec['work']
TR = spec.get('trace', {})


def thin(img):
    img = img.astype(np.uint8).copy()
    while True:
        changed = False
        for step in (0, 1):
            P = np.pad(img, 1)
            p2, p3, p4, p5 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:], P[2:, 2:]
            p6, p7, p8, p9 = P[2:, 1:-1], P[2:, :-2], P[1:-1, :-2], P[:-2, :-2]
            seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            B = sum(seq[:8].__iter__())
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                c = ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0)
            else:
                c = ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0)
            m = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if m.any():
                img[m] = 0; changed = True
        if not changed:
            return img.astype(bool)


rgba = np.asarray(Image.open(spec['sprite_path']).convert('RGBA'))
mask = rgba[..., 3] >= 96
lab, _ = ndimage.label(mask, structure=np.ones((3, 3)))
sizes = np.bincount(lab.ravel()); sizes[0] = 0
mask = lab == sizes.argmax()
holes, nh = ndimage.label(~mask)
hs = np.bincount(holes.ravel())
for k in range(1, nh + 1):
    if hs[k] < TR.get('fill_holes', 14) and not (holes[0] == k).any() and not (holes[-1] == k).any():
        mask[holes == k] = True
# the trunk runs off the bottom edge: pad it downward so the thinned trunk and its radius reach the ground
pad = 40
ext = np.vstack([mask, np.repeat(mask[-1:], pad, 0)])
dist = ndimage.distance_transform_edt(np.pad(ext, 1))[1:-1, 1:-1][:mask.shape[0]]
sk = thin(np.pad(ext, 1))[1:-1, 1:-1][:mask.shape[0]]
rows = np.where(mask.any(1))[0]; TOP, BOTTOM = int(rows.min()), int(rows.max())
H_PX = BOTTOM - TOP + 1
MPP = spec['height_m'] / H_PX

# ---------------------------------------------------------------- pixel graph
ys, xs = np.nonzero(sk)
pix = set(zip(ys.tolist(), xs.tolist()))
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def nbrs(p):
    return [(p[0] + dy, p[1] + dx) for dy, dx in N8 if (p[0] + dy, p[1] + dx) in pix]


deg = {p: len(nbrs(p)) for p in pix}
junction = {p for p in pix if deg[p] >= 3}
# junction clusters: 8-connected junction pixels, merged when within 2 px
cluster = {}
cid = 0
for p in junction:
    if p in cluster:
        continue
    stack = [p]; cluster[p] = cid
    while stack:
        q = stack.pop()
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                r = (q[0] + dy, q[1] + dx)
                if r in junction and r not in cluster:
                    cluster[r] = cid; stack.append(r)
    cid += 1
nodes = {}                      # node id -> {'p': (y, x), 'kind'}
for c in range(cid):
    m = [p for p, k in cluster.items() if k == c]
    nodes[c] = {'p': tuple(np.mean(m, 0)), 'kind': 'fork'}
# segments: connected runs of non-junction pixels
rest = pix - junction
seen = set(); edges = []
for start in rest:
    if start in seen:
        continue
    comp = []; stack = [start]; seen.add(start)
    while stack:
        q = stack.pop(); comp.append(q)
        for r in nbrs(q):
            if r in rest and r not in seen:
                seen.add(r); stack.append(r)
    cset = set(comp)
    ends = [q for q in comp if sum(r in cset for r in nbrs(q)) <= 1]
    if not ends:
        continue                # an isolated loop
    # walk from one end
    path = [ends[0]]; prev = None
    while True:
        nxt = [r for r in nbrs(path[-1]) if r in cset and r != prev and r not in path[-3:]]
        if not nxt:
            break
        prev = path[-1]; path.append(nxt[0])
        if len(path) > len(comp):
            break

    def touch(q):
        cs = {cluster[r] for r in nbrs(q) if r in cluster}
        return min(cs, key=lambda c: math.dist(nodes[c]['p'], q)) if cs else None

    a, b = touch(path[0]), touch(path[-1])
    if a is None:
        a = cid; nodes[a] = {'p': path[0], 'kind': 'tip'}; cid += 1
    if b is None:
        if len(path) == 1:
            b = a
        else:
            b = cid; nodes[b] = {'p': path[-1], 'kind': 'tip'}; cid += 1
    if a == b and len(path) < 3:
        continue
    edges.append({'a': a, 'b': b, 'px': [nodes[a]['p']] + path + [nodes[b]['p']]})


def length(px):
    return float(np.linalg.norm(np.diff(np.array(px, float), axis=0), axis=1).sum())


def r_at(p):
    return float(dist[min(int(round(p[0])), dist.shape[0] - 1), min(int(round(p[1])), dist.shape[1] - 1)])


def incident(n):
    return [e for e in edges if e['a'] == n or e['b'] == n]


def dissolve():
    """Merge the two segments of every pass-through fork node (degree 2)."""
    changed = True
    while changed:
        changed = False
        for n in list(nodes):
            if nodes[n]['kind'] != 'fork':
                continue
            inc = incident(n)
            if len(inc) == 0:
                del nodes[n]; changed = True; continue
            if len(inc) != 2 or inc[0] is inc[1]:
                continue
            e1, e2 = inc
            p1 = e1['px'] if e1['b'] == n else e1['px'][::-1]
            p2 = e2['px'] if e2['a'] == n else e2['px'][::-1]
            a = e1['a'] if e1['b'] == n else e1['b']; b = e2['b'] if e2['a'] == n else e2['a']
            edges.remove(e1); edges.remove(e2)
            edges.append({'a': a, 'b': b, 'px': p1 + p2[1:]})
            del nodes[n]; changed = True


dissolve()
# prune spurs: tip segments shorter than the fork's radius (bumps on thick limbs) go
for _ in range(4):
    gone = []
    for e in edges:
        for fork, tip in ((e['a'], e['b']), (e['b'], e['a'])):
            if nodes[tip]['kind'] == 'tip' and nodes[fork]['kind'] == 'fork' and len(incident(fork)) >= 3:
                if length(e["px"]) < max(3.0, 1.15 * r_at(nodes[fork]["p"]) + 1.0):
                    gone.append((e, tip)); break
    if not gone:
        break
    for e, tip in gone:
        if e in edges:
            edges.remove(e); nodes.pop(tip, None)
    dissolve()

# root: the lowest tip (the trunk foot), pulled down to the ground row
root = max((n for n in nodes if nodes[n]['kind'] == 'tip'), key=lambda n: nodes[n]['p'][0])
for e in incident(root):
    if e['a'] == root:
        e['px'][0] = (float(BOTTOM), e['px'][0][1])
    else:
        e['px'][-1] = (float(BOTTOM), e['px'][-1][1])
nodes[root]['p'] = (float(BOTTOM), nodes[root]['p'][1])

# shortest-path tree from the root
adj = {}
for k, e in enumerate(edges):
    adj.setdefault(e['a'], []).append(k); adj.setdefault(e['b'], []).append(k)
_cost = {}


def edge_cost(k):
    """Path cost of a segment: its length over its thickness squared, so the tree from the root runs through the
    thick limbs and the loops of crossing branches open at their thinnest segment."""
    if k not in _cost:
        px = edges[k]['px']
        inner = px[len(px) // 4: max(len(px) // 4 + 1, 3 * len(px) // 4)]
        r = float(np.median([r_at(q) for q in inner]))
        _cost[k] = length(px) / max(r, 0.7) ** 2
    return _cost[k]


best = {root: 0.0}; via = {root: None}; heap = [(0.0, root)]
while heap:
    d, n = heapq.heappop(heap)
    if d > best.get(n, 1e18):
        continue
    for k in adj.get(n, []):
        e = edges[k]; m = e['b'] if e['a'] == n else e['a']
        nd = d + edge_cost(k)
        if nd < best.get(m, 1e18):
            best[m] = nd; via[m] = k; heapq.heappush(heap, (nd, m))
tree_edges = {k for k in via.values() if k is not None}
children = {}                    # node -> list of (pixel path from that node outward, child node or None)
for k, e in enumerate(edges):
    if e['a'] not in best or e['b'] not in best:
        continue                 # unreachable piece
    if k in tree_edges:
        child = e['b'] if via.get(e['b']) == k else e['a']
        parent = e['a'] if child == e['b'] else e['b']
        px = e['px'] if e['a'] == parent else e['px'][::-1]
        children.setdefault(parent, []).append((px, child))
    else:                        # a crossing in the drawing: two dangling halves
        px = e['px']; half = len(px) // 2
        if half >= 2:
            children.setdefault(e['a'], []).append((px[:half + 1], None))
            children.setdefault(e['b'], []).append((px[half:][::-1], None))
print('TRACE nodes', len(nodes), 'segments', len(edges), 'loops split', len(edges) - len(tree_edges))


def radii(px, start_r):
    """Distance-transform radii along a path, junction bulge at the start replaced, smoothed, non-increasing-ish."""
    p = np.array(px, float)
    r = np.array([r_at(q) for q in p]) - 0.35
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    beyond = np.searchsorted(s, start_r * 1.1)
    if beyond < len(r):
        r[:beyond] = r[beyond]
    elif start_r > 0:            # shorter than the fork's bulge: its own outer half decides
        r[:] = np.median(r[len(r) // 2:])
    r = ndimage.median_filter(r, size=5, mode='nearest')
    r = np.maximum(r, 0.45)
    return r


def direction(px, n=6):
    p = np.array(px[:n + 1], float)
    d = p[-1] - p[0]
    return d / max(np.linalg.norm(d), 1e-9)


axes = []


def subtree_size(node):
    tot = 0.0
    for px, ch in children.get(node, []):
        tot += length(px) * (np.mean([r_at(q) for q in px]) ** 2) + (subtree_size(ch) if ch is not None else 0)
    return tot


sizes = {}


def size(node):
    if node not in sizes:
        sizes[node] = subtree_size(node)
    return sizes[node]


def grow_axis(px0, child0, parent, level, cap=None):
    """Follow an axis from its first segment through forks (continuing into the best child), spawning side axes."""
    pts = list(px0); rad = list(radii(px0, r_at(px0[0]) if parent is not None else 0.0)); node = child0
    if cap is not None:          # a side axis is thinner than its parent where it leaves it
        rad = list(np.minimum(rad, cap))
    pending = []
    while node is not None and children.get(node):
        din = np.array(pts[-1], float) - np.array(pts[max(0, len(pts) - 8)], float)
        din /= max(np.linalg.norm(din), 1e-9)
        opts = children[node]
        rin = rad[-1]

        def score(o):
            px, ch = o
            r = np.median([r_at(q) for q in px[min(len(px) - 1, int(r_at(px[0]) * 1.2) + 1):][:12]] or [1.0])
            heft = r * r * length(px) + (size(ch) if ch is not None else 0)
            return (1.0 + float(np.dot(din, direction(px)))) * math.sqrt(heft + 1e-6)

        ranked = sorted(opts, key=score, reverse=True)
        main = ranked[0]
        for o in ranked[1:]:
            pending.append((o, len(pts) - 1))
        px, ch = main
        rr = radii(px, r_at(px[0]))
        rr = np.minimum(rr, rin * 1.05)
        pts += list(px[1:]); rad += list(rr[1:]); node = ch
    # thinning stops about a radius short of the drawn tip: extend the end along its last direction
    if len(pts) >= 3:
        end = np.array(pts[-1], float); d = end - np.array(pts[max(0, len(pts) - 5)], float)
        d /= max(np.linalg.norm(d), 1e-9)
        ext_px = min(rad[-1], 2.5) + 1.0
        pts.append(tuple(end + d * ext_px)); rad.append(max(rad[-1] * 0.7, 0.45))
    # an axis ending thick (a crossing split in the drawing, a pruned fork) tapers off instead of a blunt stump
    if rad[-1] > 1.2 and parent is not None:
        p = np.array(pts, float)
        s_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
        span = min(s_[-1] * 0.6, 8.0 * rad[-1])
        f = np.clip((s_[-1] - s_) / max(span, 1e-6), 0, 1)
        rad = list(np.array(rad) * (0.25 + 0.75 * f ** 0.7))
    k = len(axes)
    axes.append({'px': pts, 'r': rad, 'parent': parent, 'level': level})
    for (px, ch), at in pending:
        grow_axis(px, ch, k, level + 1, cap=0.85 * rad[at])


first = children[root]
assert len(first) >= 1
grow_axis(first[0][0], first[0][1], None, 0)
for px, ch in first[1:]:
    grow_axis(px, ch, 0, 1, cap=0.85 * axes[0]['r'][0])

# ---------------------------------------------------------------- output in metres
axis_x = None
trunk = np.array(axes[0]['px'], float)
foot = trunk[trunk[:, 0] > BOTTOM - H_PX * 0.08]
axis_x = float(foot[:, 1].mean())
out = []
for ax in axes:
    p = np.array(ax['px'], float)
    # resample every ~2.5 px (the build smooths further)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    n = max(2, int(math.ceil(s[-1] / 2.5)) + 1)
    ss = np.linspace(0, s[-1], n)
    y = np.interp(ss, s, p[:, 0]); x = np.interp(ss, s, p[:, 1]); r = np.interp(ss, s, np.array(ax['r'], float))
    out.append({'points': [[float((xx - axis_x) * MPP), float((BOTTOM - yy) * MPP)] for xx, yy in zip(x, y)],
                'radii': [float(v * MPP * TR.get('radius_scale', 1.2)) for v in r], 'parent': ax['parent'], 'level': ax['level'],
                'length_px': float(s[-1])})
json.dump({'mpp': MPP, 'height_px': H_PX, 'axis_px': axis_x, 'axes': out},
          open(os.path.join(W, 'skeleton.json'), 'w'))
levels = np.bincount([a['level'] for a in out])
print('TRACE axes', len(out), 'by level', levels.tolist(), 'total length m', round(sum(a['length_px'] for a in out) * MPP, 1),
      'trunk r m', round(out[0]['radii'][0], 3), 'mpp', round(MPP, 4))

# debug overlay: sprite faded, axes coloured by level
im = Image.new('RGBA', mask.shape[::-1], (235, 235, 240, 255))
sp = Image.fromarray(rgba).copy(); sp.putalpha(Image.fromarray((rgba[..., 3] * 0.35).astype(np.uint8)))
im.alpha_composite(sp)
d = ImageDraw.Draw(im)
COL = [(200, 0, 0), (0, 120, 220), (0, 160, 60), (200, 120, 0), (150, 0, 180), (90, 90, 90)]
for ax in axes:
    c = COL[min(ax['level'], len(COL) - 1)]
    pts = [(q[1], q[0]) for q in ax['px']]
    d.line(pts, fill=c + (255,), width=2)
    d.ellipse([pts[0][0] - 2, pts[0][1] - 2, pts[0][0] + 2, pts[0][1] + 2], outline=(0, 0, 0, 255))
im.resize((im.width * 2, im.height * 2), Image.NEAREST).convert('RGB').save(os.path.join(W, 'skeleton.png'))
