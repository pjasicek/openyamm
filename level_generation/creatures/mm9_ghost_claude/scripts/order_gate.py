#!/usr/bin/env python3
"""Blend order gate. The engine writes no depth for blended primitives and draws them back to front by their REST centres, so a limb that swings to the other side of the body stays in its rest layer.
Per clip at 6 fps and 8 camera azimuths (camera far away, level): the 1.5 cm screen cells where an arm (or the head) overlaps the body, and the share where its near surface is in the wrong layer against the body's near wall (more than 1 cm behind it yet drawn over it, or the reverse).
Also the head against the body and arms. Usage: order_gate.py <glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = []
for mesh in doc['meshes']:
    if mesh.get('name') == 'Ghost':
        names = [doc['materials'][p['material']]['name'].rsplit('_', 1)[0] for p in mesh['primitives']]
print(names)
centres = [0.5 * (p['positions'].min(0) + p['positions'].max(0)) for p in m.primitives]
A = np.radians(np.arange(0, 360, 45))
rep = {}
for a in doc['animations']:
    c = a['name']
    if c == 'Dead':
        continue
    tot = {n: np.zeros(8) for n in names}; bad = {n: np.zeros(8) for n in names}
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 6):
        P = [q[0] for q in m.skinned_positions(m.world(m.sample(c, float(t))))]
        for i, az in enumerate(A):
            v = np.array([np.sin(az), 0, np.cos(az)]); r = np.array([np.cos(az), 0, -np.sin(az)]); u = np.array([0, 1, 0.0])
            depth = [p @ v for p in P]
            xy = [np.c_[p @ r, p @ u] for p in P]
            for b, nb in enumerate(names):
                if nb == 'Ghost':
                    continue
                other = names.index('Ghost')
                # the body's near wall per 1.5 cm cell on screen
                cell = np.floor(xy[other] / 0.015).astype(np.int64)
                key = cell[:, 0] * 100000 + cell[:, 1]
                order = np.argsort(key); uk, first = np.unique(key[order], return_index=True)
                near = np.maximum.reduceat(depth[other][order], first)
                ka = np.floor(xy[b] / 0.015).astype(np.int64); ka = ka[:, 0] * 100000 + ka[:, 1]
                oa = np.argsort(ka); ua, fa = np.unique(ka[oa], return_index=True)
                nearA = np.maximum.reduceat(depth[b][oa], fa)
                pos = np.minimum(np.searchsorted(uk, ua), len(uk) - 1)
                ok = uk[pos] == ua
                if not ok.any():
                    continue
                da = nearA[ok]; dn = near[pos[ok]]
                drawn_after = centres[b] @ v > centres[other] @ v
                wrong = (da < dn - 0.01) if drawn_after else (da > dn + 0.01)
                tot[nb][i] += ok.sum(); bad[nb][i] += wrong.sum()
    rep[c] = {n: {'overlap_verts': int(tot[n].sum()), 'wrong_pct': round(float(100 * bad[n].sum() / max(tot[n].sum(), 1)), 1), 'worst_az_deg': int(np.degrees(A[int(np.argmax(bad[n] / np.maximum(tot[n], 1)))])),
                  'worst_az_pct': round(float((100 * bad[n] / np.maximum(tot[n], 1)).max()), 1)} for n in names if n != 'Ghost'}
    print(f'{c:13s}', ' '.join(f"{n[5:]}: {rep[c][n]['wrong_pct']}% (az {rep[c][n]['worst_az_deg']} {rep[c][n]['worst_az_pct']}%)" for n in names if n != 'Ghost'))
if len(sys.argv) > 2:
    json.dump(rep, open(sys.argv[2], 'w'), indent=1)
