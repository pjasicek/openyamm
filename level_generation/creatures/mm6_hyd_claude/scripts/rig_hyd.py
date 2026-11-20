"""Hydra rig on a hydra mesh in the rig frame (1 m tall, ground z 0, heads -Y): one body chain + five neck chains.

- Necks: mesh pieces above Z_SPLIT (connected through vertices above it) are the five necks. Each is traced by marching
  slabs (as mm6_seas_claude/rig_seas.py) from its lowest part upward, restricted to its own vertices; the last
  HEAD_LEN of the trace is one head bone. Each neck is then traced downward from its lowest point (continuing its
  lower direction) through its own surface region until the trace reaches LOW_Z. Regions: geodesic distance over the
  mesh from seeds (each neck piece, the body behind BODY_SEED_Y); on the 200k mesh a middle neck's trace through all
  low vertices wandered into a neighbour's run: the outer necks
  curve down to the ground at the ends of the body's U, and a straight stub to the body let the neighbouring neck's
  base claim their lower half (weights and tier regions).
- Body: from the tail tip (the low vertex farthest from the neck bases) by marching through the low vertices toward
  the root (centroid of the neck bases at BASE_Z), stopping within ROOT_STOP of it.
- Bones: Body_Root at the root; Tail_01.. outward to the tip (parents toward the root); Neck<k>_00 (base) parented to
  the nearest body bone, Neck<k>_01.., Head<k>. Neck k is numbered left to right in the front view (x ascending).
- Weights: each vertex belongs to the chain of its geodesically nearest seed (below); nearest segment of that chain,
  blended linearly with the neighbouring segment of the same chain by the
  position along it (partition of unity, no heat weights).
Writes work/rig_v1.blend (Hydra + Hydra_Rig) and work/rig.json for anim_hyd.py."""
import bpy, json, os, math
import numpy as np
from mathutils import Vector
import heapq

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z_SPLIT, LOW_Z, HEAD_LEN, SEG = 0.32, 0.16, 0.13, 0.075
STEP, SLAB, REACH, MAX_TURN, ROOT_STOP, DROP = 0.03, 0.016, 0.16, math.radians(28), 0.1, 0.05
BODY_SEED_Y = 0.45
mesh = bpy.data.objects['Hydra']; me = mesh.data
co = np.array([tuple(v.co) for v in me.vertices])
adj = [[] for _ in co]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)

# ---- neck pieces ---------------------------------------------------------------------------------------------------
up = co[:, 2] > Z_SPLIT; lab = -np.ones(len(co), int); pieces = []
for v in np.nonzero(up)[0]:
    if lab[v] >= 0:
        continue
    stack = [v]; lab[v] = len(pieces); members = []
    while stack:
        a = stack.pop(); members.append(a)
        for b in adj[a]:
            if up[b] and lab[b] < 0:
                lab[b] = len(pieces); stack.append(b)
    pieces.append(np.array(members))
pieces = sorted(pieces, key=len, reverse=True)[:5]
pieces.sort(key=lambda m: co[m, 0].mean())


def geodesic_labels(seed_sets):
    """Label of the geodesically nearest seed set for every vertex (multi-source Dijkstra over mesh edges)."""
    dist = np.full(len(co), np.inf); label = np.full(len(co), -1); heap = []
    for lab_, seeds in enumerate(seed_sets):
        heap += [(0.0, int(v), lab_) for v in seeds]
    heapq.heapify(heap)
    while heap:
        d, v, lab_ = heapq.heappop(heap)
        if d >= dist[v]:
            continue
        dist[v] = d; label[v] = lab_
        for b in adj[v]:
            nd = d + float(np.linalg.norm(co[b] - co[v]))
            if nd < dist[b]:
                heapq.heappush(heap, (nd, b, lab_))
    return label


region0 = geodesic_labels([np.nonzero((co[:, 1] > BODY_SEED_Y) & (co[:, 2] < Z_SPLIT))[0]] + pieces)


