"""Faces of small separate source pieces (connected by shared vertices in the welded work/mesh_in.npz, at most
REA_PIECE_VERTS vertices, default 110): belt, belt medallion, front panel, bracers. Their ends and painted rims fray at
any cut (belt medallion gold shard, smeared panel studs at 70 %). -> work/small_pieces.npy"""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; n = len(d['verts'])
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
size = np.bincount(lab); small = size[lab[f[:, 0]]] <= int(os.environ.get('REA_PIECE_VERTS', '110'))
c = d['verts'][f].mean(1)
for p in np.unique(lab[f[small, 0]]):
    sel = lab[f[:, 0]] == p; print('PIECE', size[p], 'verts', int(sel.sum()), 'faces at', np.round(c[sel].mean(0), 2))
np.save('work/small_pieces.npy', small); print('KEEP', int(small.sum()), 'faces')
