#!/usr/bin/env python3
"""Headwear gate (2026-11-02): the added veil and braids against the rest of the body in every clip, at every key and between keys at
30 fps. Parts by connectivity in the runtime GLB's head primitive (rest pose): braids = the two long thin tubes, veil = the sheet hanging
below 1.45 m at the back. Body = every other LOD0 vertex (dress, skirt, head shell, hood, arms). A headwear vertex counts as inside when
the nearest body vertex's normal points away from it (behind the surface) within 3 cm. Reports per clip the deepest point and the frames
with any vertex more than 1 cm inside. Headwear above 1.55 m at rest (the braids' tops inside the hood, the veil's band on it) is left
out. Args: <runtime glb> <out json>"""
import sys, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
M = Model(Glb(sys.argv[1])); doc = M.glb.json
heads = [i for i, p in enumerate(M.primitives) if 'Head' in (doc['materials'][doc['meshes'][doc['nodes'][p['node']]['mesh']]['primitives'][0].get('material', 0)]['name'] if False else '')]
# the head primitive: the one with the braids (the material name ends in Head)
names = []
for node_i in M.order:
    nd = doc['nodes'][node_i]
    if 'mesh' in nd:
        for pr in doc['meshes'][nd['mesh']]['primitives']: names.append(doc['materials'][pr.get('material', 0)]['name'])
hp = next(i for i, p in enumerate(M.primitives) if 'Head' in names[i])
P0 = M.primitives[hp]['positions']; T0 = M.primitives[hp]['triangles']
# parts from work/uv_tex2.npz by rest position (Blender frame of the raw ABC side -> the mirrored, floor-lifted glTF frame)
U = np.load(Path(sys.argv[1]).resolve().parents[1] / 'work' / 'uv_tex2.npz'); un = [str(x) for x in U['names']]
best = None
for sx in (-1, 1):
    Q = np.c_[sx * U['co'][:, 0], U['co'][:, 2], -U['co'][:, 1]]; Q[:, 1] += P0[:, 1].min() - Q[U['mat'] == 1][:, 1].min() if False else 0
    for lift in (0.0, 0.9297, 0.9299):
        d, j = cKDTree(Q + [0, lift, 0]).query(P0)
        if best is None or np.median(d) < best[0]: best = (float(np.median(d)), j, sx, lift)
print('MATCH median mm', round(best[0] * 1000, 3), 'mirror', best[2], 'lift', best[3])
cp = U['comp'][best[1]]
parts = {k: np.where(cp == un.index(k))[0] for k in ('veil', 'braids') if k in un}
hw_all = np.isin(cp, [un.index(k) for k in ('veil', 'braids') if k in un])
# the braids' tops (inside the hood by construction) and the veil's top band (on the hood) are left out: rest height below 1.55 m only
parts = {k: v[P0[v, 1] < 0.62] for k, v in parts.items()}
print('PARTS', {k: len(v) for k, v in parts.items()})
hw = hw_all
def depths(posed):
    bp, bn = [], []
    for i, (pts, tri) in enumerate(posed):
        fn = np.cross(pts[tri[:, 1]] - pts[tri[:, 0]], pts[tri[:, 2]] - pts[tri[:, 0]])
        vn = np.zeros_like(pts)
        for c in range(3): np.add.at(vn, tri[:, c], fn)
        vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
        keep = np.ones(len(pts), bool)
        if i == hp: keep = ~hw
        used = np.zeros(len(pts), bool); used[np.unique(tri)] = True
        bp.append(pts[keep & used]); bn.append(vn[keep & used])
    bp = np.vstack(bp); bn = np.vstack(bn); kd = cKDTree(bp); out = {}
    for k, idx in parts.items():
        q = posed[hp][0][idx]; d, j = kd.query(q); dep = -np.einsum('ij,ij->i', q - bp[j], bn[j]); dep[(d >= 0.03) | (dep < 0)] = 0; out[k] = dep
    return out
# the bind pose's own readings (the test misreads some rest contacts, e.g. normals on thin cloth edges): only penetration beyond them counts
REST = depths(M.skinned_positions(M.world({})))
print('REST max cm', {k: round(float(v.max()) * 100, 2) for k, v in REST.items()})
res = {}
for clip in M.clips:
    times = M.clip_times(clip); ts = np.unique(np.r_[times, np.arange(0, times[-1] + 1e-6, 1 / 30)])
    worst = {k: (0.0, None) for k in parts}; frames = {k: 0 for k in parts}
    for t in ts:
        posed = M.skinned_positions(M.world(M.sample(clip, t)))
        bp, bn = [], []
        for i, (pts, tri) in enumerate(posed):
            fn = np.cross(pts[tri[:, 1]] - pts[tri[:, 0]], pts[tri[:, 2]] - pts[tri[:, 0]])
            vn = np.zeros_like(pts)
            for c in range(3): np.add.at(vn, tri[:, c], fn)
            vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
            keep = np.ones(len(pts), bool)
            if i == hp: keep = ~hw
            used = np.zeros(len(pts), bool); used[np.unique(tri)] = True
            bp.append(pts[keep & used]); bn.append(vn[keep & used])
        bp = np.vstack(bp); bn = np.vstack(bn); kd = cKDTree(bp)
        hpos = posed[hp][0]
        for k, idx in parts.items():
            q = hpos[idx]; d, j = kd.query(q)
            depth = -np.einsum('ij,ij->i', q - bp[j], bn[j]); depth[(d >= 0.03) | (depth < 0)] = 0
            depth = depth - REST[k]
            dmax = float(depth.max())
            if dmax > worst[k][0]: worst[k] = (dmax, round(float(t), 3))
            if dmax > 0.01: frames[k] += 1
    res[clip] = {k: {'max_cm': round(worst[k][0] * 100, 2), 'at_s': worst[k][1], 'frames_over_1cm': frames[k], 'frames': len(ts)} for k in parts}
    print(f'{clip:12s}', '  '.join(f"{k}: {v['max_cm']:4.1f} cm @{v['at_s']} ({v['frames_over_1cm']}/{v['frames']} f > 1 cm)" for k, v in res[clip].items()))
json.dump(res, open(sys.argv[2], 'w'), indent=1)
