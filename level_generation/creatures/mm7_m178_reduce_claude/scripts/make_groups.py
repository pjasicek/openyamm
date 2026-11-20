#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep masks.
MM7 Devil (m178, faces -y, 1.70 m rest, 1.5 m tail towards +y). Pieces: one closed skin (9,000 faces: head with ears,
horns and skull/shoulder/forearm spikes, four-fingered clawed hands, slate feet with heel spurs, tail) and 22 small
pieces (977 faces: 8 tooth pieces, 2 eyes, 12 tail spikes).
Labels: 0 torso, arms, legs (rest of the skin); 1 head texture set (u > 0.5 in the 2080x1024 atlas) outside the face
front; 2 hands and claws (B_*_Hand dominated); 3 feet and toes (B_*_Foot, B_*_Toe0); 6 tail (B_Tail*); 7 face front
(head set, centroid in front of FRONT_Y and below FRONT_ZMAX: brow, eyes, nose, lips, chin).
work/keep_small.npy: every small piece kept exactly, plus the SOLES (faces whose three vertices are within SOLE_Z of the
rest floor: the levelled feet stand on them). work/keep_front.npy: keep_small plus the face front."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SOLE_Z = float(os.environ.get('SOLE_Z', '0.03'))
FRONT_Y = float(os.environ.get('FRONT_Y', '-0.15'))
FRONT_ZMAX = float(os.environ.get('FRONT_ZMAX', '1.58'))
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); body = np.argmax(sizes)
dom = info['dom'].astype(str)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
small = pc != body
nrm = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
cen = v[f].mean(1)
g = np.zeros(len(f), int)
g[np.array(['Hand' in x or 'Finger' in x for x in dom])] = 2
g[np.array(['Foot' in x or 'Toe0' in x for x in dom])] = 3
g[np.char.startswith(dom, 'B_Tail')] = 6
head = (u > 0.5) & ~small
g[head] = 1
front = head & (cen[:, 1] < FRONT_Y) & (cen[:, 2] < FRONT_ZMAX)
g[front] = 7
z = v[:, 2]; zmin = z.min()
soles = (z[f] < zmin + SOLE_Z).all(1) & (g == 3)
np.save('work/groups.npy', g); np.save('work/keep_small.npy', small | soles); np.save('work/keep_soles.npy', soles)
np.save('work/keep_front.npy', small | soles | front)
print('GROUPS', {k: int(((g == k) & ~small).sum()) for k in (0, 1, 2, 3, 6, 7)}, 'small kept', int(small.sum()),
      'sole faces kept', int(soles.sum()), 'face front', int(front.sum()))
