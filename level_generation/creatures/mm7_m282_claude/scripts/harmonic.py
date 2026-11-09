#!/usr/bin/env python3
"""Axial centreline of the Medusa skin from a harmonic field (python3): u = 0 at the rattle tip, 1 at the crown, Laplace
(cotangent-free graph Laplacian with 1/edge-length weights) elsewhere on the skin piece. Level sets of u are clean
cross-section rings along the tail and column (edge geodesics zig-zag on the long tail triangles). Band centroids of u
give the centreline; arms are dead-end branches with near-constant u and are excluded by distance from the band
centroid. Writes work/axial.json (points along the centreline with radius) and work/u.npy."""
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve
P = Path(__file__).resolve().parents[1]
d = np.load(P / 'work' / 'step1_mesh.npz'); co, pv, tri = d['co'], d['piece'], d['tri']
ids = np.where(pv == 0)[0]; idx = -np.ones(len(co), int); idx[ids] = np.arange(len(ids))
t = tri[(pv[tri] == 0).all(1)]
E = np.unique(np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1), axis=0)
w = 1.0 / np.maximum(np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1), 1e-4)
n = len(ids); a, b = idx[E[:, 0]], idx[E[:, 1]]
A = coo_matrix((np.r_[w, w], (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
L = diags(np.asarray(A.sum(1)).ravel()) - A
c = co[ids]
tipv = c[np.argmax(np.linalg.norm(c[:, :2], axis=1))]
fix0 = np.linalg.norm(c - tipv, axis=1) < 0.03
fix1 = c[:, 2] > c[:, 2].max() - 0.03
fixed = fix0 | fix1; val = np.where(fix1, 1.0, 0.0)
free = ~fixed
L = L.tocsr()
u = np.zeros(n); u[fixed] = val[fixed]
rhs = -L[free][:, fixed] @ u[fixed]
u[free] = spsolve(L[free][:, free].tocsc(), rhs)
U = np.full(len(co), -1.0); U[ids] = u
np.save(P / 'work' / 'u.npy', U)
pts = []
qs = np.unique(np.quantile(u, np.linspace(0, 1, 401)))
for lo, hi in zip(qs[:-1], qs[1:]):
    m = (u >= lo) & (u < hi)
    if m.sum() < 4:
        continue
    q = c[m]; ctr = q.mean(0)
    for _ in range(2):                               # drop far branch points (arms at the shoulder level)
        dd = np.linalg.norm(q - ctr, axis=1); keep = dd < np.median(dd) * 1.8
        ctr = q[keep].mean(0)
    pts.append([float((lo + hi) / 2), *ctr.tolist(), float(np.median(np.linalg.norm(q[keep] - ctr, axis=1)))])
pts = np.array(pts)
for k in range(0, len(pts), 8):
    print('U %.3f c (%.3f %.3f %.3f) r %.3f' % tuple(pts[k]))
(P / 'work' / 'axial.json').write_text(json.dumps({'u_c_r': np.round(pts, 5).tolist()}))
