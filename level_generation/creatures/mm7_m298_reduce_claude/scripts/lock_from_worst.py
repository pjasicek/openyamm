#!/usr/bin/env python3
"""err_lock.py's lock step from its saved per-vertex worst error (work/worst_<cand>.npy), for other thresholds without
re-running the clips. Usage: lock_from_worst.py <worst .npy> <base keep .npy> <out .npy> <mm> <radius m>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
worst = np.load(sys.argv[1]); keep = np.load(sys.argv[2]).copy(); T = float(sys.argv[4]) / 1000; R = float(sys.argv[5])
m = np.load('work/mesh_in.npz'); rest, faces = m['verts'], m['faces']; bad = np.flatnonzero(worst > T); n0 = int(keep.sum())
if len(bad):
    near = cKDTree(rest[bad]).query(rest)[0] < R
    keep |= near[faces].any(1)
np.save(sys.argv[3], keep); print('LOCK', len(bad), 'vertices over', T * 1000, 'mm; kept', n0, '->', int(keep.sum()))
