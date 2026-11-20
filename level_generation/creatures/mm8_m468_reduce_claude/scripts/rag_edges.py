#!/usr/bin/env python3
"""Ragged cloth edges (MM8 Vampire): faces of the vest (label 4) and trousers (label 5) that touch an open edge of the
welded mesh (the torn hems and flap points), plus REA_RING rings of neighbours. The collapse rounds the jags off and
pulls skin-coloured gutter into the hem (ladder b), so the edges are kept exactly.
Usage: rag_edges.py <base keep .npy> <out .npy> [labels, default 4,5]"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']; g = np.load('work/groups.npy')
labels = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else '4,5').split(',')]
e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1)
u, cnt = np.unique(e, axis=0, return_counts=True)
bverts = np.unique(u[cnt == 1])
sel = np.isin(g, labels) & np.isin(f, bverts).any(1)
for _ in range(int(os.environ.get('REA_RING', '0'))):
    vs = np.unique(f[sel]); sel |= np.isin(g, labels) & np.isin(f, vs).any(1)
keep = np.load(sys.argv[1]) | sel
np.save(sys.argv[2], keep)
print('RAG', {k: int((sel & (g == k)).sum()) for k in labels}, 'of', {k: int((g == k).sum()) for k in labels}, 'keep', int(keep.sum()))
