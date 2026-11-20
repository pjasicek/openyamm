#!/usr/bin/env python3
"""Per-face region labels of the Chain Fighter rest mesh (work/mesh_in.npz) by connected piece and texture set ->
work/regions.npy: 1 body (torso, skirt, legs, boots: the body texture set of the main piece), 2 head skin and hair
(the head texture set of the main piece), 3 arm shells (sleeves, gauntlets, fingers), 4 helmet / coif, 5 shoulder
guard, 6 gold panels, 7 neck trims, 8 small pieces (<= 80 faces: belt links, eyes). work/soles.npy: body faces below
6 cm (foot contact patches). Prints the counts."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
headset = d['wuv'].reshape(-1, 3, 2)[..., 0].mean(1) > .5
reg = np.full(len(f), 8)
for p in np.flatnonzero(sizes):
    m = fl == p; s = sizes[p]
    if s > 3000:
        reg[m] = np.where(headset[m], 2, 1)
    elif s > 1000:
        reg[m] = 3
    elif s > 400:
        reg[m] = 4
    elif s > 230:
        reg[m] = 5
    elif s > 150:
        reg[m] = 6
    elif s > 80:
        reg[m] = 7
soles = (reg == 1) & (c[:, 2] < 0.06)
np.save('work/regions.npy', reg); np.save('work/soles.npy', soles)
names = {1: 'body', 2: 'head', 3: 'arms', 4: 'helmet', 5: 'shoulder', 6: 'gold panels', 7: 'neck trims', 8: 'small'}
print({names[k]: int((reg == k).sum()) for k in names}, 'soles', int(soles.sum()))
