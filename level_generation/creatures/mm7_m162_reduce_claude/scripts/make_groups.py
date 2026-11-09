#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep masks.
MM7 Behemoth (m162, faces -y, 2.2 m). Pieces: one skin piece (8,509 faces: body, head, ears, the three sickle claws
of each paw) and 337 small pieces (6,242 faces): about 240 mane shingles on the clavicles and spine, and on the head
the teeth, upper and lower tusks, eyes and the beard/crown shingles.
Labels of the skin piece by dominant bone: 0 torso, arms and legs, 1 head and neck (B_Head, B_Neck), 2 paws and claws
(B_*_Hand), 3 feet and toes (B_*_Foot, B_*_Toe0); 5 mane shingles (small pieces whose dominant bone is not B_Head).
work/keep_head.npy: the small head pieces (teeth, tusks, eyes, beard/crown shingles) kept exactly.
work/keep_small.npy: every small piece kept exactly (mane included)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); body = np.argmax(sizes)
dom = info['dom'].astype(str)
small = pc != body
headpiece = np.zeros(len(f), bool)
for p in np.unique(pc[small]):
    sel = pc == p; vals, cnt = np.unique(dom[sel], return_counts=True)
    headpiece[sel] = vals[cnt.argmax()] == 'B_Head'
g = np.zeros(len(f), int)
g[np.isin(dom, ['B_Head', 'B_Neck'])] = 1
g[np.isin(dom, ['B_L_Hand', 'B_R_Hand'])] = 2
g[np.isin(dom, ['B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'])] = 3
g[small] = 5
np.save('work/groups.npy', g); np.save('work/keep_head.npy', small & headpiece); np.save('work/keep_small.npy', small)
print('GROUPS', {k: int(((g == k) & ~(small & headpiece)).sum()) for k in (0, 1, 2, 3, 5)},
      'head pieces kept', int((small & headpiece).sum()), 'all small', int(small.sum()))
