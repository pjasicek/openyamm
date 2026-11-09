#!/usr/bin/env python3
"""Crystal Dragon per-region budgets for decimate_tex.py (REA_GROUPS / REA_KEEP_FACES).
Keep exactly: small pieces (<= 130 faces: the two amber eyes, a stray face), the lip line (faces touching a vertex
shared by Head- and Jaw-dominated faces, plus one ring around it) and faces on the open mouth/neck borders.
Group 1: the rest of the head and crown (Head-dominated; 3,505 of 7,570 faces, the codex build protected its density),
group 2: the rest of the jaw, 0: body, legs and tail (already lean).
-> work/groups.npy, work/keep.npy"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
fb = np.load('work/face_bones.npz'); names = [str(n) for n in fb['names']]; dom = fb['dom']
bone = np.array([names[i] for i in dom])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
keep = sizes[fl] <= 130
head, jaw = bone == 'Head', bone == 'Jaw'
seam_v = np.intersect1d(np.unique(f[head]), np.unique(f[jaw]))
lip = np.isin(f, seam_v).any(1)
ring_v = np.unique(f[lip]); lip |= np.isin(f, ring_v).any(1)
es = np.sort(e, 1); E, inv, cnt = np.unique(es, axis=0, return_inverse=True, return_counts=True)
border = (cnt[inv] == 1).reshape(3, -1).any(0) & (head | jaw | (bone == 'Neck1'))
keep |= lip | border
groups = np.zeros(len(f), int); groups[head & ~keep] = 1; groups[jaw & ~keep] = 2
np.save('work/keep.npy', keep); np.save('work/groups.npy', groups)
print('KEEP', int(keep.sum()), '(small', int((sizes[fl] <= 130).sum()), 'lip', int(lip.sum()), 'border', int(border.sum()), ')',
      'head', int((groups == 1).sum()), 'jaw', int((groups == 2).sum()), 'rest', int((groups == 0).sum() - keep.sum()))
