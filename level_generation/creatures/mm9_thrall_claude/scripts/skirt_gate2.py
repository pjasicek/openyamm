#!/usr/bin/env python3
"""Legs through the skirt, per clip at 48 fps. In the Spine frame a ray runs from the body axis out to each leg vertex; the vertex is through when the cloth lies on that ray before it
(depth = how far past the cloth). The cloth is rasterised to a (azimuth, height) -> outermost radius map from its triangles, so jagged gaps in the hem count as open, not as cloth, and the double
wall does not matter. Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); prims = m.primitives
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
J = np.vstack([p['joints'] for p in prims]); W = np.vstack([p['weights'] for p in prims])
sk = [i for i, n in enumerate(jn) if n.startswith('Skirt_')]; leg = [i for i, n in enumerate(jn) if 'Thigh' in n or 'Calf' in n or 'Foot' in n]
sw = (np.isin(J, sk) * W).sum(1); lw = (np.isin(J, leg) * W).sum(1)
offs = np.cumsum([0] + [len(p['positions']) for p in prims])
tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(prims, offs)])
def allpos(w): return np.concatenate([r[0] for r in m.skinned_positions(w)])
partf = np.where((sw[tri] > 0.0).any(1))[0]
legv = np.where(lw > 0.5)[0]
SP = names.index('Bip01 Spine')
print('skirt faces', len(partf), 'leg verts', len(legv))
w0 = m.world({})
Si0 = np.linalg.inv(w0[SP])
up = Si0[:3, :3] @ np.array([0, 1.0, 0]); up /= np.linalg.norm(up)
a1 = np.cross(up, [0.3, 0.5, 0.8]); a1 /= np.linalg.norm(a1); a2 = np.cross(up, a1)
Rest = allpos(w0); rS = (Si0 @ np.c_[Rest, np.ones(len(Rest))].T).T[:, :3]
ax0 = rS[np.where(sw > 0.0)[0]].mean(0)          # axis through the skirt's centre, parallel to up
ax0 = ax0 - up * (ax0 @ up)
B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [.5, 0, .5], [0, .5, .5], [.34, .33, .33], [.67, .17, .16], [.17, .67, .16], [.16, .17, .67]])
NA, NH, H0, H1 = 180, 90, -0.75, 0.15
res = {}
for clip in [a['name'] for a in m.glb.json['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; T = np.arange(0, dur + 1e-6, 1 / 48)
    frames = 0; deep = []; wf = 0; where = None
    for ti, t in enumerate(T):
        w = m.world(m.sample(clip, float(t))); x = allpos(w)
        Si = np.linalg.inv(w[SP]); y = (Si @ np.c_[x, np.ones(len(x))].T).T[:, :3]
        def polar(q):
            q = q - ax0; h = q @ up; u, v = q @ a1, q @ a2
            return np.arctan2(v, u), np.hypot(u, v), h
        tp = y[tri[partf]]                       # n, 3, 3
        pts = np.einsum('ij,njk->nik', B, tp).reshape(-1, 3)
        a, r, h = polar(pts)
        ia = ((a + np.pi) / (2 * np.pi) * NA).astype(int) % NA; ih = ((h - H0) / (H1 - H0) * NH).astype(int)
        ok = (ih >= 0) & (ih < NH)
        M = np.zeros((NA, NH))
        np.maximum.at(M, (ia[ok], ih[ok]), r[ok])
        a, r, h = polar(y[legv])
        ia = ((a + np.pi) / (2 * np.pi) * NA).astype(int) % NA; ih = ((h - H0) / (H1 - H0) * NH).astype(int)
        ok = (ih >= 0) & (ih < NH)
        d = np.zeros(len(legv)); d[ok] = np.where(M[ia[ok], ih[ok]] > 0, r[ok] - M[ia[ok], ih[ok]], 0)
        topv = float(d.max())
        if topv > 0.002: frames += 1
        if topv > (max(deep) if deep else 0): wf = ti; where = (x[legv][d.argmax()]).round(3).tolist()
        deep.append(max(topv, 0))
    res[clip] = dict(frames=frames, of=len(T), max_cm=round(max(deep) * 100, 1), worst_frame=wf, where=where)
    print(f"{clip:14s} through {frames:3d}/{len(T):3d} max {max(deep) * 100:5.1f} cm  worst frame {wf} at {where}", flush=True)
json.dump(res, open(out, 'w'), indent=1)
