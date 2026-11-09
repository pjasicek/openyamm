#!/usr/bin/env python3
"""Keep the source faces within R metres (rest pose) of given points exactly (spots a close-up found: a fold that
showed the body's inside). Usage: spot_lock.py <base keep .npy> <out .npy> <R> x,y,z [x,y,z ...]"""
import sys
import numpy as np
m = np.load('work/mesh_in.npz'); c = m['verts'][m['faces']].mean(1)
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); R = float(sys.argv[3])
for p in sys.argv[4:]:
    keep |= np.linalg.norm(c - np.array([float(x) for x in p.split(',')]), axis=1) < R
np.save(sys.argv[2], keep); print('SPOTLOCK kept', n0, '->', int(keep.sum()))
