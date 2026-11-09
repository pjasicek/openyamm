#!/usr/bin/env python3
"""Rest-pose two-way error of ladder meshes (work/mesh_<tag>.npz) against the source (work/mesh_in.npz), per source
piece (connected component) and region: p99/max of source vertex -> candidate surface. Usage: rest_error.py <tag...>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
s = np.load('work/mesh_in.npz'); f, v = s['faces'], s['verts']; n = len(v)
reg = np.load('work/regions.npy')
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
vreg = np.zeros(n, int); vreg[f.ravel()] = np.repeat(reg, 3)
for tag in sys.argv[1:]:
    d = np.load(f'work/mesh_{tag}.npz'); tri = d['verts'][d['faces']]
    # dense surface samples of the candidate (about 1 mm spacing on large faces) as a point-to-surface proxy
    area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
    k = np.clip((area / 1e-6).astype(int), 3, 400); fi = np.repeat(np.arange(len(tri)), k)
    b = np.random.default_rng(0).dirichlet((1, 1, 1), len(fi))
    pts = np.concatenate([np.einsum('nk,nkc->nc', b, tri[fi]), d['verts']])
    dist = cKDTree(pts).query(v)[0] * 1000
    print(tag, 'rest p99 %.2f max %.2f mm' % (np.percentile(dist, 99), dist.max()))
    for p in np.unique(lab):
        sel = lab == p
        if dist[sel].max() > 4:
            i = np.flatnonzero(sel)[dist[sel].argmax()]
            print('  piece', p, 'region', vreg[sel][0], 'verts', sel.sum(), 'p95 %.1f max %.1f at' % (np.percentile(dist[sel], 95), dist[sel].max()), np.round(v[i], 3))
