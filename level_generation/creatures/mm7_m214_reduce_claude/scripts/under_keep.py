#!/usr/bin/env python3
"""Faces of the cut surfaces lying under layered kept pieces: vest, trousers and chest-skin faces (pieces 1, 4, 5)
with a vertex within REA_UNDER_R (default 0.02 m) of a waist strap, pouch, belt bit or calf lacing vertex (pieces 10,
13, 14). A decimated vest pushed through the kept upper strap at the front (e85). Usage: under_keep.py <out .npy>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; p = np.load('work/pieces.npy')
top = np.unique(f[np.isin(p, (10, 13, 14))]); R = float(os.environ.get('REA_UNDER_R', '0.02'))
dist, _ = cKDTree(v[top]).query(v); near = dist < R
keep = np.isin(p, (1, 4, 5)) & near[f].any(1)
np.save(sys.argv[1], keep); print('UNDER kept', int(keep.sum()), {k: int((keep & (p == k)).sum()) for k in (1, 4, 5)})
