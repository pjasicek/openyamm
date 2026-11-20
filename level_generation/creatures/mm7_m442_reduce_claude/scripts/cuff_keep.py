#!/usr/bin/env python3
"""m410: keep the forearm skin around the wrist band and the gold bangles (piece 10): torso-shell faces with a vertex
within REA_CUFF_R (default 0.03 m) of a band vertex. The collapse there pulled band colour onto the forearm (a dark
wedge above the right band at 76 %; after a drift lock a gold streak above the left bangles).
Usage: cuff_keep.py <base keep .npy> <out .npy>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; p = np.load('work/pieces.npy')
dist, _ = cKDTree(v[np.unique(f[p == 10])]).query(v)
near = dist < float(os.environ.get('REA_CUFF_R', '0.03'))
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= (p == 1) & near[f].any(1)
np.save(sys.argv[2], keep); print('CUFF keep', n0, '->', int(keep.sum()))
