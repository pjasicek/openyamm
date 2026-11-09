"""Local mesh repairs of the m372 head for the face follow-up (coordinator, 2026-11-01), on a built pass GLB:

1. The spike: three head triangles share one vertex pulled 16 cm down to the hood (LOD0 3593, 3594, 3596; LOD1 the
   same fan). They draw a light line from the right mouth corner to the hood. They are removed, and the small triangle
   their other corners leave open is filled.
2. The cheek hole: a five-edge hole in the left cheek through which the head's inner walls showed as a wedge. It is
   filled.
3. The mouth opening between the lips (an open slit through which the inside of the head showed as black and pale
   shards) is closed with a surface painted as the slit's dark rose shadow.

Fills reuse the loop's vertices (copied: position, normal, joints and weights of a neighbouring copy, so they skin like
their neighbours) and are ear-clipped in the loop's best-fit plane, wound against their neighbours. Each fill gets a
small planar chart of its own in free atlas space (the hole's neighbours lie on several charts). The same 3D plane
maps the LOD1 fill, so both LODs share it. Skin fills are painted with the colours of the surrounding skin at the loop
(inverse-distance blend). The mouth fill is the slit colour. The normal is flat, the mask empty and the gloss skin's.
Applied to LOD0, LOD1 and their shadow copies; LOD2 and LOD3 keep their geometry, and their maps are transferred
again from the repaired LOD0.

Usage: fix_mesh.py <in glb> <out glb> [slit sRGB r,g,b]
Check: every original triangle not removed keeps its corner positions, normals, joints and weights; the normals of the
spike's three near corners are recomputed from the faces that remain (round 3: they kept the spike's tilt)."""
import json
import sys
import types
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb, png  # noqa: E402
import texlib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(HERE.parent / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

S = 2048
DENSITY = 2300.0                     # texels per metre (the face's)
MARGIN = 4
SPIKE_NEAR = np.array([-0.04, 1.49, 0.08])
CHEEK = np.array([0.032, 1.553, 0.097])
MOUTH = np.array([-0.007, 1.514, 0.112])
src, dst = sys.argv[1:3]
SLIT = np.array([float(v) for v in sys.argv[3].split(',')], np.float32) if len(sys.argv) > 3 else \
    np.array([110, 64, 60], np.float32)

g = Glb(src)
doc = g.doc
lod0 = doc['meshes'][0]
lods, shadows = lod0['extras']['openyamm_lods'], lod0['extras']['openyamm_shadow_lods']
report = {}


def mesh_data(mi):
    pr = doc['meshes'][mi]['primitives'][0]
    att = {k: g.accessor(v) for k, v in pr['attributes'].items()}
    return pr, att, g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)


def loops_of(tri, weld, faces_alive):
    """Boundary cycles (welded vertex ids, in the direction they appear in their faces) of the alive faces."""
    wt = weld[tri[faces_alive]]
    count = defaultdict(int)
    directed = {}
    for t in wt:
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            count[tuple(sorted((a, b)))] += 1
            directed[(a, b)] = True
    nxt = {}
    for (a, b) in directed:
        if count[tuple(sorted((a, b)))] == 1:
            nxt.setdefault(b, []).append(a)            # walk against the face direction: the fill's winding
    cycles, seen = [], set()
    for start in list(nxt):
        if start in seen or len(nxt[start]) != 1:
            continue
        cyc, v = [], start
        while v not in seen and v in nxt and len(nxt[v]) == 1:
            seen.add(v)
            cyc.append(v)
            v = nxt[v][0]
        if v == start and len(cyc) >= 3:
            cycles.append(cyc)
    return cycles


def plane(points):
    c = points.mean(0)
    _, _, vt = np.linalg.svd(points - c)
    return c, vt[0], vt[1], vt[2]


