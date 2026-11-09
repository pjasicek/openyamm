#!/usr/bin/env python3
"""Keep the source faces within R metres (rest pose) of the given source vertices (probe_err.py "src" indices = dump
order) on top of a keep mask. Usage: vert_lock.py <base keep .npy> <out .npy> <R> <i,j,...>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
base, out, R, ids = sys.argv[1], sys.argv[2], float(sys.argv[3]), [int(x) for x in sys.argv[4].split(',')]
m = np.load('work/mesh_in.npz'); v, f = m['verts'], m['faces']
keep = np.load(base).copy(); n0 = int(keep.sum())
d, _ = cKDTree(v[ids]).query(v); keep |= (d < R)[f].any(1)
np.save(out, keep); print('VERTLOCK', len(ids), 'vertices, R', R, 'kept', n0, '->', int(keep.sum()))
for i in ids:
    print(' ', i, np.round(v[i], 3))
