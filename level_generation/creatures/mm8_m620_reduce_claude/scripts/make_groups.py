#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 Bedraggled Human (faces -y). Labels: 0 rest (vest, torso, trousers, boots), 1 head skin (head-atlas faces of the
head/body piece: face, ears, neck), 2 hair volume (the separate hair_v3 piece, 1,248 faces), 3 left hand, 4 right hand
(faces dominated by a hand or finger bone), 5 face (head skin in front of y = REA_FACE_Y, default 0.0, above the
chin, z > 1.49: eyes, nose, mouth, cheeks). Group 1 is then the scalp under the hair, the ears, the back and the neck. Kept exactly: pieces of up to REA_SMALL faces (default 80: the hair
strands over the scalp, waist cords) and the soles (faces below 1.5 cm)."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); head = info['u'] > .505; dom = info['dom']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
hair_piece = max((p for p in np.unique(pc[head]) if head[pc == p].all()), key=lambda p: sizes[p])
g = np.zeros(len(f), int)
g[head & (pc != hair_piece)] = 1
g[pc == hair_piece] = 2
hand = np.array([('Hand' in b or 'Finger' in b) for b in dom])
g[(g == 1) & (c[:, 1] < float(os.environ.get('REA_FACE_Y', '0.0'))) & (c[:, 2] > 1.49)] = 5
g[hand & (c[:, 0] > 0)] = 3; g[hand & (c[:, 0] < 0)] = 4
keep = size <= int(os.environ.get('REA_SMALL', '80'))
keep |= v[f][:, :, 2].max(1) < 0.015
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(6)}, 'keep', int(keep.sum()), 'soles', int((v[f][:, :, 2].max(1) < 0.015).sum()))
