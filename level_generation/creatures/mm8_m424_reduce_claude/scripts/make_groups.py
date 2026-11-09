#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 Dark Elf peasant (faces -y). Labels: 0 rest (torso, trousers, boots, sleeves), 1 face and ears skin (head set,
not hair), 2 hair (the separate hair piece), 3 left hand, 4 right hand (holds the dagger). Kept exactly: pieces of up
to 250 faces (eyes, teeth, sleeve attachment rings); REA_KEEP_RHAND=1 also keeps the right hand (dagger grip)."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); head = info['u'] > .505
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
hair_piece = max((p for p in np.unique(pc[head])), key=lambda p: sizes[p] if head[pc == p].all() else -1)
g = np.zeros(len(f), int)
g[head & (pc != hair_piece)] = 1
g[pc == hair_piece] = 2
hands = (size >= 1200) & (size <= 1800) & (np.abs(c[:, 0]) > .4)
g[hands & (c[:, 0] > 0)] = 3; g[hands & (c[:, 0] < 0)] = 4
keep = size <= 250
if os.environ.get('REA_KEEP_RHAND') == '1':
    keep |= g == 4
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'keep', int(keep.sum()))
