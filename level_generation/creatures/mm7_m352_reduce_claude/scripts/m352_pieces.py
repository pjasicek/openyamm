#!/usr/bin/env python3
"""Per-face source shell (work/source_pieces.npz from source_pieces.py, mapped by nearest rest position) of the m352 rest
mesh (work/mesh_in.npz) -> work/pieces.npy (source 'piece' id, majority of the face's vertices), work/garment_v.npy and
work/piece_v.npy (per vertex), work/soles.npy (shoe faces below 6 cm).
Source shells (mm7_m352_claude step1_clean.py): 0 tunic with the belt, 1 trouser legs, 2 head + neck, 3/4 hands with the
forearms inside the sleeves (right/left), 5 long hair, 6/7 shoes, 8 buckle, 9 hanging strap end, 10/11 eyes, 12..68 brass
studs (neckline, cuffs, belt)."""
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; s = np.load('work/source_pieces.npz')
dist, i = cKDTree(s['co']).query(v)
pv, gv = s['piece'][i], s['garment'][i]
fp = np.array([np.bincount(x, minlength=70).argmax() for x in pv[f]])
mixed = int((pv[f] != fp[:, None]).any(1).sum())
soles = np.isin(fp, (6, 7)) & (v[f].mean(1)[:, 2] < 0.06)
np.save('work/pieces.npy', fp); np.save('work/piece_v.npy', pv); np.save('work/garment_v.npy', gv); np.save('work/soles.npy', soles)
print('MAP max dist mm', round(float(dist.max()) * 1000, 4), 'mixed faces', mixed, 'soles', int(soles.sum()))
c = v[f].mean(1)
for p in range(70):
    m = fp == p
    if not m.any(): continue
    print(f'  piece {p:2d} faces {int(m.sum()):5d} centre {np.round(c[m].mean(0), 3)} zmax {v[f[m]][..., 2].max():.3f}')
