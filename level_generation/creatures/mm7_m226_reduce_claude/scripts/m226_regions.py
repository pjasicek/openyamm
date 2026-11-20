#!/usr/bin/env python3
"""Per-face region labels of the m226 Leather Fighter rest mesh (work/mesh_in.npz) by connected piece (sizes from
small_pieces.py) -> work/regions.npy: 1 skin (body, arms, boots), 2 head skin, 3 hair cap, 4 hands (separate shells,
sword grip), 5 ponytail + loose strand, 6 shoulder yoke, 7 dagger + sheath, 8 back scabbard, 9 belt + buckle,
10 thigh strap, 11 small pieces (<= REA_SMALL faces: studs, spikes, buckles, eyes, face strands).
work/soles.npy: skin faces below 6 cm (boot contact patches)."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v)
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
LIM = int(os.environ.get('REA_SMALL', '80'))
uvu = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
reg = np.zeros(len(f), int)
for p in np.flatnonzero(sizes):
    m = fl == p; s = sizes[p]; vs = np.unique(f[m]); cp = v[vs].mean(0)
    dom = names[int(np.argmax(W[vs].sum(0)))]; headset = (uvu[m] > .5).mean() > .5
    if s <= LIM:
        r = 11
    elif s > 2000:
        r = 1
    elif headset and dom == 'B_Head' and s > 1000:
        r = 2
    elif headset and s > 500:
        r = 3
    elif headset:
        r = 5
    elif dom.endswith('_Hand'):
        r = 4
    elif cp[2] > 1.25 and abs(cp[1]) < .1:
        r = 6
    elif dom == 'B_Spine2':
        r = 8
    elif dom == 'B_Pelvis' and W[vs][:, names.index('B_Pelvis')].min() > .99:
        r = 7
    elif dom.endswith('_Thigh'):
        r = 10
    else:
        r = 9
    reg[m] = r
soles = (reg == 1) & (c[:, 2] < 0.06)
np.save('work/regions.npy', reg); np.save('work/soles.npy', soles)
nm = {1: 'skin', 2: 'head', 3: 'hair', 4: 'hands', 5: 'ponytail', 6: 'yoke', 7: 'dagger', 8: 'scabbard', 9: 'belt',
      10: 'strap', 11: 'small'}
print({nm[k]: int((reg == k).sum()) for k in nm}, 'unlabelled', int((reg == 0).sum()), 'soles', int(soles.sum()))
