#!/usr/bin/env python3
"""Per-face piece labels of the m214 rest mesh (work/mesh_in.npz, groups.npz) by connected piece, its mean weights and
position -> work/pieces.npy:
1 head piece (face, ears, scalp, neck and the skin under the vest), 2 hair, 3 eyes, 4 vest (with the upper arms),
5 trousers, 6 hands (fingers; the left fist holds the bow), 7 forearms (tooled bracers), 8 quiver, 9 quiver arrows and
fletchings, 10 waist straps, 11 bare feet and calves, 12 bowstring (skinned tube: Bow ends, StringNock middle),
13 pouches and belt bits, 14 calf lacing, 15 small head piece (hair tie); work/soles.npy: foot faces below 6 cm."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v)
g = np.load('work/groups.npz'); W = g['W']; names = [str(x) for x in g['names']]
col = lambda pred: W[:, [i for i, nm in enumerate(names) if pred(nm)]].sum(1)
bones = {'head': col(lambda s: s in ('B_Head', 'B_Neck')), 'hand': col(lambda s: s.endswith('_Hand') or 'Finger' in s),
         'fore': col(lambda s: 'Forearm' in s), 'string': col(lambda s: s in ('Bow', 'StringNock')),
         'spine2': col(lambda s: s == 'B_Spine2'), 'foot': col(lambda s: 'Foot' in s or 'Toe' in s),
         'calf': col(lambda s: 'Calf' in s), 'thigh': col(lambda s: 'Thigh' in s)}
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
reg = np.zeros(len(f), int)
for p in np.flatnonzero(sizes):
    m = fl == p; vs = np.unique(f[m]); s = sizes[p]; cp = v[vs].mean(0)
    w = {k: float(b[vs].mean()) for k, b in bones.items()}
    if w['string'] > .9:
        r = 12
    elif s > 2000:
        r = 1
    elif w['hand'] > .4:
        r = 6
    elif w['head'] > .95:
        r = 2 if s > 400 else (3 if cp[1] < -0.05 else 15)
    elif w['spine2'] > .95:
        r = 8 if s > 200 else 9
    elif w['fore'] > .5:
        r = 7
    elif w['foot'] > .4:
        r = 11
    elif s > 600:
        r = 4
    elif s > 400:
        r = 5
    elif s > 200:
        r = 10
    elif cp[2] > 0.6:
        r = 13
    else:
        r = 14
    reg[m] = r
soles = (reg == 11) & (c[:, 2] < 0.06)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles)
NAMES = {1: 'head', 2: 'hair', 3: 'eyes', 4: 'vest', 5: 'trousers', 6: 'hands', 7: 'forearms', 8: 'quiver',
         9: 'arrows', 10: 'straps', 11: 'feet', 12: 'string', 13: 'pouches', 14: 'lacing', 15: 'hair tie'}
print({NAMES[k]: int((reg == k).sum()) for k in NAMES}, 'unlabelled', int((reg == 0).sum()), 'soles', int(soles.sum()))
