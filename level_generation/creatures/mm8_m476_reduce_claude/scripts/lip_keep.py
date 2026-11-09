#!/usr/bin/env python3
"""Keep the face skin around the mouth exactly: faces within REA_LIP_R (default 0.015 m) of the mouth and teeth
pieces (small head pieces in front of the face below the eyes: y < -0.18, z < 1.46). Usage: lip_keep.py <base keep> <out>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; piece = np.load('work/piece.npy'); sizes = np.bincount(piece)
c = v[f].mean(1); small = sizes[piece] <= 160
mouth = small & (c[:, 1] < -.18) & (c[:, 2] < 1.46)
pts = v[np.unique(f[mouth])]
near = cKDTree(pts).query(v)[0] < float(os.environ.get('REA_LIP_R', '0.015'))
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= near[f].any(1)
np.save(sys.argv[2], keep); print('LIPS mouth/teeth faces', int(mouth.sum()), 'kept', n0, '->', int(keep.sum()))
