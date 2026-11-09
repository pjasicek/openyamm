#!/usr/bin/env python3
"""Per-region budgets for the Cyclops (work/mesh_in.npz, work/vweights.npz): keep exactly the small pieces (up to
REA_SMALL faces: neck discs, fangs, arm band) and finger-weighted faces (fitted boulder grip); group 1 = the head
texture set (u > 0.5: face, eye, brow, hair), group 2 = palm/back of hand, group 3 = boots (centre below
REA_BOOT_Z, default 0.72 m). Faces within REA_EYE_R (0.05 m) of the eye (iris at 0, -0.159, 2.241) are kept too: any head cut flattened the upper lid. The loincloth and hip skin (the m520 LOD builder's protected box) are kept exactly:
their jagged tips blunted from 66 %. -> work/keep_regions.npy, work/groups.npy"""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); w = np.load('work/vweights.npz'); f = d['faces']; n = len(d['verts'])
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)[1][f[:, 0]]
small = np.bincount(lab)[lab] <= int(os.environ.get('REA_SMALL', '250'))
finger = w['finger'][f].mean(1) > float(os.environ.get('REA_FINGER_W', '0.3'))
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
head = u > .5
hand = (w['hand'][f].mean(1) > .3) & ~finger
c = d['verts'][f].mean(1)
loin = (np.abs(c[:, 0]) < .5) & (np.abs(c[:, 1]) < .6) & (c[:, 2] > .87) & (c[:, 2] < 1.30)
boot = c[:, 2] < float(os.environ.get('REA_BOOT_Z', '0.72'))
eye = np.linalg.norm(c - np.array([0, -.159, 2.241]), axis=1) < float(os.environ.get('REA_EYE_R', '0.05'))
keep = small | finger | loin | eye
groups = np.where(head & ~keep, 1, np.where(hand & ~keep, 2, np.where(boot & ~keep, 3, 0)))
np.save('work/keep_regions.npy', keep); np.save('work/groups.npy', groups)
print('KEEP small', int(small.sum()), 'eye', int((eye & ~small).sum()), 'finger', int((finger & ~small).sum()), 'total', int(keep.sum()),
      '| head', int((groups == 1).sum()), 'hand', int((groups == 2).sum()), 'boot', int((groups == 3).sum()), 'rest', int((groups == 0).sum()))
