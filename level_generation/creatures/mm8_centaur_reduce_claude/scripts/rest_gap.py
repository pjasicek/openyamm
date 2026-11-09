#!/usr/bin/env python3
"""Rest-pose surface gaps: for every source vertex the distance to the candidate surface (work/mesh_r<NN>.npz),
point-to-triangle, local to 0.25 m. Prints the worst vertices with their dominant bone and piece size.
Usage: rest_gap.py <NN> [n]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def pt_tri(p, a, b, c):
    # closest-point distance from p (3,) to triangles (n,3) a,b,c (Ericson)
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-20, 1e-20, va + vb + vc)
    v = vb / den; w = vc / den
    q = a + ab * v[:, None] + ac * w[:, None]
    for cond, val in [((d1 <= 0) & (d2 <= 0), a), ((d3 >= 0) & (d4 <= d3), b), ((d6 >= 0) & (d5 <= d6), c)]:
        q[cond] = val[cond]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(d1 - d3 == 0, 1, d1 - d3); q[m] = (a + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(d2 - d6 == 0, 1, d2 - d6); q[m] = (a + ac * t[:, None])[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0); t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1, (d4 - d3) + (d5 - d6)); q[m] = (b + (c - b) * t[:, None])[m]
    return np.linalg.norm(q - p, axis=1).min() if len(q) else 9
d = np.load('work/mesh_in.npz'); c = np.load(f'work/mesh_r{sys.argv[1]}.npz'); g = np.load('work/groups.npz')
v, f = d['verts'], d['faces']; cv, cf = c['verts'], c['faces']; names = g['names']; W = g['W']
cen = cv[cf].mean(1); tree = cKDTree(cen)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
size = np.bincount(lab[f[:, 0]], minlength=lab.max() + 1)
gap = np.array([pt_tri(p, *(cv[cf[idx]].transpose(1, 0, 2))) for p, idx in ((p, tree.query_ball_point(p, .25)) for p in v)])
np.save(f'work/rest_gap_r{sys.argv[1]}.npy', gap)
print('p99 %.2f mm, max %.2f mm' % (np.percentile(gap, 99) * 1000, gap.max() * 1000))
for i in np.argsort(-gap)[:int(sys.argv[2]) if len(sys.argv) > 2 else 15]:
    print('%.1f mm' % (gap[i] * 1000), np.round(v[i], 3), names[W[i].argmax()], 'piece', lab[i], size[lab[i]])
