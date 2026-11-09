#!/usr/bin/env python3
"""Mouth bag inside the head, every clip at 12 fps: rays from each bag vertex behind the lips, away from the bag's centre, must hit the shell (all LOD0 head faces that are not bag, teeth, tongue or eyes). Prints the worst count per clip. Usage: bag_gate.py <glb>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g); doc = g.json
mesh = next(x for x in doc['meshes'] if x['name'] == 'Banshee')
nm = [doc['materials'][p['material']]['name'].rsplit('_', 1)[0] for p in mesh['primitives']]
k = nm.index('BansheeHead')
UV = g.accessor(mesh['primitives'][k]['attributes']['TEXCOORD_0'])
rx, ry, rs = json.load(open(Path(__file__).parent / 'bag_rect.json'))
bag = (np.abs(UV[:, 0] - (rx + rs / 2) / 1024) < rs / 2048 + 0.002) & (np.abs(UV[:, 1] - (ry + rs / 2) / 1024) < rs / 2048 + 0.002)
P0, T = m.skinned_positions(m.world({}))[k]; T = np.asarray(T).reshape(-1, 3)
isb = bag[T].all(1)
key = np.round(P0 / 1e-5).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.reshape(-1)
par = np.arange(inv.max() + 1)
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for t in inv[T]:
    a, b, c = find(t[0]), find(t[1]), find(t[2]); par[b] = a; par[find(c)] = a
lab = np.array([find(i) for i in range(len(par))])
comp = lab[inv[T[:, 0]]]; shell = np.bincount(comp).argmax()
ST = T[comp == shell]
idx = np.unique(T[isb])
keep = idx                                                     # every bag vertex, shot toward the throat (not outward): an open mouth faces forward, so only the jaw floor or the neck can stop these rays
up = int(ST.ravel()[np.argmax(P0[ST.ravel(), 1])])                          # crown
low = np.where(np.abs(P0[:, 0]) < 0.02)[0]; low = low[np.isin(low, ST)]
low = int(low[np.argmin(P0[low, 1] + 0.5 * np.abs(P0[low, 2] - P0[idx, 2].mean()))])    # throat
print('bag verts', len(idx), 'tested', len(keep), 'shell tris', len(ST))
worst = 0
for a in doc['animations']:
    c = a['name']; wc = 0; wt = 0
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 8):
        P = m.skinned_positions(m.world(m.sample(c, float(t))))[k][0]
        A = P[ST[:, 0]]; E1 = P[ST[:, 1]] - A; E2 = P[ST[:, 2]] - A
        cen = P[idx].mean(0); out = 0
        for v in keep:
            d = P[low] - P[up]; d = d / np.linalg.norm(d); o = P[v]
            h = np.cross(d, E2); det = (E1 * h).sum(1)
            with np.errstate(divide='ignore', invalid='ignore'):
                f = 1 / det; s = o - A; u = f * (s * h).sum(1); q = np.cross(s, E1); w = f * (q @ d); tt = f * (E2 * q).sum(1)
            if not (((u >= 0) & (w >= 0) & (u + w <= 1) & (tt > 0)).any()):
                out += 1
        if out > wc:
            wc, wt = out, round(float(t), 2)
    print(f'{c}:{wc}@{wt}', end=' ')
    worst = max(worst, wc)
print('\nBAG outside, worst', worst)
