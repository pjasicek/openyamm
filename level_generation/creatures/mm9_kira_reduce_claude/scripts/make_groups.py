#!/usr/bin/env python3
"""Kira: exact-keep mask and per-region groups for decimate_tex.py (work/keep.npy, work/groups.npy) from work/faces_info.npz.
Kept exactly (REDUCTION_BRIEF_20261104 "faces are untouchable" and "keep exactly what fixes and gates depend on"):
  hands and fingers (part 0: MPFB graft, r8 smooth finger cut, glove stub inside the vambrace), face and neck skin (20: r8 jaw
  rigidity, chin fold, UV slivers), eyes (22), braid (23, built tube on Yp*), the vambraces within WRIST_R of the hand (rim caps,
  inner wall, sleeve-tuck zone: wrist_fill.py and the sleeve gate), pieces of up to SMALL faces (belt buckle, the two smallest
  pauldron lames) and the soles (all corners within SOLE_Z of the floor).
Groups (own ratios through REA_GROUP_RATIOS): 1 hair (21), 2 mail skirt (7, on six hinges), 3 belt, medallion, knee cops, pauldron
lames, tasset (9-13); 0 = armour shell and legs (the ladder budget)."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
WRIST_R = float(os.environ.get('WRIST_R', '0.04')); SMALL = int(os.environ.get('SMALL', '80')); SOLE_Z = float(os.environ.get('SOLE_Z', '0.03'))
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']; part = info['part']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; small = np.bincount(pc)[pc] <= SMALL
cen = v[f].mean(1)
dd, _ = cKDTree(v[np.unique(f[part == 0])]).query(cen); wrist = (dd < WRIST_R) & (part == 1)
sole = v[f][:, :, 2].max(1) < v[:, 2].min() + SOLE_Z
keep = np.isin(part, [0, 20, 22, 23]) | wrist | small | sole
g = np.zeros(len(f), int); g[part == 21] = 1; g[part == 7] = 2; g[np.isin(part, [9, 10, 11, 12, 13])] = 3
g[keep] = 0
np.save('work/keep.npy', keep); np.save('work/groups.npy', g)
print('KEEP', int(keep.sum()), {'hands': int((part == 0).sum()), 'face': int((part == 20).sum()), 'eyes': int((part == 22).sum()),
      'braid': int((part == 23).sum()), 'wrist': int(wrist.sum()), 'small': int((small & ~np.isin(part, [0, 20, 22, 23])).sum()),
      'soles': int(sole.sum())})
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(4)})
