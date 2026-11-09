#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep masks.
Hesper Landfall villager, male (hvm, faces -y, 1.70 m rest, 9,450 welded triangles in one HVM_A atlas: body set
u < 0.5, head set u > 0.5). Pieces: coat with belt (2,195), head + neck (1,696), two five-fingered hands (~990 each),
trousers (684), pouch (250), shoes (~225), eyes, ~100 short hair cards (head set, 20-110 faces), the pin and the gold
clasps (28-80 faces).
Labels: 0 trousers and the rest; 1 head piece outside the face front (scalp under the hair, ears, neck); 2 hands;
3 shoes; 4 hair cards (small head-set pieces other than the eyes); 5 coat; 6 pouch; 7 face front (head piece in front
of FRONT_Y between FRONT_ZMIN and FRONT_ZMAX: brows, eyes, nose, mouth, chin).
work/keep_small.npy: body-set pieces of up to SMALL faces (pin, clasps), the eyes, and the SOLES (all three vertices
within SOLE_Z of the rest floor). work/keep_front.npy: keep_small + face front."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SOLE_Z = float(os.environ.get('SOLE_Z', '0.03'))
SMALL = int(os.environ.get('SMALL', '90'))
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
    if sizes[p] > 1500 and frac(p, 'Head') > .9:
        g[m] = 1                                           # head piece
    elif sizes[p] > 1500:
        g[m] = 5                                           # coat
    elif sizes[p] > 500 and (frac(p, 'Hand') + frac(p, 'Finger')) > .5:
        g[m] = 2
    elif 150 < sizes[p] < 400 and (frac(p, 'Foot') + frac(p, 'Toe')) > .5:
        g[m] = 3
    elif 150 < sizes[p] < 400:
        g[m] = 6
    elif sizes[p] <= 150 and pu[p] > .5:
        eye = (v[f[m]].reshape(-1, 3).max(0) - v[f[m]].reshape(-1, 3).min(0)).max() < .035
        if eye:
            small[m] = True
        else:
            g[m] = 4
    elif sizes[p] <= SMALL:
        small[m] = True
front = (g == 1) & (cen[:, 1] < FRONT_Y) & (cen[:, 2] > FRONT_ZMIN) & (cen[:, 2] < FRONT_ZMAX)
g[front] = 7
z = v[:, 2]; zmin = z.min()
soles = (z[f] < zmin + SOLE_Z).all(1) & (g == 3)
np.save('work/groups.npy', g); np.save('work/keep_small.npy', small | soles); np.save('work/keep_soles.npy', soles)
np.save('work/keep_front.npy', small | soles | front)
print('GROUPS', {k: int(((g == k) & ~small).sum()) for k in range(8)}, 'small kept', int(small.sum()),
      'sole faces kept', int(soles.sum()), 'face front', int(front.sum()))