def march(points, start, direction, stop=None, climbing=False, low_z=None, no_turn_back=False):
    """climbing (necks): stop once the trace has dropped DROP below its highest point (it passed the head and the
    crest pulled it back down)."""
    p = np.array(start, float); d = np.array(direction, float); d /= np.linalg.norm(d)
    out, rad = [p.copy()], []; top = p[2]
    for _ in range(300):
        q = p + STEP * d; rel = points - q
        s = points[(np.abs(rel @ d) < SLAB) & (np.linalg.norm(rel, axis=1) < REACH)]
        if len(s) < 5:
            break
        c = (s.min(0) + s.max(0)) / 2; c = c - ((c - q) @ d) * d
        nd = (c - p) / np.linalg.norm(c - p)
        ang = math.acos(max(-1.0, min(1.0, float(nd @ d))))
        if ang > MAX_TURN:
            axis = np.cross(d, nd); axis /= np.linalg.norm(axis)
            nd = d * math.cos(MAX_TURN) + np.cross(axis, d) * math.sin(MAX_TURN); c = p + STEP * nd
        if climbing and c[2] < top - DROP:
            break
        if no_turn_back and nd @ np.asarray(direction, float) < 0:
            break                                       # circling back at the end of its region
        top = max(top, c[2])
        if low_z is not None and c[2] < low_z:
            break
        out.append(c.copy()); rad.append(float(np.median(np.linalg.norm(s - c, axis=1))))
        d, p = nd, c
        if stop is not None and np.linalg.norm(p - stop) < ROOT_STOP:
            break
    rad = [rad[0] if rad else 0.05] + rad
    return np.array(out), np.array(rad)


def resample(pts, rad, seg, head_len=0.0):
    for _ in range(2):
        p2, r2 = [pts[0]], [rad[0]]
        for a, b, ra, rb in zip(pts[:-1], pts[1:], rad[:-1], rad[1:]):
            p2 += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]; r2 += [0.75 * ra + 0.25 * rb, 0.25 * ra + 0.75 * rb]
        p2.append(pts[-1]); r2.append(rad[-1]); pts, rad = np.array(p2), np.array(r2)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    end = arc[-1] - head_len
    n = max(1, int(round(end / seg)))
    samp = np.linspace(0, end, n + 1)
    if head_len > 0:
        samp = np.append(samp, arc[-1])
    return np.stack([np.interp(samp, arc, pts[:, i]) for i in range(3)], 1), np.interp(samp, arc, rad)


necks = []
for k, m in enumerate(pieces):
    pc = co[m]
    low = pc[pc[:, 2] < pc[:, 2].min() + 0.03]
    start = (low.min(0) + low.max(0)) / 2
    pts, rad = march(pc, start, (0, 0, 1), climbing=True)
    while len(pts) > 3 and pts[-1][2] < pts[:-1, 2].max() - 0.02:      # trim the descending end
        pts, rad = pts[:-1], rad[:-1]
    # snout: the piece's vertex farthest along the last direction
    d = pts[-1] - pts[-3]; d /= np.linalg.norm(d)
    tip = pc[np.argmax((pc - pts[-1]) @ d)]
    pts = np.vstack([pts, tip]); rad = np.append(rad, 0.03)
    d0 = pts[0] - pts[min(2, len(pts) - 1)]; d0 /= np.linalg.norm(d0)
    down, drad = march(co[region0 == k + 1], pts[0], d0, low_z=LOW_Z, no_turn_back=True)
    pts = np.vstack([down[:0:-1], pts]); rad = np.concatenate([drad[:0:-1], rad])
    J, R = resample(pts, rad, SEG, HEAD_LEN)
    necks.append((J, R))
root = np.mean([J[0] for J, _ in necks], axis=0)

# ---- body ----------------------------------------------------------------------------------------------------------
lowv = co[co[:, 2] < Z_SPLIT - 0.06]
tip = lowv[np.argmax(np.linalg.norm(lowv[:, :2] - root[:2], axis=1))]
body_pts, body_rad = march(lowv, tip, root - tip, stop=root)
body_pts = np.vstack([body_pts, root]); body_rad = np.append(body_rad, body_rad[-1])
BJ, BR = resample(body_pts[::-1], body_rad[::-1], SEG)           # root first, tail tip last
print('BODY length %.3f joints %d; NECKS' % (np.linalg.norm(np.diff(BJ, axis=0), axis=1).sum(), len(BJ)),
      [len(J) for J, _ in necks])

