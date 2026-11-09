#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Cleric of the Moon (faces -y). After the weld the body is a set of Smart Topology pieces (sizes at 9,883 faces):
face skin on the head atlas (2,124), robe top + bell sleeves (1,299), skirt (848), gold helmet (712), two open claw
hands (589 / 585), the back crescent (450), hair (396), two banners (354 / 346), two back rods with hooks (272 / 258),
and small pieces (collar, eyes, beads, rope ends, medallion, brooches). Labels: 1 face, 2 hair, 3 left hand,
4 right hand, 5 skirt, 6 robe top, 7 helmet, 8 crescent, 9 banners. Kept exactly: pieces of up to 250 faces, the two
back rods (thin tubes with hooks and beads, which break at any cut) and the skirt hem band below 12 cm."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); u = info['u']; dom = info['dom']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
big = [p for p in np.argsort(-sizes) if sizes[p] > 250]


def piece(pred):
    return [p for p in big if pred(pc == p)]


g = np.zeros(len(f), int)
face = piece(lambda m: (u[m] > .4925).mean() > .5)
hair = piece(lambda m: (u[m] <= .4925).all() and (dom[m] == 'B_Head').mean() > .3 and c[m, 2].min() > 1.1 and c[m, 2].max() < 1.45)
helmet = piece(lambda m: (dom[m] == 'B_Head').mean() > .9 and c[m, 2].min() > 1.35 and (u[m] <= .4925).all())
handL = piece(lambda m: (dom[m] == 'B_L_Hand').mean() > .6); handR = piece(lambda m: (dom[m] == 'B_R_Hand').mean() > .6)
banners = piece(lambda m: np.char.startswith(dom[m].astype(str), 'Banner').mean() > .5)
spine2 = piece(lambda m: (dom[m] == 'B_Spine2').mean() > .9)
crescent = [p for p in spine2 if c[pc == p, 0].min() < -.1 and c[pc == p, 0].max() > .1]
rods = [p for p in spine2 if p not in crescent]
skirt = piece(lambda m: c[m, 2].min() < .05 and c[m, 2].max() < 1.0)
top = [p for p in big if p not in face + hair + helmet + handL + handR + banners + spine2 + skirt]
for k, ps in ((1, face), (2, hair), (3, handL), (4, handR), (5, skirt), (6, top), (7, helmet), (8, crescent), (9, banners)):
    g[np.isin(pc, ps)] = k
keep = (size <= 250) | np.isin(pc, rods) | ((g == 5) & (c[:, 2] < .12))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('PIECES face', face, 'hair', hair, 'helmet', helmet, 'hands', handL, handR, 'banners', banners, 'crescent', crescent,
      'rods', rods, 'skirt', skirt, 'top', top)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(10)}, 'keep', int(keep.sum()))
