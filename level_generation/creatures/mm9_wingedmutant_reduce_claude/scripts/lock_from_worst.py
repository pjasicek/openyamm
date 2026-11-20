#!/usr/bin/env python3
"""Error lock from a saved worst-over-clips map (err_lock.py's work/worst_<cand>.npy, per source vertex): faces with a
vertex within R m (rest) of a source vertex missed by more than T mm, mirrored to both sides.
Usage: lock_from_worst.py <worst .npy> <T mm> <R m> <out .npy> [only group g]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
w = np.load(sys.argv[1]); T, R, out = float(sys.argv[2]) / 1000, float(sys.argv[3]), sys.argv[4]
s = np.load('work/mesh_in.npz'); v, f = s['verts'], s['faces']; S = np.load('work/sets.npz')
bad = np.flatnonzero(w > T); pts = np.vstack([v[bad], v[bad] * [-1, 1, 1]])
d, _ = cKDTree(pts).query(v); lock = (d < R)[f].any(1) & ~S['back']
if len(sys.argv) > 5:
    lock &= S['group'] == int(sys.argv[5])
np.save(out, lock); print('LOCK', len(bad), 'vertices over', T * 1000, 'mm ->', int(lock.sum()), 'faces,', int((lock & ~S['keep']).sum()), 'not yet kept')
