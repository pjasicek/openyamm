#!/usr/bin/env python3
"""Armour plates against the legs, per clip at 48 fps on the LOD0: points of the hip plates and the front flap (vertices and face centres) that lie inside a leg: behind the nearest leg face within a 45 deg cone, up to 7 cm. Reports per clip and plate group the frames and the worst depth. The inverse of skirt_gate.py: a plate through a thigh is what the eye sees. Args: <glb> <out txt> [clips]"""
import sys, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, out = sys.argv[1:3]; want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); PR = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(PR))])
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
J, W = np.vstack([p['joints'] for p in PR]), np.vstack([p['weights'] for p in PR])
offs = np.cumsum([0] + [len(p['positions']) for p in PR]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, offs)])
restp = np.vstack([p['positions'] for p in PR]); SH = np.load('work/shell_pos.npy'); sw = cKDTree(SH).query(restp)[0] < 1e-4
legb = [i for i, n in enumerate(jn) if ('Thigh' in n or 'Calf' in n)]; lw = (np.isin(J, legb) * W).sum(1)
legs = {s: np.where(((lw > .4) & (restp[:, 0] * sg > -.02)))[0] for s, sg in (('L', 1), ('R', -1))}
legf = np.where((lw[tri] > .4).all(1) & ~sw[tri].any(1))[0]
pl = np.where(sw)[0]; lab = np.array(['flap' if abs(c[0]) < .07 and c[2] > .03 else 'inner' if abs(c[0]) < .15 else 'tasset' for c in restp[pl]])
res = []
for clip in [a['name'] for a in m.glb.json['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; T = np.arange(0, dur + 1e-6, 1 / 48); st = {k: [0, 0.] for k in ('flap', 'inner', 'tasset')}
    for t in T:
        x = allpos(m.world(m.sample(clip, float(t)))); ft = x[tri[legf]]; c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
        q = x[pl]; _, near = cKDTree(c_).query(q, k=16); pts = np.repeat(q, near.shape[1], 0)
        qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
        dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q)); fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]; v = q - cp
        s_ = -np.einsum('ij,ij->i', v, n_[fid]); dist = dd[r, b]; ins = (s_ > .003) & (s_ > .7 * dist) & (dist < .07)
        for k in st:
            kk = ins & (lab == k)
            if kk.any(): st[k][0] += 1; st[k][1] = max(st[k][1], float(s_[kk].max()))
    line = f"{clip:13s} of {len(T):3d} " + ' '.join(f"{k} {v[0]:3d}f {v[1] * 100:4.1f} cm" for k, v in st.items()); res.append(line); print(line, flush=True)
open(out, 'w').write('\n'.join(res) + '\n')
