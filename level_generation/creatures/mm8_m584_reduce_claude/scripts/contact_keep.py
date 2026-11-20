#!/usr/bin/env python3
"""Faces of one connected piece that lie within REA_CONTACT_R (default 8 mm) of another piece's surface in the rest
pose (bra cups and studs on the skin, loincloth over the shorts, knee guards, belt): the collapse moves either layer
a few millimetres and the lower one pokes through. Wings are excluded as neighbours (they are kept whole anyway).
Writes work/keep_contact.npy and prints the count. Usage: contact_keep.py"""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; region = np.load('work/region.npy')
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]
R = float(os.environ.get('REA_CONTACT_R', '0.008'))
# dense samples on each face (centroid + 3 edge midpoints + corners) labelled by piece
bary = np.array([[1/3, 1/3, 1/3], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
pts = np.einsum('sk,fkd->fsd', bary, v[f])
nonwing = region != 1
samp = pts[nonwing].reshape(-1, 3); spiece = np.repeat(fl[nonwing], len(bary))
tree = cKDTree(samp)
keep = np.zeros(len(f), bool)
for i in np.flatnonzero(nonwing):
    for p in pts[i]:
        if any(spiece[j] != fl[i] for j in tree.query_ball_point(p, R)):
            keep[i] = True; break
np.save('work/keep_contact.npy', keep)
print('CONTACT', int(keep.sum()), 'faces within', R, 'm of another piece; by region',
      {k: int((keep & (region == k)).sum()) for k in range(4)})
