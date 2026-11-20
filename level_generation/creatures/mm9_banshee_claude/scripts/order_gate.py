#!/usr/bin/env python3
"""Blend order gate. The engine writes no depth for blended primitives and draws them back to front by their REST centres, so a limb that swings to the other side of a drape stays in its rest layer.
Per clip at 6 fps and 8 camera azimuths (camera far away, level), for each pair of primitives: the 1.5 cm screen cells where both have surface, and the share where they are in the wrong layer (more than 1.5 cm apart in depth and drawn in the wrong order).
Report per clip the worst pairs. Usage: order_gate.py <glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = []
for mesh in doc['meshes']:
    if mesh.get('name') == 'Banshee':
        names = [doc['materials'][p['material']]['name'].rsplit('_', 1)[0].replace('Banshee', '') or 'Torso' for p in mesh['primitives']]
print(names)
n = len(names)
centres = [0.5 * (p['positions'].min(0) + p['positions'].max(0)) for p in m.primitives[:n]]
print({k: np.round(c, 2).tolist() for k, c in zip(names, centres)})
A = np.radians(np.arange(0, 360, 45))
PAIRS = [('Torso', 'ArmL'), ('Torso', 'ArmR'), ('Skirt', 'ArmL'), ('Skirt', 'ArmR'), ('Cape', 'ArmL'), ('Cape', 'ArmR'), ('WingL', 'ArmL'), ('WingR', 'ArmR'), ('WingL', 'Torso'), ('WingR', 'Torso'), ('Cape', 'Torso'), ('Cape', 'Skirt'), ('WingL', 'Skirt'), ('WingR', 'Skirt'),
         ('Head', 'Torso'), ('Head', 'ArmL'), ('Head', 'ArmR'), ('HairL', 'Head'), ('HairR', 'Head'), ('HairL', 'ArmL'), ('HairR', 'ArmR'), ('Neck', 'Torso')]
rep = {}
tot_all = {p: 0 for p in PAIRS}; bad_all = {p: 0 for p in PAIRS}
for a in doc['animations']:
    c = a['name']
    if c == 'Dead':
        continue
    tot = {p: 0 for p in PAIRS}; bad = {p: 0 for p in PAIRS}
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 6):
        P = [q[0] for q in m.skinned_positions(m.world(m.sample(c, float(t))))][:n]
        for i, az in enumerate(A):
            v = np.array([np.sin(az), 0, np.cos(az)]); r = np.array([np.cos(az), 0, -np.sin(az)]); u = np.array([0, 1, 0.0])
            depth = {}
            for k, nm in enumerate(names):
                key = np.floor(np.c_[P[k] @ r, P[k] @ u] / 0.015).astype(np.int64)
                key = key[:, 0] * 100000 + key[:, 1]
                d = P[k] @ v
                o = np.argsort(key); uk, first = np.unique(key[o], return_index=True)
                depth[nm] = (uk, np.maximum.reduceat(d[o], first))
            for p in PAIRS:
                x, y = p
                ux, dx = depth[x]; uy, dy = depth[y]
                com, ia, ib = np.intersect1d(ux, uy, return_indices=True)
                if not len(com):
                    continue
                cx = centres[names.index(x)] @ v; cy = centres[names.index(y)] @ v
                if x == 'Head' or y == 'Head':
                    other_near = (dy[ib] if x == 'Head' else dx[ia])
                    tot[p] += len(com)
                    continue                          # the head is opaque and writes depth: against it nothing is in the wrong layer
                # drawn later = nearer rest centre
                wrong = (dx[ia] < dy[ib] - 0.015) if cx > cy else (dy[ib] < dx[ia] - 0.015)
                tot[p] += len(com); bad[p] += int(wrong.sum())
    rep[c] = {f'{x}/{y}': [tot[(x, y)], round(100 * bad[(x, y)] / max(tot[(x, y)], 1), 1)] for x, y in PAIRS}
    for p in PAIRS:
        tot_all[p] += tot[p]; bad_all[p] += bad[p]
    w = sorted(rep[c].items(), key=lambda t: -t[1][1])[:4]
    print(f'{c:13s}', ' '.join(f'{k}:{v[1]}%' for k, v in w))
print('ALL', ' '.join(f'{x}/{y}:{100 * bad_all[(x, y)] / max(tot_all[(x, y)], 1):.1f}%' for x, y in PAIRS))
if len(sys.argv) > 2:
    json.dump(rep, open(sys.argv[2], 'w'), indent=1)
