#!/usr/bin/env python3
"""Per-face piece labels of the m406 rest mesh (work/mesh_in.npz) by connected piece and position -> work/pieces.npy:
1 head (face, beard, scalp, neck skin), 2 helmet, 3 mail coif, 4 eyes, 5 torso + tabard, 6 legs + boots,
7 gauntlets (hands, fingers), 8 arms, 9 belt buckle, 10 knee pieces; work/soles.npy: leg faces below 6 cm."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
reg = np.zeros(len(f), int)
for p in np.flatnonzero(sizes):
    m = fl == p; cp = c[m].mean(0); s = sizes[p]; zt = v[f[m]][..., 2].max()
    if s > 2000:
        reg[m] = 1
    elif s > 1000 and cp[2] < 0.6:
        reg[m] = 6
    elif s > 1000 and abs(cp[0]) > 0.3:
        reg[m] = 7
    elif s > 1000:
        reg[m] = 5
    elif s > 600 and zt > 1.65:
        reg[m] = 2
    elif s > 400:
        reg[m] = 8
    elif s > 250 and cp[2] > 1.3:
        reg[m] = 3
    elif s > 150:
        reg[m] = 9
    elif cp[2] > 1.4:
        reg[m] = 4
    else:
        reg[m] = 10
soles = (reg == 6) & (c[:, 2] < 0.06)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles)
names = {1: 'head', 2: 'helmet', 3: 'coif', 4: 'eyes', 5: 'torso', 6: 'legs', 7: 'gauntlets', 8: 'arms', 9: 'buckle', 10: 'knee'}
print({names[k]: int((reg == k).sum()) for k in names}, 'unlabelled', int((reg == 0).sum()), 'soles', int(soles.sum()))
