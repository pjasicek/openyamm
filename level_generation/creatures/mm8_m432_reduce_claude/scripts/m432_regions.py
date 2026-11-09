#!/usr/bin/env python3
"""Per-face region labels of the Dark Elf warrior rest mesh (work/mesh_in.npz) by connected piece -> work/regions.npy:
1 body suit, 2 head skin (face, ears, neck), 3 hair (shell + loose strand), 4 gloves (sword grip, both hands),
5 boots, 6 pauldrons, 7 eyes, 8 small pieces (studs). work/soles.npy: boot faces below 6 cm (foot contact patches).
Prints the counts."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
reg = np.full(len(f), 8)
for p in np.flatnonzero(sizes):
    m = fl == p; cp = c[m].mean(0); s = sizes[p]
    if s > 3000:
        reg[m] = 1
    elif s > 1800:
        reg[m] = 2
    elif s > 1000:
        reg[m] = 3
    elif s > 700:
        reg[m] = 4
    elif s > 500:
        reg[m] = 5
    elif s > 240:
        reg[m] = 6
    elif s > 150:
        reg[m] = 7
    elif s > 40 and cp[2] > 1.7:
        reg[m] = 3  # loose hair strand beside the face
soles = (reg == 5) & (c[:, 2] < 0.06)
np.save('work/regions.npy', reg); np.save('work/soles.npy', soles)
names = {1: 'body', 2: 'head', 3: 'hair', 4: 'gloves', 5: 'boots', 6: 'pauldrons', 7: 'eyes', 8: 'small'}
print({names[k]: int((reg == k).sum()) for k in names}, 'soles', int(soles.sum()))
