#!/usr/bin/env python3
"""Per-part weights for decimated meshes (REA_WEIGHTS=component in reduce_ladder.py): each candidate vertex takes its
weights from the source part (connected component) it was decimated from. Vertices that are source vertices keep
their weights exactly; the others blend the three nearest source vertices of that part (inverse distance). A
candidate component's part is the majority part of its vertices' nearest source vertices.
Usage: component_weights.py <ratio,...>  (work/mesh_in.npz, work/src_weights.npz, work/mesh_r<NN>.npz -> work/weights_r<NN>.npz)"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


def parts(n, f):
    rows = np.r_[f[:, 0], f[:, 1], f[:, 2]]; cols = np.r_[f[:, 1], f[:, 2], f[:, 0]]
    return connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)), directed=False)[1]


s = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz'); W = sw['weights']
sv = s['verts']; spart = parts(len(sv), s['faces']); stree = cKDTree(sv)
for r in [float(x) for x in sys.argv[1].split(',')]:
    tag = int(r * 100); d = np.load(f'work/mesh_r{tag}.npz'); v, f = d['verts'], d['faces']
    dist, near = stree.query(v); cpart = parts(len(v), f); owner = np.zeros(len(v), int)
    for p in np.unique(cpart):
        m = cpart == p; owner[m] = np.bincount(spart[near[m]]).argmax()
    out = np.zeros((len(v), W.shape[1]), np.float32)
    for p in np.unique(owner):
        m = owner == p; idx = np.where(spart == p)[0]; k = min(3, len(idx))
        dd, nn = cKDTree(sv[idx]).query(v[m], k)
        dd, nn = dd.reshape(len(dd), -1), nn.reshape(len(nn), -1)
        wt = 1 / np.maximum(dd, 1e-6); wt /= wt.sum(1, keepdims=True)
        out[m] = (W[idx[nn]] * wt[..., None]).sum(1)
    exact = dist < 1e-7; out[exact] = W[near[exact]]
    np.savez(f'work/weights_r{tag}.npz', weights=out, names=sw['names'])
    print('WEIGHTS', tag, len(v), 'exact', int(exact.sum()), 'parts', len(np.unique(owner)))