# ---- armature ------------------------------------------------------------------------------------------------------
arm = bpy.data.armatures.new('Hydra_Rig'); rig = bpy.data.objects.new('Hydra_Rig', arm)
bpy.context.scene.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
chains = []          # (bone names, joints, radii, parent bone name or None)
body_names = ['Body_Root'] + [f'Tail_{i:02d}' for i in range(1, len(BJ) - 1)]
eb = {}
for i, nm in enumerate(body_names):
    b = arm.edit_bones.new(nm); b.head, b.tail = Vector(BJ[i]), Vector(BJ[i + 1]); b.align_roll(Vector((0, 0, 1)))
    if i:
        b.parent = eb[body_names[i - 1]]
    b.use_connect = False; eb[nm] = b
chains.append((body_names, BJ, BR, None))
for k, (J, R) in enumerate(necks, 1):
    names = [f'Neck{k}_{i:02d}' for i in range(len(J) - 2)] + [f'Head{k}']
    near = int(np.argmin(np.linalg.norm(BJ[:-1] - J[0], axis=1)))
    for i, nm in enumerate(names):
        b = arm.edit_bones.new(nm); b.head, b.tail = Vector(J[i]), Vector(J[i + 1]); b.align_roll(Vector((1, 0, 0)))
        b.parent = eb[body_names[near]] if i == 0 else eb[names[i - 1]]
        b.use_connect = False; eb[nm] = b
    chains.append((names, J, R, body_names[near]))
bpy.ops.object.mode_set(mode='OBJECT')

# ---- weights -------------------------------------------------------------------------------------------------------
per_chain = []                                          # (distance in radii, segment, t) per chain
for c, (names, J, R, _) in enumerate(chains):
    best = np.full(len(co), 1e9); seg = np.zeros(len(co), int); tt = np.zeros(len(co))
    for i in range(len(names)):
        a, b = J[i], J[i + 1]; d = b - a
        t = np.clip(((co - a) @ d) / (d @ d), 0, 1)
        dist = np.linalg.norm(co - (a + t[:, None] * d), axis=1) / max(R[i], 0.02)   # relative to body radius
        m = dist < best
        best[m] = dist[m]; seg[m] = i; tt[m] = t[m]
    per_chain.append((best, seg, tt))
# chain ownership by geodesic distance over the surface from seeds (each neck above Z_SPLIT, the body behind
# BODY_SEED_Y, by nearest segment): the outer necks run along the ground into the root under the other necks' bases,
# where the nearest segment handed their lower halves to a neighbouring neck
nearest_chain = np.argmin(np.array([p[0] for p in per_chain]), axis=0)
seeds = np.nonzero(((nearest_chain > 0) & (co[:, 2] > Z_SPLIT)) | ((nearest_chain == 0) & (co[:, 1] > BODY_SEED_Y)))[0]
dist = np.full(len(co), np.inf); source = np.full(len(co), -1); heap = [(0.0, int(v), int(v)) for v in seeds]
while heap:
    d, v, src = heapq.heappop(heap)
    if d >= dist[v]:
        continue
    dist[v] = d; source[v] = src
    for b in adj[v]:
        nd = d + float(np.linalg.norm(co[b] - co[v]))
        if nd < dist[b]:
            heapq.heappush(heap, (nd, b, src))
owner = nearest_chain[np.maximum(source, 0)]
seg_of = np.array([per_chain[owner[v]][1][v] for v in range(len(co))])
t_of = np.array([per_chain[owner[v]][2][v] for v in range(len(co))])
groups = {nm: mesh.vertex_groups.new(name=nm) for names, *_ in chains for nm in names}
for v in range(len(co)):
    names = chains[owner[v]][0]; i = seg_of[v]; t = t_of[v]
    other = i + 1 if t > 0.5 else i - 1
    if 0 <= other < len(names):
        w = abs(t - 0.5)                                  # 0 at the segment middle, 0.5 at its ends
        groups[names[i]].add([v], 1.0 - w, 'REPLACE'); groups[names[other]].add([v], w, 'REPLACE')
    else:
        groups[names[i]].add([v], 1.0, 'REPLACE')
mesh.parent = rig
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
json.dump({'chains': [{'names': n, 'joints': J.round(5).tolist(), 'radius': R.round(4).tolist(), 'parent': p}
                      for n, J, R, p in chains]}, open(os.path.join(HERE, 'work', 'rig.json'), 'w'), indent=1)
print('RIG bones', sum(len(n) for n, *_ in chains), 'unweighted', sum(1 for v in me.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
