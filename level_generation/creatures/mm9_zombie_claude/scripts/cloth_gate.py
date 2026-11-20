#!/usr/bin/env python3
"""Thighs through the cloth, per clip at 48 fps, on a clip GLB (LOD0). The only loose cloth over the legs is the waist tatter (part 2). A trouser vertex of the thigh counts as through when it lies on
the OUTER side of the tatter and its nearest tatter point is inside a triangle (foot on the cloth, not past its hem). Depth = distance outside. Linings (zero UV area) are skipped by part match.
Args: <glb> <faces npz> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, faces, out = sys.argv[1:4]
want = sys.argv[4].split(',') if len(sys.argv) > 4 else None
D = np.load(faces); LIFT = 0.7566
tc = D['co'][D['part'] == 2].reshape(-1, 3); leg = D['co'][D['part'] == 1].reshape(-1, 3)
conv = lambda q: np.c_[q[:, 0], q[:, 2] + LIFT, -q[:, 1]]
m = Model(Glb(glb)); doc = m.glb.json
Rs = m.skinned_positions(m.world({}))
offs = np.cumsum([0] + [len(r[0]) for r in Rs])
rest = np.concatenate([r[0] for r in Rs]); T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
dt, _ = cKDTree(conv(tc)).query(rest); dl, _ = cKDTree(conv(leg)).query(rest)
isc = dt < 1e-3; isl = (dl < 1e-3) & (rest[:, 1] > LIFT - 0.55) & (rest[:, 1] < LIFT + 0.40) & ~isc
cf = np.where(isc[T].all(1))[0]
print('cloth faces', len(cf), 'thigh verts', int(isl.sum()), 'match p99', np.percentile(dt[isc], 99) if isc.any() else None)
q = np.where(isl)[0]
res = {}
for a_ in doc['animations']:
    clip = a_['name']
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; TS = np.arange(0, dur + 1e-6, 1 / 48)
    frames = 0; top = 0.0; tt = 0
    for t in TS:
        x = np.concatenate([r[0] for r in m.skinned_positions(m.world(m.sample(clip, float(t))))])
        ft = x[T[cf]]
        c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
        _, near = cKDTree(c_).query(x[q], k=min(16, len(c_)))
        pts = np.repeat(x[q], near.shape[1], 0)
        qq, bc = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
        dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
        fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]; v = x[q] - cp
        s_ = np.einsum('ij,ij->i', v, n_[fid]); dist = dd[r, b]
        through = (s_ > 0.002) & (s_ > 0.98 * dist) & (dist < 0.2)
        if through.any():
            frames += 1
            d = float(s_[through].max())
            if d > top: top = d; tt = float(t)
    res[clip] = dict(frames=frames, of=len(TS), max_cm=round(top * 100, 1), at=tt)
    print(f'{clip:15s} frames through {frames:3d}/{len(TS):3d} max {top * 100:5.1f} cm at {tt:.2f}', flush=True)
json.dump(res, open(out, 'w'), indent=1)
