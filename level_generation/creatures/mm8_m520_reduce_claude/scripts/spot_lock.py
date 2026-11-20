#!/usr/bin/env python3
"""Keep the source faces within R metres of rest-pose spots found by eye (ray-picked in GLB renders).
Usage: spot_lock.py <base keep .npy> <out .npy> <R> x,y,z [x,y,z ...]"""
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); c = d['verts'][d['faces']].mean(1)
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); R = float(sys.argv[3])
for s in sys.argv[4:]:
    keep |= np.linalg.norm(c - np.array([float(x) for x in s.split(',')]), axis=1) < R
np.save(sys.argv[2], keep); print('SPOT', n0, '->', int(keep.sum()), 'faces kept')
