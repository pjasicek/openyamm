#!/usr/bin/env python3
"""True creases of the cloak and dress, per clip at 15 fps: pairs of adjacent LOD0 faces (welded by position) whose normals turn more than 110 degrees against each other in the pose, minus pairs already so at rest, outer faces only (no lining). The collapse gate's flip test compares a face with a blend of two chains' rotations and calls a sheet that turned over a flip; this measures whether the sheet actually folds on itself.
Usage: fold_gate.py <glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
mesh = next(x for x in doc['meshes'] if x['name'] == 'Banshee')
names = [doc['materials'][p['material']]['name'].rsplit('_', 1)[0] for p in mesh['primitives']]
want = [i for i, n in enumerate(names) if n in ('BansheeCape', 'BansheeWingL', 'BansheeWingR', 'BansheeSkirt')]
pairs = {}
rest = m.skinned_positions(m.world({}))
for k in want:
    P, T = rest[k]
    T = np.asarray(T).reshape(-1, 3)
    n = len(T) // 2              # lining first, outer after: the outer half
    T = T[n:]
    key = np.round(P / 1e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
    Tw = inv[T]
    edges = {}
    for f, t in enumerate(Tw):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = (min(t[a], t[b]), max(t[a], t[b]))
            edges.setdefault(e, []).append(f)
    adj = np.array([v[:2] for v in edges.values() if len(v) >= 2])
    pairs[k] = (T, adj)


def normals(P, T):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


C = np.cos(np.radians(110))
rep = {}
for a in doc['animations']:
    c = a['name']
    worst = {}; tot = 0; wt = {}
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 15):
        sk = m.skinned_positions(m.world(m.sample(c, float(t))))
        for k in want:
            T, adj = pairs[k]
            N = normals(sk[k][0], T)
            d = (N[adj[:, 0]] * N[adj[:, 1]]).sum(1)
            cnt = int((d < C).sum())
            tot += cnt
            if cnt > worst.get(names[k], -1):
                worst[names[k]] = cnt; wt[names[k]] = round(float(t), 2)
    rep[c] = {'worst': worst, 'time': wt, 'pair_frames': tot}
    print(f'{c:13s}', 'crease pairs:', ' '.join(f"{k[7:]}={v}@{wt[k]}" for k, v in worst.items()))
print('EDGES', {names[k]: len(pairs[k][1]) for k in want})
if len(sys.argv) > 2:
    json.dump(rep, open(sys.argv[2], 'w'), indent=1)
