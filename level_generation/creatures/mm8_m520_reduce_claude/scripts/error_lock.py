#!/usr/bin/env python3
"""Keep the source faces within REA_LOCK_R (default 0.04 m) of source vertices whose worst animated error
(region_err.py, work/worst_<cand>.npy) exceeds REA_LOCK_MM (default 20). Usage: error_lock.py <base keep .npy> <out .npy> <cand>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
base, out, cand = sys.argv[1:4]
d = np.load('work/mesh_in.npz'); worst = np.load(f'work/worst_{cand}.npy')
keep = np.load(base).copy(); n0 = int(keep.sum())
bad = d['verts'][worst > float(os.environ.get('REA_LOCK_MM', '20')) / 1000]
near = cKDTree(bad).query(d['verts'])[0] < float(os.environ.get('REA_LOCK_R', '0.04')) if len(bad) else np.zeros(len(d['verts']), bool)
keep |= near[d['faces']].any(1)
np.save(out, keep); print('LOCK', len(bad), 'vertices over the limit; kept faces', n0, '->', int(keep.sum()))