def ear_clip(p2):
    """Ear clipping of a simple polygon (N,2); returns triangles as index triples (counter-clockwise input)."""
    idx = list(range(len(p2)))
    out = []
    area = 0.5 * sum(p2[i, 0] * p2[(i + 1) % len(p2), 1] - p2[(i + 1) % len(p2), 0] * p2[i, 1] for i in idx)
    sign = 1 if area > 0 else -1
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        best = None
        for k in range(len(idx)):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            cross = (p2[b, 0] - p2[a, 0]) * (p2[c, 1] - p2[a, 1]) - (p2[b, 1] - p2[a, 1]) * (p2[c, 0] - p2[a, 0])
            if cross * sign <= 1e-14:
                continue
            ok = True
            for o in idx:
                if o in (a, b, c):
                    continue
                m = np.array([[p2[b, 0] - p2[a, 0], p2[c, 0] - p2[a, 0]], [p2[b, 1] - p2[a, 1], p2[c, 1] - p2[a, 1]]])
                try:
                    s_, t_ = np.linalg.solve(m, p2[o] - p2[a])
                except np.linalg.LinAlgError:
                    continue
                if s_ >= 0 and t_ >= 0 and s_ + t_ <= 1:
                    ok = False
                    break
            if ok:
                # prefer the fattest ear (no slivers)
                e = [np.linalg.norm(p2[a] - p2[b]), np.linalg.norm(p2[b] - p2[c]), np.linalg.norm(p2[c] - p2[a])]
                q = abs(cross) / max(max(e) ** 2, 1e-18)
                if best is None or q > best[0]:
                    best = (q, k, (a, b, c))
        if best is None:
            break
        out.append(best[2])
        idx.pop(best[1])
    if len(idx) == 3:
        out.append(tuple(idx))
        idx = []
    return out, idx


# ---- the fill charts: planes from LOD0's loops, placed in free atlas space
pr0, att0, tri0 = mesh_data(0)
pos0 = att0['POSITION'].astype(np.float64)
_, weld0 = np.unique(pos0.round(6), axis=0, return_inverse=True)
weld0 = weld0.ravel()
wpos0 = np.zeros((weld0.max() + 1, 3))
wpos0[weld0] = pos0


def find_spike(tri, weld, wpos):
    P = wpos[weld[tri]]
    e = np.linalg.norm(P[:, [1, 2, 0]] - P, axis=2).max(1)
    near = np.linalg.norm(P.mean(1) - SPIKE_NEAR, axis=1) < 0.03
    return np.nonzero((e > 0.12) & near)[0]


def pick_loops(tri, weld, wpos, alive):
    cycles = loops_of(tri, weld, alive)
    chosen = {}
    for name, centre, rad in (('cheek', CHEEK, 0.012), ('mouth', MOUTH, 0.03), ('spike', None, 0.0)):
        best = None
        for cyc in cycles:
            c = wpos[cyc].mean(0)
            if name == 'spike':
                continue
            d = np.linalg.norm(c - centre)
            if d < rad and (best is None or d < best[0]):
                best = (d, cyc)
        if best:
            chosen[name] = best[1]
    return cycles, chosen


spike0 = find_spike(tri0, weld0, wpos0)
alive0 = np.ones(len(tri0), bool)
alive0[spike0] = False
spike_corners = set(weld0[tri0[spike0]].ravel())
cycles0, chosen0 = pick_loops(tri0, weld0, wpos0, alive0)
# the spike's loop: the cycle made only of the spike faces' corners
for cyc in cycles0:
    if set(cyc) <= spike_corners and len(cyc) <= 6:
        chosen0['spike'] = cyc
report['lod0_spike_faces'] = spike0.tolist()
report['lod0_loops'] = {k: len(v) for k, v in chosen0.items()}
assert set(chosen0) == {'spike', 'cheek', 'mouth'}, chosen0.keys()

