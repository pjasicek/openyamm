#!/usr/bin/env python3
"""Skin weights for decimated meshes of the Malevolent Boulder (REA_WEIGHTS=component in reduce_ladder.py reads the
output, like uv_weights.py). The boulder is 122 separate rigid stones, one bone each. Many stones share texture
space, so a UV lookup lands on the wrong stone, and stones overlap, so a nearest-vertex fallback takes a neighbour's
bone; both tore stones apart in Death (120 mm errors). Here every output vertex takes the bone of its own stone: the
source piece that most of its output component's kept vertices (src_index) belong to; a component with no kept
vertex uses its nearest source vertices. Source vertices keep their weights exactly. Reports components that span
more than one source piece (stones bridged by the collapse).
Usage: piece_weights.py <ratio,...>  (work/mesh_in.npz, work/src_weights.npz, work/mesh_r<NN>.npz -> work/weights_r<NN>.npz)"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


def components(n, f):
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    return connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)[1]


s = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz'); W = sw['weights']
src_piece = components(len(s['verts']), s['faces']); tree = cKDTree(s['verts'])
for r in sys.argv[1].split(','):
    tag = int(float(r) * 100); d = np.load(f'work/mesh_r{tag}.npz'); v, f, si = d['verts'], d['faces'], d['src_index']
    lab = components(len(v), f); out = np.zeros((len(v), W.shape[1]), np.float32); bridged = 0
    for c in np.unique(lab):
        ids = np.where(lab == c)[0]; kept = si[ids][si[ids] >= 0]
        votes = src_piece[kept] if len(kept) else src_piece[tree.query(v[ids])[1]]
        pieces, counts = np.unique(votes, return_counts=True)
        bridged += len(pieces) > 1
        piece = pieces[np.argmax(counts)]
        out[ids] = W[np.where(src_piece == piece)[0][0]]
    exact = si >= 0; out[exact] = W[si[exact]]
    np.savez(f'work/weights_r{tag}.npz', weights=out, names=sw['names'])
    print('PIECEWEIGHTS', tag, len(v), 'exact', int(exact.sum()), 'components', lab.max() + 1, 'bridged', bridged)
