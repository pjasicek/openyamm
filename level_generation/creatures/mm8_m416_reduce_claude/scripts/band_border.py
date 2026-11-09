#!/usr/bin/env python3
"""Faces of the head skin (with its scalp cap) and of the bandanna within REA_BORDER_R (default 1.2 cm) of the other
piece, kept exactly so the bandanna rim and the hairline do not move (the sibling Pirate Warrior's right-temple hole).
Usage: band_border.py <base keep .npy> <out .npy>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npy'); v, f = d['verts'], d['faces']
R = float(os.environ.get('REA_BORDER_R', '0.012'))
cap = np.arange(len(f)) >= len(np.load('work/faces_info.npz')['dom'])
skin, band = np.isin(g, [1, 2]) | cap, g == 3
near = lambda a, b: (cKDTree(v[np.unique(f[b])]).query(v)[0] < R)[f].any(1) & a
border = near(skin, band) | near(band, skin)
keep = np.load(sys.argv[1]); n0 = int(keep.sum()); np.save('work/band_border.npy', border); keep = keep | border
np.save(sys.argv[2], keep); print('BORDER', int(border.sum()), 'faces (skin', int((border & skin).sum()), 'bandanna',
                                    int((border & band).sum()), '); keep', n0, '->', int(keep.sum()))
