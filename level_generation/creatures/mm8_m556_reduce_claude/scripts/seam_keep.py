#!/usr/bin/env python3
"""Faces kept exactly around every coincident vertex pair with other weights (Bone Dragon: wing finger tips, tail
tip, ribs; import_source.py reports 49 such vertices): every face with a vertex within REA_SEAM_R (default 0.01 m)
of one. Collapses there otherwise build faces across the split. Usage: seam_keep.py <base keep .npy or -> <out .npy>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']
keep = np.zeros(len(f), bool) if sys.argv[1] == '-' else np.load(sys.argv[1]).copy(); n0 = int(keep.sum())
seam = np.unique(cKDTree(v).query_pairs(1e-6, output_type='ndarray'))
near = cKDTree(v[seam]).query(v)[0] < float(os.environ.get('REA_SEAM_R', '0.01'))
keep |= near[f].any(1)
np.save(sys.argv[2], keep); print('SEAM vertices', len(seam), 'kept faces', n0, '->', int(keep.sum()))
