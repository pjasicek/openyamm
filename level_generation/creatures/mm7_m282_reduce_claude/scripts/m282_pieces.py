#!/usr/bin/env python3
"""Per-face piece labels of the medusa rest mesh (work/mesh_in.npz) from the batch I master's 'piece' attribute
(work/master_pieces.npz, dump_pieces.py; nearest rest vertex, majority per face) -> work/pieces.npy, plus connected
pieces (sizes, centres) and the head texture set (u > 0.51 in the merged atlas) -> work/headset.npy."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; m = np.load('work/master_pieces.npz')
dist, i = cKDTree(m['P']).query(v); vp = m['piece'][i]
print('map dist mm max', round(float(dist.max()) * 1000, 3), 'p99', round(float(np.percentile(dist, 99)) * 1000, 3))
fp = np.array([np.bincount(r, minlength=100).argmax() for r in vp[f]])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1); head = u > 0.51
np.save('work/pieces.npy', fp); np.save('work/headset.npy', head); np.save('work/component.npy', fl)
for k in np.unique(fp):
    s = fp == k; c = v[f[s]].reshape(-1, 3)
    print(f'piece {k:3d} faces {s.sum():5d} comps {len(np.unique(fl[s])):3d} head-set {int((s & head).sum()):5d} '
          f'centre {np.round(c.mean(0), 3)} z {c[:, 2].min():.3f}..{c[:, 2].max():.3f}')
print('components', int((sizes > 0).sum()), 'sizes', sorted(sizes[sizes > 0].tolist(), reverse=True)[:45])
