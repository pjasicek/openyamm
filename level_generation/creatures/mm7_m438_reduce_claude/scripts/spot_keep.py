#!/usr/bin/env python3
"""Keep the source faces within R metres (rest pose) of given points exactly (probe_err.py's failing source vertices,
playbook: a single failing point fixed by a 4 cm patch). Usage: spot_keep.py <in keep .npy> <out keep .npy> <R> <vertex id,...>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
src, out, R, ids = sys.argv[1], sys.argv[2], float(sys.argv[3]), [int(x) for x in sys.argv[4].split(',')]
d = np.load('work/mesh_in.npz'); cen = d['verts'][d['faces']].mean(1); keep = np.load(src).copy(); n0 = int(keep.sum())
for i in ids:
    keep[cKDTree(cen).query_ball_point(d['verts'][i], R)] = True
np.save(out, keep); print('SPOTKEEP', n0, '->', int(keep.sum()))
