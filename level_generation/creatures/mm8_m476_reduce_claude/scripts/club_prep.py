#!/usr/bin/env python3
"""Club for decimate_tex.py: weld exact duplicate positions of work/club_in.npz (glTF splits at UV seams; wedge UVs stay
per corner) into work/club/mesh_in.npz, and keep the grip (club_grip.npy) plus small separate pieces (up to
REA_SMALL faces: wraps, rivets) exactly -> work/club/keep.npy. Prints the pieces."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/club_in.npz'); v, f = d['verts'], d['faces']
key = np.round(v / 1e-6).astype(np.int64)
_, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
nv = v[first]; nf = inv.reshape(-1)[f]
os.makedirs('work/club', exist_ok=True)
np.savez('work/club/mesh_in.npz', verts=nv, faces=nf.astype(np.int32), wuv=d['wuv'], protect=np.zeros(len(nf)))
n = len(nv); e = np.concatenate([nf[:, [0, 1]], nf[:, [1, 2]], nf[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[nf[:, 0]]; sizes = np.bincount(fl)
for c in np.argsort(-sizes):
    if sizes[c]:
        m = fl == c; p = nv[nf[m]].reshape(-1, 3)
        print('piece', c, sizes[c], 'z %.3f..%.3f' % (p[:, 2].min(), p[:, 2].max()), 'xy span', (p[:, :2].max(0) - p[:, :2].min(0)).round(3))
keep = np.load('work/club_grip.npy') | (sizes[fl] <= int(os.environ.get('REA_SMALL', '80')))
np.save('work/club/keep.npy', keep); np.save('work/club/piece.npy', fl)
print('WELD', len(v), '->', len(nv), 'verts; keep', int(keep.sum()), 'of', len(nf))
