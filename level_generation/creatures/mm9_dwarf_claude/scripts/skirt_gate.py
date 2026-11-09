#!/usr/bin/env python3
"""Thighs through the tunic skirt, per clip at 48 fps on a runtime or test GLB (LOD0; adapted from mm9_skeletonwarrior_claude/scripts/skirt_gate.py).
A pants vertex counts as through when it lies on the skirt's OUTER side and its nearest skirt point is inside that triangle (perpendicular foot on the cloth, not past
its edge: a leg below the hem is free). Depth = distance outside. Skirt faces: all vertices with Skirt_* weight share > 0 or the skirt band under the belt.
Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); PR = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(PR))])
names = [n.get('name') for n in m.glb.json['nodes']]
jn = [names[j] for j in m.joints]
J, W = np.vstack([p['joints'] for p in PR]), np.vstack([p['weights'] for p in PR])
sk = [i for i, n in enumerate(jn) if n.startswith('Skirt_')]
leg = [i for i, n in enumerate(jn) if 'Thigh' in n]                      # thighs: a calf kicked up behind a lifted skirt is free of it
sw = (np.isin(J, sk) * W).sum(1); lw = (np.isin(J, leg) * W).sum(1)
offs = np.cumsum([0] + [len(p['positions']) for p in PR]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, offs)])
face = np.where((sw[tri] > 0.01).all(1))[0]
legv = np.where((lw > 0.5) & (sw < 0.01))[0]                       # run 2: skirt cloth carried by the thighs (r14) is not a leg
# the Meshy hem is a double wall: only the outer wall counts (rest normal facing away from the body axis)
rest = allpos(m.world({}))
ft = rest[tri[face]]; n0 = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); c0 = ft.mean(1)
rad = c0 * [1, 0, 1]; rad[:, 2] -= 0.0
nn = n0 / np.maximum(np.linalg.norm(n0, axis=1, keepdims=True), 1e-12)
face = face[((nn * rad).sum(1) > 0) & (np.abs(nn[:, 1]) < 0.6)]     # not the rolled hem's underside
print('outer skirt faces', len(face), 'leg verts', len(legv))
res = {}
for clip in [a['name'] for a in m.glb.json['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; T = np.arange(0, dur + 1e-6, 1 / 48)
    frames = 0; deep = []; wf = 0
    for ti, t in enumerate(T):
        x = allpos(m.world(m.sample(clip, float(t))))
        ft = x[tri[face]]
        c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
        q = x[legv]
        _, near = cKDTree(c_).query(q, k=min(24, len(c_)))
        pts = np.repeat(q, near.shape[1], 0)
        qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
        dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
        fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]; v = q - cp
        s_ = np.einsum('ij,ij->i', v, n_[fid]); dist = dd[r, b]
        th = (s_ > 0.002) & (s_ > 0.98 * dist) & (dist < 0.2)
        top = float(s_[th].max()) if th.any() else 0.0
        if th.any(): frames += 1
        if ti == int(__import__('os').environ.get('DBGF', -1)) and clip == __import__('os').environ.get('DBGC', ''):
            print('DBG flagged', th.sum(), 'of', len(q), 'q mean', q[th].mean(0).round(3), 'cp mean', cp[th].mean(0).round(3), 'n', n_[fid[th]].mean(0).round(2), 's', s_[th].round(3)[:8], 'qmin', q[th].min(0).round(3), 'qmax', q[th].max(0).round(3))
        if top > (max(deep) if deep else 0): wf = ti
        deep.append(top)
    res[clip] = dict(frames=frames, of=len(T), max_cm=round(max(deep) * 100, 1), worst_frame=wf)
    print(f"{clip:14s} frames through {frames:3d}/{len(T):3d} max {max(deep) * 100:5.1f} cm  worst frame {wf}", flush=True)
json.dump(res, open(out, 'w'), indent=1)