uv0 = att0['TEXCOORD_0'].astype(np.float64)
occ, _ = texlib.raster(uv0[tri0], S)
free = ~ndimage.binary_dilation(occ >= 0, iterations=MARGIN)
free[:MARGIN] = free[-MARGIN:] = False
free[:, :MARGIN] = free[:, -MARGIN:] = False
charts = {}
for name in ('mouth', 'spike', 'cheek'):
    pts = wpos0[chosen0[name]]
    c, ax, ay, n = plane(pts)
    q = np.stack([(pts - c) @ ax, (pts - c) @ ay], 1) * DENSITY
    lo = q.min(0) - 3
    w, h = (np.ceil(q.max(0) - lo) + 3).astype(int)
    integral = np.pad(np.cumsum(np.cumsum(free.astype(np.int32), 0), 1), ((1, 0), (1, 0)))
    win = integral[h:, w:] - integral[:-h, w:] - integral[h:, :-w] + integral[:-h, :-w]
    ys, xs = np.nonzero(win == w * h)
    assert len(ys), f'no free {w}x{h} window for the {name} fill'
    y0, x0 = int(ys[0]), int(xs[0])
    free[max(y0 - MARGIN, 0):y0 + h + MARGIN, max(x0 - MARGIN, 0):x0 + w + MARGIN] = False
    charts[name] = {'centre': c, 'ax': ax, 'ay': ay, 'lo': lo, 'origin': np.array([x0, y0], float), 'size': (w, h)}
    report[f'{name}_chart'] = {'px': [int(w), int(h)], 'at': [x0, y0]}


def chart_uv(name, p):
    ch = charts[name]
    q = np.stack([(p - ch['centre']) @ ch['ax'], (p - ch['centre']) @ ch['ay']], -1) * DENSITY
    return (q - ch['lo'] + ch['origin']) / S


# ---- paint the fill charts (before the far-LOD transfer reads LOD0)
mat = doc['materials'][pr0['material']]
pbr = mat['pbrMetallicRoughness']
tex = {'basecolor': pbr['baseColorTexture']['index'], 'metal_rough': pbr['metallicRoughnessTexture']['index'],
       'normal': mat['normalTexture']['index'], 'region_mask': mat['extras']['openyamm_region_mask']['index']}
imgs = {k: np.asarray(g.image(doc['textures'][v]['source']).convert('RGBA' if k == 'region_mask' else 'RGB'),
                      np.float32).copy() for k, v in tex.items()}
base = imgs['basecolor']
# loop vertex colours: the base colour at a neighbouring face's corner, nudged into that face
skin_mr = None
for name, ch in charts.items():
    cyc = chosen0[name]
    vcol, vpos = [], []
    for wv in cyc:
        faces = np.nonzero(alive0 & (weld0[tri0] == wv).any(1))[0]
        cols = []
        for f in faces[:8]:
            k = int(np.nonzero(weld0[tri0[f]] == wv)[0][0])
            u = uv0[tri0[f, k]] * 0.4 + uv0[tri0[f]].mean(0) * 0.6
            cols.append(texlib.bilinear(base, u[None])[0])
        vcol.append(np.median(cols, 0))
        vpos.append(wpos0[wv])
    vcol, vpos = np.array(vcol), np.array(vpos)
    w, h = ch['size']
    x0, y0 = ch['origin'].astype(int)
    yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]
    q = np.stack([xx + 0.5 - x0 + ch['lo'][0], yy + 0.5 - y0 + ch['lo'][1]], -1) / DENSITY
    p3 = ch['centre'] + q[..., :1] * ch['ax'] + q[..., 1:] * ch['ay']
    if name == 'mouth':
        col = np.broadcast_to(SLIT, p3.shape).copy()
    else:
        d = np.linalg.norm(p3[..., None, :] - vpos[None, None], axis=-1)
        wgt = 1.0 / np.maximum(d, 1e-4) ** 2
        col = (wgt[..., None] * vcol[None, None]).sum(-2) / wgt.sum(-1)[..., None]
    base[y0:y0 + h, x0:x0 + w] = col
    imgs['normal'][y0:y0 + h, x0:x0 + w] = (128, 128, 255)
    report[f'{name}_colour'] = np.round(col.reshape(-1, 3).mean(0), 1).tolist()
