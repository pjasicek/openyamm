#!/usr/bin/env python3
"""Cheek stretch per clip: the edges of the outer head shell that span the jaw's blend (their ends differ in jaw weight), or for MM9 the mesh edges joining the jaw bones to the head: posed length over rest length, and the net jaw opening.
Usage: cheek_gate.py ours <glb> [json] | cheek_gate.py mm9 <glb>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
mode, path = sys.argv[1:3]
m = Model(Glb(path)); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
JAW = np.array([n in ('Xjaw', 'Xchin', 'Xjawpiv') for n in names])
if mode == 'ours':
    mesh = next(x for x in doc['meshes'] if x['name'] == 'Banshee')
    pn = [doc['materials'][p['material']]['name'] for p in mesh['primitives']]
    k = next(i for i, n in enumerate(pn) if n.startswith('BansheeHead'))
    prims = [k]
else:
    prims = [i for i, n in enumerate(mesh['name'] for mesh in doc['meshes']) if n == 'model']
    prims = [i for i, pr in enumerate(m.primitives) if len(pr['positions']) > 1000][:1]
edges = {}
for k in prims:
    pr = m.primitives[k]
    P0, T = m.skinned_positions(m.world({}))[k]
    T = np.asarray(T).reshape(-1, 3)
    key = np.round(P0 / 1e-4).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1)
    jw = (pr['weights'] * JAW[pr['joints']]).sum(1)
    Tw = inv[T]
    fn = np.cross(P0[T[:, 1]] - P0[T[:, 0]], P0[T[:, 2]] - P0[T[:, 0]])
    E = set()
    for t, f in zip(Tw, T):
        for a, b, fa, fb in ((t[0], t[1], f[0], f[1]), (t[1], t[2], f[1], f[2]), (t[2], t[0], f[2], f[0])):
            if a != b and abs(jw[fa] - jw[fb]) > 0.08:
                E.add((min(fa, fb), max(fa, fb)))
    E = np.array(sorted(E))
    if mode == 'ours' and '--all' not in sys.argv:
        sys.path.insert(0, str(Path(__file__).parent))
        import interior
        Tf = T
        inn = interior.interior_faces(P0[Tf])
        outv = np.zeros(len(P0), bool); outv[Tf[~inn].ravel()] = True
        inv_ = np.zeros(len(P0), bool); inv_[Tf[inn].ravel()] = True
        E = E[outv[E].all(1) & ~inv_[E].any(1)]
    L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
    E = E[L0 > 1e-3]; L0 = L0[L0 > 1e-3]
    rep = {}
    for a in doc['animations']:
        c = a['name']
        if c in ('bansetup',):
            continue
        Te = m.clip_times(c)[-1]
        rows = []
        for t in np.arange(0, Te + 1e-6, 1 / 24):
            P = m.skinned_positions(m.world(m.sample(c, float(t))))[k][0]
            rows.append(np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / L0)
        R = np.array(rows)
        i = np.unravel_index(R.argmax(), R.shape)
        rep[c] = {'p50': round(float(np.percentile(R, 50)), 2), 'p95': round(float(np.percentile(R, 95)), 2), 'p99_worst_frame': round(float(np.percentile(R, 99, axis=1).max()), 2), 'max': round(float(R.max()), 2)}
        wi = np.argsort(R[i[0]])[-3:]
        print(f'{c:14s}', rep[c], 'edges', len(E), 'worst at', (P0[E[i[1]]].mean(0).round(3).tolist(), round(float(L0[i[1]]), 4), round(float(jw[E[i[1], 0]]), 2), round(float(jw[E[i[1], 1]]), 2)) if '--where' in sys.argv else '')
if len(sys.argv) > 3:
    json.dump(rep, open(sys.argv[3], 'w'), indent=1)
