#!/usr/bin/env python3
"""What passes through the cloth, per clip at 48 fps, on a runtime GLB (LOD0, first primitives).
 feet/robe: a foot vertex outside the robe's outer wall;  hands/robe: finger or hand vertex behind the robe's outer wall coming from outside (arm gate covers depth; here the count);
 head/collar: head vertices behind the collar's inner face (chin through the collar);  lining/robe: lining vertices outside the robe.
A vertex counts when its nearest robe point lies inside a triangle (not past the hem) and it is on the wrong side by more than 2 mm. Args: <glb> <uv npz> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, uvn, out = sys.argv[1:4]
want = sys.argv[4].split(',') if len(sys.argv) > 4 else None
D = np.load(uvn); co, comp = D['co'], D['comp']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
g_ = np.c_[co[:, 0], co[:, 2], -co[:, 1]]
m = Model(Glb(glb)); doc = m.glb.json
Rs = m.skinned_positions(m.world({}))
offs = np.cumsum([0] + [len(r[0]) for r in Rs])
rest = np.concatenate([r[0] for r in Rs]); T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
di, near = cKDTree(g_).query(rest); part = comp[near]; part[di > 2e-3] = -1
print('matched', float((di < 2e-3).mean()))
fp = part[T[:, 0]]
robe_f = np.where((fp == pid['robe']) & (part[T[:, 1]] == pid['robe']))[0]
col_v = (part == pid['torso']) & (rest[:, 1] > 1.58)
col_f = np.where(col_v[T].all(1))[0]
TESTS = (('hands', part == pid['hands'], robe_f, -1), ('sleeve', part == pid['sleeves'], robe_f, -1), ('lining', part == pid['rlining'], robe_f, 1))
res = {}
for a_ in doc['animations']:
    clip = a_['name']
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; TS = np.arange(0, dur + 1e-6, 1 / 48)
    r_ = {k: [0, 0.0, 0.0] for k, *_ in TESTS}
    for t in TS:
        x = np.concatenate([r[0] for r in m.skinned_positions(m.world(m.sample(clip, float(t))))])
        for nm, vm, ff, sgn in TESTS:
            q = np.where(vm)[0]
            ft = x[T[ff]]
            c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
            _, nr = cKDTree(c_).query(x[q], k=min(10, len(c_)))
            pts = np.repeat(x[q], nr.shape[1], 0)
            qq, bc = closest_on_triangles(pts, ft[nr.ravel(), 0], ft[nr.ravel(), 1], ft[nr.ravel(), 2])
            dd = np.linalg.norm(pts - qq, axis=1).reshape(nr.shape); b = dd.argmin(1); rr = np.arange(len(q))
            fid = nr[rr, b]; cp = qq.reshape(*nr.shape, 3)[rr, b]; v = x[q] - cp
            s_ = np.einsum('ij,ij->i', v, n_[fid]) * sgn; dist = dd[rr, b]
            lim = 0.002 if sgn > 0 else 0.010
            through = (s_ > lim) & (s_ > 0.95 * dist) & (dist < 0.25)
            if through.any():
                r_[nm][0] += 1
                d = float(s_[through].max())
                if d > r_[nm][1]: r_[nm][1] = d; r_[nm][2] = float(t)
    res[clip] = {k: dict(frames=v[0], of=len(TS), max_cm=round(v[1] * 100, 1), at=round(v[2], 2)) for k, v in r_.items()}
    print(f'{clip:15s} ' + ' | '.join(f'{k} {v[0]:3d}/{len(TS)} {v[1] * 100:4.1f} cm' for k, v in r_.items()), flush=True)
json.dump(res, open(out, 'w'), indent=1)
