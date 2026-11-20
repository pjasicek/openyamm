#!/usr/bin/env python3
"""Keep the source faces within R metres (rest pose) of given points exactly: spots found in close-ups that the
averaged checks miss (a dark slash on the neck skin at a head-atlas chart border).
Usage: spot_lock.py <base keep .npy> <out .npy> <R> x,y,z [x,y,z ...]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); c = d['verts'][d['faces']].mean(1)
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); R = float(sys.argv[3]); t = cKDTree(c)
for p in sys.argv[4:]:
    keep[t.query_ball_point([float(x) for x in p.split(',')], R)] = True
np.save(sys.argv[2], keep); print('SPOTLOCK', n0, '->', int(keep.sum()))
