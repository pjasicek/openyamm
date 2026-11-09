#!/usr/bin/env python3
"""Rest-pose geometry error of a decimated npz against work/mesh_in.npz (no weights involved): source vertex ->
densely sampled candidate surface, per region label (work/groups_<set>.npy majority, 99 = kept).
Usage: rest_error.py <npz> <set>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
s = np.load('work/mesh_in.npz'); c = np.load(sys.argv[1]); g = np.load(f'work/groups_{sys.argv[2]}.npy'); k = np.load(f'work/keep_{sys.argv[2]}.npy')
cv, cf = c['verts'], c['faces']; tri = cv[cf]
area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
n = (area / 2e-6).astype(int) + 3; rng = np.random.default_rng(0)
idx = np.repeat(np.arange(len(cf)), n); a, b = rng.random((2, len(idx)))
fl = a + b > 1; a[fl], b[fl] = 1 - a[fl], 1 - b[fl]
pts = tri[idx, 0] + a[:, None] * (tri[idx, 1] - tri[idx, 0]) + b[:, None] * (tri[idx, 2] - tri[idx, 0])
dist = cKDTree(pts).query(s['verts'])[0] * 1000
lab = np.full(len(s['verts']), -1)
for gi in np.unique(g):
    lab[np.unique(s['faces'][g == gi])] = gi
lab[np.unique(s['faces'][k])] = 99
print('REST all p99', round(float(np.percentile(dist, 99)), 2), 'max', round(float(dist.max()), 2))
for gi in np.unique(lab):
    x = dist[lab == gi]; j = np.flatnonzero(lab == gi)[np.argmax(x)]
    print(f'  region {gi:3d} verts {len(x):5d} p95 {np.percentile(x, 95):6.2f} p99 {np.percentile(x, 99):6.2f} max {x.max():6.2f} at', np.round(s['verts'][j], 3))
