#!/usr/bin/env python3
"""Per-face source shell (work/source_pieces.npz from source_pieces.py, mapped by nearest rest position) of the m190 rest
mesh (work/mesh_in.npz) -> work/pieces.npy (source 'piece' id, majority of the face's vertices), work/garment_v.npy and
work/piece_v.npy (per vertex), work/soles.npy (boot faces below 6 cm).
Source shells: 0 torso/head/beard/hair/collar, 1/2 boots, 3 ragged skirt, 4/5 hands, 6 legs, 7 mail skirt, 8 helmet,
9/10 braids, 11/12 bracers, 13/14 shoulder guards, 15/16 bare upper arms, 17/18 horns, 19/20 guard rims, 21/22 braid ends,
23 buckle, 24/25 eyes."""
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; s = np.load('work/source_pieces.npz')
dist, i = cKDTree(s['co']).query(v)
pv, gv = s['piece'][i], s['garment'][i]
fp = np.array([np.bincount(x, minlength=26).argmax() for x in pv[f]])
mixed = int((pv[f] != fp[:, None]).any(1).sum())
soles = np.isin(fp, (1, 2)) & (v[f].mean(1)[:, 2] < 0.06)
np.save('work/pieces.npy', fp); np.save('work/piece_v.npy', pv); np.save('work/garment_v.npy', gv); np.save('work/soles.npy', soles)
print('MAP max dist mm', round(float(dist.max()) * 1000, 4), 'mixed faces', mixed, 'soles', int(soles.sum()))
c = v[f].mean(1)
for p in range(26):
    m = fp == p
    print(f'  piece {p:2d} faces {int(m.sum()):5d} centre {np.round(c[m].mean(0), 3)} zmax {v[f[m]][..., 2].max():.3f}')
