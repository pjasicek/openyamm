#!/usr/bin/env python3
"""Mouth: edge stretch on the face and mouth (head faces forward of the ears, above the neck band), every clip at 30 fps. MM9 has no jaw bone, so our face is rigid on Bip01 Head and the figure must be 1.00. Args: <glb> <uv npz>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); D = np.load(sys.argv[2]); co, comp = D['co'], D['comp']; names = [str(x) for x in D['names']]
Rs = m.skinned_positions(m.world({})); rest = np.concatenate([r[0] for r in Rs]); off = np.cumsum([0] + [len(r[0]) for r in Rs])
T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, off)])
g_ = np.c_[co[:, 0], co[:, 2], -co[:, 1]]; _, nr = cKDTree(g_).query(rest); part = comp[nr]
face = (part == names.index('head')) & (rest[:, 2] > 0.06) & (np.abs(rest[:, 0]) < 0.09) & (rest[:, 1] > 1.60)
e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1); e = np.unique(e, axis=0); e = e[face[e].all(1)]
l0 = np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1); ok = l0 > 1e-4; e = e[ok]; l0 = l0[ok]
top = 0
for a in m.glb.json['animations']:
    c = a['name']
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 30):
        P = np.concatenate([r[0] for r in m.skinned_positions(m.world(m.sample(c, float(t))))])
        r = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1) / l0; top = max(top, abs(r - 1).max())
print('face edges', len(e), 'max change', round(float(top) * 100, 2), '%')
