#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 Vampire female peasant (faces -y). Pieces: legs/trousers/boots 3,751, torso/jacket/sleeves 3,435, head skin
2,020, hair 1,244, hands 612 / 608, eyes and teeth (49). Labels: 0 rest, 1 face and ears skin (the head piece),
2 hair (the separate head-atlas piece), 3 left hand, 4 right hand. Kept exactly: pieces of up to 250 faces (eyes,
teeth); REA_KEEP_HANDS=1 also keeps both hands (612 / 608 faces, already light; fingers and the hand-on-hip pose)."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); head = info['u'] > .505
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
whole_head = [p for p in np.unique(pc[head]) if head[pc == p].all() and sizes[p] > 250]
face_piece = max(whole_head, key=lambda p: (np.isin(info['dom'][pc == p], ['B_Head']).mean() < 1, sizes[p]))
hair_piece = next(p for p in whole_head if p != face_piece)
g = np.zeros(len(f), int)
g[pc == face_piece] = 1
g[pc == hair_piece] = 2
hands = (size >= 400) & (size <= 900) & (np.abs(c[:, 0]) > .25)
g[hands & (c[:, 0] > 0)] = 3; g[hands & (c[:, 0] < 0)] = 4
keep = size <= 250
if os.environ.get('REA_KEEP_HANDS') == '1':
    keep |= (g == 3) | (g == 4)
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'keep', int(keep.sum()),
      'face piece', sizes[face_piece], 'hair piece', sizes[hair_piece])