# gloss: the face skin's (metal/roughness may be smaller than the colour map)
mr = imgs['metal_rough']
sx = mr.shape[1] / S
face_f = np.nonzero(alive0 & (np.linalg.norm(wpos0[weld0[tri0]].mean(1) - np.array([-0.007, 1.54, 0.11]), axis=1) < 0.02))[0]
skin_mr = np.median(texlib.nearest(mr, uv0[tri0[face_f]].mean(1)), 0)
for name, ch in charts.items():
    w, h = ch['size']
    x0, y0 = ch['origin']
    mr[int(y0 * sx):int((y0 + h) * sx) + 1, int(x0 * sx):int((x0 + w) * sx) + 1] = \
        np.array([13.0, 242.0, 0.0]) if name == 'mouth' else skin_mr                # the mouth fill is matte
    mm = imgs['region_mask']
    mx = mm.shape[1] / S
    mm[int(y0 * mx):int((y0 + h) * mx) + 1, int(x0 * mx):int((x0 + w) * mx) + 1] = 0     # unmasked in every skin
for k, v in tex.items():
    mode = 'RGBA' if k == 'region_mask' else 'RGB'
    g.set_image(doc['textures'][v]['source'], png(Image.fromarray(np.clip(imgs[k] + 0.5, 0, 255).astype(np.uint8), mode)))


# ---- geometry: LOD0, LOD1 and their shadow copies
def repair(mi):
    pr, att, tri = mesh_data(mi)
    pos = att['POSITION'].astype(np.float64)
    _, weld = np.unique(pos.round(6), axis=0, return_inverse=True)
    weld = weld.ravel()
    wpos = np.zeros((weld.max() + 1, 3))
    wpos[weld] = pos
    spike = find_spike(tri, weld, wpos)
    alive = np.ones(len(tri), bool)
    alive[spike] = False
    cycles, chosen = pick_loops(tri, weld, wpos, alive)
    corners = set(weld[tri[spike]].ravel())
    for cyc in cycles:
        if spike.size and set(cyc) <= corners and len(cyc) <= 6:
            chosen['spike'] = cyc
    new_attr = {k: [v] for k, v in att.items()}
    # the spike's near corners had smooth normals averaged with the spike's long faces (tilted toward the hood): a
    # shading streak on the cheek. Their normals are recomputed from the faces that remain (area-weighted).
    renorm = np.zeros(len(pos), bool)
    if spike.size:
        far = np.bincount(weld[tri[spike]].ravel()).argmax()
        near_w = [w_ for w_ in np.unique(weld[tri[spike]]) if w_ != far]
        fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
        nv_new = new_attr['NORMAL'][0].astype(np.float64).copy()
        for w_ in near_w:
            faces_w = np.nonzero(alive & (weld[tri] == w_).any(1))[0]
            nrm_w = fn[faces_w].sum(0)
            nrm_w /= np.linalg.norm(nrm_w)
            verts_w = np.nonzero(weld == w_)[0]
            nv_new[verts_w] = nrm_w
            renorm[verts_w] = True
        new_attr['NORMAL'][0] = nv_new.astype(att['NORMAL'].dtype)
    new_tri = [tri[alive]]
    nv = len(pos)
    added = 0
    fans = {}
    for name, cyc in chosen.items():
        # a source copy of every loop vertex: one used by an alive neighbouring face
        src_v = []
        for wv in cyc:
            cand = tri[alive][(weld[tri[alive]] == wv)]
            src_v.append(int(cand[0]))
        pts = wpos[cyc]
        c, ax, ay, n = plane(pts)
        p2 = np.stack([(pts - c) @ ax, (pts - c) @ ay], 1)
        tris, rest = ear_clip(p2)
        ring = list(src_v)
        fans[name] = len(rest)
        if rest:
            # a zig-zag the plane cannot ear-clip: the rest is a fan around its centre (a vertex copied from the
            # nearest loop vertex, at the rest's centroid)
            centre = pos[[src_v[i] for i in rest]].mean(0)
            near = src_v[rest[int(np.argmin(np.linalg.norm(pos[[src_v[i] for i in rest]] - centre, axis=1)))]]
            ring.append(near)
            ci = len(cyc)
            tris += [(rest[i], rest[(i + 1) % len(rest)], ci) for i in range(len(rest))]
        for k, v in att.items():
            if k == 'TEXCOORD_0':
                uvv = chart_uv(name, pos[ring])
                if rest:
                    uvv[-1] = chart_uv(name, centre[None])[0]
                new_attr[k].append(uvv.astype(v.dtype))
            elif k == 'POSITION' and rest:
                vals = v[ring].copy()
                vals[-1] = centre
                new_attr[k].append(vals)
            elif k == 'NORMAL' and name == 'mouth':
                # the mouth fill faces the front (the loop's inward lip normals lit it in steps)
                nn_ = n if n[2] > 0 else -n
                new_attr[k].append(np.repeat(nn_[None].astype(v.dtype), len(ring), 0))
            else:
                new_attr[k].append(v[ring])
        # winding: loops_of walks against the faces' direction, so the cycle order is the fill's winding, and every ear
        # keeps the cycle's order
        tt = np.array(tris, np.int64)
        new_tri.append(tt + nv)
        nv += len(ring)
        added += len(tt)
    for k in new_attr:
        g.set_accessor(pr['attributes'][k], np.concatenate(new_attr[k]))
    g.set_accessor(pr['indices'], np.concatenate(new_tri).reshape(-1))
    return {'removed': spike.tolist(), 'loops': {k: len(v) for k, v in chosen.items()}, 'added': added,
            'fans': fans, 'renormalised_vertices': int(renorm.sum()),
            'triangles': f'{len(tri)} -> {len(tri) - len(spike) + added}'}, tri, att, alive, renorm


