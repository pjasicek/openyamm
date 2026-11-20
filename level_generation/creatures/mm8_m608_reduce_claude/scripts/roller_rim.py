#!/usr/bin/env python3
"""Keep the rolling contour of each roller exactly: faces with a vertex within REA_RIM_MM (default 3) of the convex hull
of the roller seen along its x axis (any of those vertices can be the lowest at some roll angle): the reduced rollers otherwise dipped 1.4 mm under the floor in Walking, and the
creature's contact audit keeps every rolling subframe above it. Usage: roller_rim.py <base keep .npy> <out .npy>"""
import os, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; reg = np.load('work/regions.npy')
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); band = float(os.environ.get('REA_RIM_MM', '3')) / 1000
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v),) * 2), directed=False)
for piece in np.unique(lab[f[reg == 4][:, 0]]):
    vs = np.flatnonzero(lab == piece); c = (v[vs].min(0) + v[vs].max(0)) / 2
    from scipy.spatial import ConvexHull
    h = ConvexHull(v[vs][:, 1:]); eq = h.equations  # n.x + o <= 0 inside
    dist = -(v[vs][:, 1:] @ eq[:, :2].T + eq[:, 2]).max(1)
    rim = np.zeros(len(v), bool); rim[vs[dist < band]] = True; r = np.zeros(len(v)); r[vs] = np.hypot(*(v[vs][:, 1:] - c[1:]).T)
    keep |= rim[f].any(1)
    print('ROLLER piece', piece, 'radius %.3f' % r[vs].max(), 'rim verts', int(rim.sum()))
np.save(sys.argv[2], keep); print('RIM kept faces', n0, '->', int(keep.sum()))
