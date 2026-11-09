#!/usr/bin/env python3
"""Faces kept exactly around the split lip seam (MM8 Dragon): every face with a vertex within REA_MOUTH_R (default
0.012 m) of a coincident seam vertex in front of the neck (y < -0.3), plus the upper teeth cones (small pieces in that
box). MeshLab collapses near the mouth corners otherwise build faces across the seam, and the open jaw stretches
them into a box. Usage: mouth_keep.py <base keep .npy or -> <out .npy>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']
keep = np.zeros(len(f), bool) if sys.argv[1] == '-' else np.load(sys.argv[1]).copy(); n0 = int(keep.sum())
pairs = np.unique(cKDTree(v).query_pairs(1e-6, output_type='ndarray'))
seam = pairs[v[pairs, 1] < float(os.environ.get('REA_MOUTH_Y', '-0.3'))]  # Phoenix: -0.17 (beak)
near = cKDTree(v[seam]).query(v)[0] < float(os.environ.get('REA_MOUTH_R', '0.012'))
keep |= near[f].any(1)
c = v[f].mean(1)
teeth = (np.abs(c[:, 0]) < .03) & (c[:, 1] < -.33) & (c[:, 2] > .27) & (c[:, 2] < .3)
small = np.load('work/keep_small.npy')
if os.environ.get('REA_MOUTH_TEETH', '1') == '1':  # dragon's upper teeth cones; the Phoenix has none
    keep |= teeth & small
np.save(sys.argv[2], keep); print('MOUTH seam vertices', len(seam), 'kept faces', n0, '->', int(keep.sum()))
