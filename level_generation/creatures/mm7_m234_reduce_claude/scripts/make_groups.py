#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep masks.
MM7 Gargoyle (m234, faces -y, 1.913 m incl. the folded wings). Pieces: one stone shell (9,539 faces: body, head with
horns and ears, arms and clawed hands, wing arms and struts, membranes welded to it, tail) and 19 small pieces: the two
eyes, 16 teeth and the tail spade (1,273 faces).
Labels by dominant bone: 0 torso, arms and legs; 1 head and neck (B_Head, B_Neck: face, horns, ears); 2 hands and
claws (B_*_Hand, B_*_Finger*); 3 feet and toes (B_*_Foot, B_*_Toe0); 4 wings (Wing_*); 6 tail (Tail_*).
work/keep_small.npy: every small piece (eyes, teeth, spade) kept exactly, plus the SOLES (faces whose three vertices
are within SOLE_Z of the rest floor: the user-fixed flat feet stand on them)."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SOLE_Z = float(os.environ.get('SOLE_Z', '0.03'))
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); body = np.argmax(sizes)
dom = info['dom'].astype(str)
small = pc != body
g = np.zeros(len(f), int)
g[np.char.startswith(dom, 'B_Head') | np.char.startswith(dom, 'B_Neck')] = 1
g[np.array(['Hand' in x or 'Finger' in x for x in dom])] = 2
g[np.array(['Foot' in x or 'Toe0' in x for x in dom])] = 3
g[np.char.startswith(dom, 'Wing_')] = 4
g[np.char.startswith(dom, 'Tail_')] = 6
z = v[:, 2]; zmin = z.min()
soles = (z[f] < zmin + SOLE_Z).all(1) & np.isin(g, [3])
np.save('work/groups.npy', g); np.save('work/keep_small.npy', small | soles); np.save('work/keep_soles.npy', soles)
print('GROUPS', {k: int(((g == k) & ~small).sum()) for k in (0, 1, 2, 3, 4, 6)}, 'small kept', int(small.sum()),
      'sole faces kept', int(soles.sum()))