checks = {}
for mi in (0, shadows[0], lods[0], shadows[1]):
    name = doc['meshes'][mi]['name']
    rep, tri_before, att_before, alive, renorm = repair(mi)
    report[name] = rep
    # check: the kept triangles keep every corner attribute except UVs
    pr = doc['meshes'][mi]['primitives'][0]
    tri_after = g.accessor(pr['indices']).reshape(-1, 3)
    keep = tri_before[alive]
    same = all(np.array_equal(att_before[k][keep], g.accessor(pr['attributes'][k])[tri_after[:len(keep)]])
               for k in att_before if k not in ('TEXCOORD_0', 'NORMAL'))
    ok_n = ~renorm[keep]                       # normals: unchanged except at the spike's three near corners
    same &= np.array_equal(att_before['NORMAL'][keep][ok_n], g.accessor(pr['attributes']['NORMAL'])[tri_after[:len(keep)]][ok_n])
    checks[name] = bool(same)
g.save(dst)

# ---- far LODs: maps again from the repaired LOD0
g = Glb(dst)
doc = g.doc
lod0 = doc['meshes'][0]
for level in (2, 3):
    pr = doc['meshes'][lods[level - 1]]['primitives'][0]
    corners = TT.source_faces(doc, g.bin, pr)
    uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
    m = doc['materials'][pr['material']]
    kinds = TT.material_maps(m)
    size = g.image(doc['textures'][kinds['basecolor']]['source']).size[0]
    maps, coverage = TT.transfer(doc, g.bin, lod0['primitives'][0], pr, corners, uv[corners], size)
    for kind, picture in maps.items():
        g.set_image(doc['textures'][kinds[kind]]['source'], png(picture))
g.save(dst)
report['kept_triangles_unchanged'] = checks
print('FIX_MESH', json.dumps(report))
if not all(checks.values()):
    sys.exit(1)
