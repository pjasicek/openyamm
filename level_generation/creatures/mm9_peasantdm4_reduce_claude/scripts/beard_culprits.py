#!/usr/bin/env python3
"""Beard edges of a candidate that stretch more than the installed beard's per-clip maximum (beard_gate_dm4.py definition), with
their rest positions: the spots to keep exact. Usage: beard_culprits.py <candidate glb> <installed beard.json> <out npy (rest
positions of the culprit edges' vertices, glTF)>"""
import json
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
g = Glb(Path(sys.argv[1])); m = Model(g); ref = json.load(open(sys.argv[2]))['clips']
prim = g.json['meshes'][next(n['mesh'] for n in g.json['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)]['primitives']
kh = [g.json['materials'][p['material']]['name'] for p in prim].index('PeasantDM4Head')
rh = m.skinned_positions(m.world({}))[kh][0]; T = np.asarray(m.primitives[kh]['triangles']).reshape(-1, 3); c = rh[T].mean(1)
bf = (np.abs(c[:, 0]) <= 0.3) & (c[:, 1] < 0.975) & (c[:, 1] > 0.80)
E_ = np.vstack([T[bf][:, [0, 1]], T[bf][:, [1, 2]], T[bf][:, [2, 0]]]); L0 = np.linalg.norm(rh[E_[:, 0]] - rh[E_[:, 1]], axis=1)
E_ = E_[L0 > 1e-4]; L0 = L0[L0 > 1e-4]
pts = []
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; lim = ref[clip]['stretch']
    for t in np.append(np.arange(0, t1, 1 / 48), t1):
        ph = m.skinned_positions(m.world(m.sample(clip, t)))[kh][0]
        r = np.linalg.norm(ph[E_[:, 0]] - ph[E_[:, 1]], axis=1) / L0
        bad = r > lim + 1e-3
        if bad.any():
            pts.append(rh[E_[bad].ravel()])
            print(clip, round(t, 3), 'edges over', int(bad.sum()), 'max', round(float(r.max()), 3), 'at', rh[E_[bad][0]].mean(0).round(3))
P = np.unique(np.vstack(pts).round(6), axis=0) if pts else np.zeros((0, 3))
np.save(sys.argv[3], P); print('CULPRIT points', len(P))
