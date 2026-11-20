#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 Wererat, rat form (m452, faces -y). Pieces: one body with head, paws and tail (6,424 faces), the two eyes (58,
48), a detached paw piece (18), four incisors (12 each) and six single-triangle whiskers. Labels by dominant bone:
0 body (spine, neck, legs), 1 head (Head, Jaw), 2 front paws, 3 hind paws, 4 tail (Tail1-6).
Kept exactly: every piece other than the body (eyes, incisors, whiskers, the paw piece)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); body = np.argmax(sizes)
dom = info['dom'].astype(str)
g = np.zeros(len(f), int)
g[np.isin(dom, ['Head', 'Jaw'])] = 1
g[np.isin(dom, ['FrontPaw_L', 'FrontPaw_R'])] = 2
g[np.isin(dom, ['HindPaw_L', 'HindPaw_R'])] = 3
g[np.char.startswith(dom, 'Tail')] = 4
keep = pc != body
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'keep', int(keep.sum()))
