#!/usr/bin/env python3
"""Keep the source faces within REA_LOCK_R (default 0.03 m) of named reduced faces exactly in the next ladder (a visible
defect the automatic checks miss; MM8 Nightmare: face 7508 of r55 reached over its chart border onto mouth-red texels).
Usage: lock_faces.py <base keep .npy> <out .npy> <tag> <face,...>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
base, out, tag, ids = sys.argv[1], sys.argv[2], sys.argv[3], [int(i) for i in sys.argv[4].split(',')]
R = float(os.environ.get('REA_LOCK_R', '0.03'))
s = np.load('work/mesh_in.npz'); tree = cKDTree(s['verts'][s['faces']].mean(1))
keep = np.load(base).copy(); n0 = int(keep.sum()); d = np.load(f'work/mesh_{tag}.npz')
for i in ids:
    tri = d['verts'][d['faces'][i]]
    for p in [*tri, tri.mean(0)]:
        keep[tree.query_ball_point(p, R)] = True
np.save(out, keep); print('LOCK', n0, '->', int(keep.sum()), 'faces kept')
