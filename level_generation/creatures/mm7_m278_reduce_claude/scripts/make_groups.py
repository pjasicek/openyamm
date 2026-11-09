#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Manticore (m278, faces -y). Pieces: the skin (7,699 faces: lion body, face, legs, tail root), the five rigid
chitin tail segments (Tail2-6, 488-1,004 faces each; the stinger is Tail6) and 167 small pieces up to 200 faces
(mane shingles, claws, teeth, eyes, ear and brow pieces; 5,127 faces).
Labels: 0 skin (rest), 1 face (Head-dominated skin), 2 tail segments.
Kept exactly: every small piece (their ends taper into points at any cut)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); skin = np.argmax(sizes)
dom = info['dom'].astype(str)
g = np.zeros(len(f), int)
g[(pc == skin) & (dom == 'Head')] = 1
g[(pc != skin) & (sizes[pc] > 400)] = 2
keep = (pc != skin) & (sizes[pc] <= 400)
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(3)}, 'keep', int(keep.sum()))
