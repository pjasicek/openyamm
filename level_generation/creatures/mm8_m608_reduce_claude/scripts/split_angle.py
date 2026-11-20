#!/usr/bin/env python3
"""Fit the smoothing angle behind a mesh's hard edges: per welded edge, dihedral angle and whether the two faces'
corner normals at the edge differ. Usage: split_angle.py <glb> <mesh index>"""
import sys, collections, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes
d, b = read_glb(Path(sys.argv[1])); mi = int(sys.argv[2])
def val(i):
    a = d['accessors'][i]
    return np.frombuffer(accessor_bytes(d, b, i), dtype={5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]).reshape(a['count'], -1)
p = d['meshes'][mi]['primitives'][0]; P = val(p['attributes']['POSITION']); N = val(p['attributes']['NORMAL']); I = val(p['indices']).reshape(-1, 3)
_, w = np.unique(np.round(P, 5), axis=0, return_inverse=True); w = w.ravel()
f = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); f /= np.linalg.norm(f, axis=1)[:, None] + 1e-12
edges = collections.defaultdict(list)
for fi, t in enumerate(I):
    for k in range(3):
        a, c = t[k], t[(k + 1) % 3]
        edges[tuple(sorted((w[a], w[c])))].append((fi, {w[a]: a, w[c]: c}))
rows = []
for e, fs in edges.items():
    if len(fs) != 2:
        continue
    (f1, m1), (f2, m2) = fs
    ang = np.degrees(np.arccos(np.clip(f[f1] @ f[f2], -1, 1)))
    split = any(N[m1[v]] @ N[m2[v]] < 0.999 for v in e)
    rows.append((ang, split))
rows = np.array(rows)
for t in (10, 15, 20, 25, 30, 35, 40, 45, 50, 60):
    pred = rows[:, 0] > t; acc = (pred == rows[:, 1].astype(bool)).mean()
    print('angle', t, 'agree %.3f' % acc, 'split', int(rows[:, 1].sum()), 'pred', int(pred.sum()))
print('split edges angle percentiles', np.percentile(rows[rows[:, 1] > 0, 0], [5, 25, 50, 75]).round(1) if rows[:, 1].any() else '-')
print('smooth edges angle p95/p99', np.percentile(rows[rows[:, 1] == 0, 0], [95, 99]).round(1))
