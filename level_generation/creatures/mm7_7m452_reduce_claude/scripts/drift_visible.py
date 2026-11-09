#!/usr/bin/env python3
"""texture_drift.py results restricted to visible surface: a candidate face counts only when the source face nearest to
its centre is seen in some view (work/visible_all.npy > 0; hidden scalp/neck under helmet and coif drift harmlessly).
Writes work/drift_<tag>_vis.npy (hidden faces zeroed) for drift_lock.py. Usage: drift_visible.py <tag>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
tag = sys.argv[1]
s = np.load('work/mesh_in.npz'); seen = np.load('work/visible_all.npy') > 0
c = np.load(f'work/mesh_{tag}.npz'); drift = np.load(f'work/drift_{tag}.npy')
tri = c['verts'][c['faces']]; cen = tri.mean(1)
_, i = cKDTree(s['verts'][s['faces']].mean(1)).query(cen)
vis = seen[i]; dv = np.where(vis, drift, 0)
area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
bad = dv > 40
print(tag, 'visible faces', int(vis.sum()), 'drift>40:', int(bad.sum()), 'area cm2', round(float(area[bad].sum() * 1e4), 1),
      'over 3 cm2:', int((bad & (area > 3e-4)).sum()))
for k in np.argsort(-dv * area)[:10]:
    if dv[k] > 25:
        print(f'  face {k} drift {dv[k]:.0f} area {area[k]*1e4:.2f}cm2 at {np.round(cen[k], 3)} group {c["group"][k]}')
np.save(f'work/drift_{tag}_vis.npy', dv)
