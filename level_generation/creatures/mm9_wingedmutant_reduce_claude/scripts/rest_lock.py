#!/usr/bin/env python3
"""Rest-pose error lock (numpy, no Blender): source vertices that the candidate work/mesh_r<tag>.npz misses by more than
T mm at rest (rest_err.py's work/rest_err_<tag>.npy) keep every source face within R m exactly, mirrored to both sides.
Usage: rest_lock.py <tag> <T mm> <R m> <out .npy> [base .npy to OR]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
tag, T, R, out = sys.argv[1], float(sys.argv[2]) / 1000, float(sys.argv[3]), sys.argv[4]
s = np.load('work/mesh_in.npz'); v, f = s['verts'], s['faces']
err = np.load(f'work/rest_err_{tag}.npy')
bad = np.flatnonzero(err > T)
pts = np.vstack([v[bad], v[bad] * [-1, 1, 1]]) if len(bad) else np.zeros((0, 3))
near = np.zeros(len(v), bool)
if len(pts):
    d, _ = cKDTree(pts).query(v); near = d < R
keep = near[f].any(1)
if len(sys.argv) > 5:
    keep |= np.load(sys.argv[5])
np.save(out, keep); print('RESTLOCK', len(bad), 'vertices over', T * 1000, 'mm ->', int(keep.sum()), 'faces locked')
