#!/usr/bin/env python3
"""Beard edge stretch per clip: longest edge ratio against rest over the head-set faces below the nose, 48 fps sample of 24 fps. Args: <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g); P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
mats = [g.json['materials'][pr['material']]['name'] for pr in g.json['meshes'][0]['primitives'][:len(P)]]
k = next(i for i, n in enumerate(mats) if n.startswith('DwarfHead'))
T = np.asarray(P[k]['triangles']).reshape(-1, 3); r = m.skinned_positions(m.world({}))[k][0]
low = r[:, 1] < r[:, 1].min() + 0.2
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
neck = np.isin(P[k]['joints'], [jn.index('Bip01 Neck')]) * P[k]['weights']; low &= neck.sum(1) < 0.05            # the collar tube under the helmet is not beard
E_ = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); E_ = E_[low[E_].all(1)]; L0 = np.linalg.norm(r[E_[:, 0]] - r[E_[:, 1]], axis=1); E_ = E_[L0 > 1e-4]; L0 = L0[L0 > 1e-4]
out = []
for c in m.clips:
    d = max(m.clip_times(c)); w = 0
    for t in np.arange(0, d + 1e-6, 1 / 24):
        x = m.skinned_positions(m.world(m.sample(c, float(t))))[k][0]; w = max(w, float((np.linalg.norm(x[E_[:, 0]] - x[E_[:, 1]], axis=1) / L0).max()))
    out.append(f'{c} {w:.2f}')
print('BEARD', ' '.join(out))
