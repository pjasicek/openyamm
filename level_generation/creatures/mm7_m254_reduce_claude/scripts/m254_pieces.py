#!/usr/bin/env python3
"""Per-face piece labels of the m254 Golem rest mesh (work/mesh_in.npz) by connected piece, size and position ->
work/pieces.npy: 1 face/neck skin (head texture set of the skin shell, u > 0.51), 2 body skin, 3 loincloth (striped
shendyt), 4 collar, 5 crown (modius), 6 nemes, 7 belt, 8 beard, 9 horns, 10 cuffs (wrist and ankle), 11 horn sockets,
12 eyes, 13 ear studs, 14 collar studs; work/soles.npy: body-skin faces below 6 cm."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v, w = d['faces'], d['verts'], d['wuv']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
um = w.reshape(-1, 3, 2)[:, :, 0].mean(1)
reg = np.zeros(len(f), int)
for p in np.flatnonzero(sizes):
    m = fl == p; cp = c[m].mean(0); s = sizes[p]
    if s > 3000:
        reg[m] = 2; reg[m & (um > 0.51)] = 1
    elif s > 430:
        reg[m] = 3
    elif s > 390 and cp[2] > 1.6:
        reg[m] = 5
    elif s > 390:
        reg[m] = 4
    elif s > 300:
        reg[m] = 6
    elif s > 200:
        reg[m] = 7
    elif s > 150:
        reg[m] = 8
    elif s > 100 and cp[2] > 1.5:
        reg[m] = 9
    elif s > 80 and cp[2] < 1.2:
        reg[m] = 10
    elif s > 80:
        reg[m] = 11
    elif s > 40 and cp[2] > 1.5:
        reg[m] = 12
    elif cp[2] > 1.5:
        reg[m] = 13
    else:
        reg[m] = 14
soles = (reg == 2) & (c[:, 2] < 0.06)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles)
names = {1: 'face skin', 2: 'body skin', 3: 'loincloth', 4: 'collar', 5: 'crown', 6: 'nemes', 7: 'belt', 8: 'beard',
         9: 'horns', 10: 'cuffs', 11: 'sockets', 12: 'eyes', 13: 'ear studs', 14: 'collar studs'}
print({names[k]: int((reg == k).sum()) for k in names}, 'unlabelled', int((reg == 0).sum()), 'soles', int(soles.sum()))
print('head-set faces per piece', {names[k]: int(((reg == k) & (um > 0.51)).sum()) for k in names})
print('top', round(float(v[:, 2].max()), 4), 'top piece', names[reg[np.argmax(v[f][:, :, 2].max(1))]])
