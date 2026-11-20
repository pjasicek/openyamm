#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Griffin (m258, faces -y, rest pose with the wings raised). Pieces: the main body with head, beak, wings, hind
legs (12,562 faces), the two eagle forelegs with talons (1,558, 1,408), the tail tuft (387) and the two eyes (117, 94).
Labels by dominant bone: 0 body (spine, neck, hind legs, tail chain), 1 head (Head: head feathers and beak), 2 wings
(Wing1-3), 3 eagle forelegs and talons (UpperArm/ForeArm/FrontPaw on the foreleg pieces), 4 tail tuft (its piece).
Kept exactly: the eyes."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); order = np.argsort(-sizes)
body, legs, tuft = order[0], order[1:3], order[3]
dom = info['dom'].astype(str)
g = np.zeros(len(f), int)
g[dom == 'Head'] = 1
g[np.char.startswith(dom, 'Wing')] = 2
g[np.isin(pc, legs)] = 3
g[pc == tuft] = 4
keep = sizes[pc] < 200                                                   # the eyes
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'keep', int(keep.sum()))
