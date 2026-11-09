#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep masks.
Hesper Landfall villager, female (hvf, faces -y, 1.70 m rest, 10,468 triangles in one HVF_A atlas: body set u < 0.5,
head set u > 0.5). Pieces: head + neck (3,519: kept whole by the source project's own reduction), coat-dress with
sleeves (3,451, skirt on robe chains), trousers (587), bun (517), hands (~440), bag (240), sash tail (200), strap (150),
boots (~140), eyes, fringe, earrings, buttons and clips (14-96 faces).
Labels: 0 trousers and the rest; 1 head piece outside the face front (scalp under the hair, ears, neck); 2 hands;
3 boots; 4 bun and fringe (head-set hair pieces); 5 coat-dress; 6 bag, strap and sash tail; 7 face front (head piece in
front of FRONT_Y between FRONT_ZMIN and FRONT_ZMAX).
work/keep_small.npy: pieces of up to SMALL faces (buttons, clips, earrings, eyes) and the SOLES (all three vertices
within SOLE_Z of the rest floor). work/keep_front.npy: keep_small + face front."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SOLE_Z = float(os.environ.get('SOLE_Z', '0.03'))
SMALL = int(os.environ.get('SMALL', '100'))
FRONT_Y = float(os.environ.get('FRONT_Y', '-0.04'))
FRONT_ZMIN = float(os.environ.get('FRONT_ZMIN', '1.45'))
FRONT_ZMAX = float(os.environ.get('FRONT_ZMAX', '1.63'))
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc)
dom = info['dom'].astype(str)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
cen = v[f].mean(1)
pu = np.array([u[pc == p].mean() if sizes[p] else 0 for p in range(len(sizes))])
frac = lambda p, key: (np.char.find(dom[pc == p], key) >= 0).mean()
g = np.zeros(len(f), int); small = np.zeros(len(f), bool)
for p in np.unique(pc):
    m = pc == p
    if sizes[p] <= SMALL:
        small[m] = True
    elif sizes[p] > 1500 and frac(p, 'Head') > .9:
        g[m] = 1                                           # head piece
    elif sizes[p] > 1500:
        g[m] = 5                                           # coat-dress
    elif pu[p] > .5:
        g[m] = 4                                           # bun, fringe
    elif (frac(p, 'Hand') + frac(p, 'Finger') + frac(p, 'ForearmTwist')) > .5:
        g[m] = 2
    elif (frac(p, 'Foot') + frac(p, 'Toe') + frac(p, 'Calf')) > .7:
        g[m] = 3
    elif sizes[p] < 400:
        g[m] = 6                                           # bag, strap, sash tail
front = (g == 1) & (cen[:, 1] < FRONT_Y) & (cen[:, 2] > FRONT_ZMIN) & (cen[:, 2] < FRONT_ZMAX)
g[front] = 7
z = v[:, 2]; zmin = z.min()
soles = (z[f] < zmin + SOLE_Z).all(1) & (g == 3)
np.save('work/groups.npy', g); np.save('work/keep_small.npy', small | soles); np.save('work/keep_soles.npy', soles)
np.save('work/keep_front.npy', small | soles | front)
print('GROUPS', {k: int(((g == k) & ~small).sum()) for k in range(8)}, 'small kept', int(small.sum()),
      'sole faces kept', int(soles.sum()), 'face front', int(front.sum()))
