#!/usr/bin/env python3
"""Per-face piece labels of the m218 rest mesh (work/mesh_in.npz) by connected piece and position -> work/pieces.npy:
1 head skin (main shell, head texture set u > 0.51: face, ears, hair), 2 body skin (main shell, body set), 3 hands
(fingers; the spear grips are solved), 4 eyes and mouth pieces, 5 crown leaves (small head pieces above 1.6 m),
6 bracers, 7 belt, 8 loincloth panels, 9 back shaft, 10 hip pouch, 11 ponytail, 12 other small pieces (loincloth tabs,
necklace beads, pouch flap); work/soles.npy: body faces below 6 cm."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v); wuv = d['wuv'].reshape(-1, 3, 2)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1); hu = wuv[:, :, 0].mean(1) > 0.51
reg = np.zeros(len(f), int)
for p in np.flatnonzero(sizes):
    m = fl == p; cp = c[m].mean(0); s = sizes[p]; head = hu[m].mean() > .5
    if s > 3000:
        reg[m & hu] = 1; reg[m & ~hu] = 2
    elif s > 900:
        reg[m] = 3
    elif head and cp[2] < 1.6 and cp[1] < -0.05:
        reg[m] = 4
    elif head and cp[2] >= 1.6:
        reg[m] = 5
    elif s > 60 and abs(cp[0]) > 0.3:
        reg[m] = 6
    elif s > 150 and 0.95 < cp[2] < 1.05:
        reg[m] = 7
    elif s > 100 and 0.85 < cp[2] < 0.95 and abs(cp[0]) < 0.05:
        reg[m] = 8
    elif s > 250:
        reg[m] = 9
    elif s > 100 and abs(cp[0]) > 0.1:
        reg[m] = 10
    elif s > 60:
        reg[m] = 11
    else:
        reg[m] = 12
soles = (reg == 2) & (c[:, 2] < 0.06)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles)
names = {1: 'head skin', 2: 'body skin', 3: 'hands', 4: 'eyes/mouth', 5: 'crown leaves', 6: 'bracers', 7: 'belt',
         8: 'loincloth', 9: 'back shaft', 10: 'pouch', 11: 'ponytail', 12: 'small pieces'}
print({names[k]: int((reg == k).sum()) for k in names}, 'unlabelled', int((reg == 0).sum()), 'soles', int(soles.sum()))
