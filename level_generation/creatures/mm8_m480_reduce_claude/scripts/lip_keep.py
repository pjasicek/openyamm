#!/usr/bin/env python3
"""Keep the face pieces and the face skin around the mouth exactly. Troll Peasant (copied from the Troll m476): the
eyes, teeth, gums and tongue are separate pieces of up to 200 faces in front of the face (centre y < -0.11; the
peasant faces -Y), kept whole; faces within REA_LIP_R (default 0.015 m) of the mouth pieces (those below the eyes,
z < 1.40) are kept too. Usage: lip_keep.py <base keep> <out>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; piece = np.load('work/piece.npy'); sizes = np.bincount(piece)
c = v[f].mean(1); pc = np.array([c[piece == k].mean(0) if sizes[k] else np.zeros(3) for k in range(len(sizes))])
front = (sizes[piece] <= 200) & (pc[piece, 1] < -.11)
mouth = front & (pc[piece, 2] < 1.40)
pts = v[np.unique(f[mouth])]
near = cKDTree(pts).query(v)[0] < float(os.environ.get('REA_LIP_R', '0.015'))
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= front | near[f].any(1)
np.save(sys.argv[2], keep); print('LIPS face pieces', int(front.sum()), 'mouth faces', int(mouth.sum()), 'kept', n0, '->', int(keep.sum()))
