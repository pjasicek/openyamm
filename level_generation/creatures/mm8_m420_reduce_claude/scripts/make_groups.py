#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy),
MM8 Pirate Mage (m420). Head texture set = u > 0.5 of the merged 2080x1024 atlas; front is -y (Blender rest pose).
Labels: 0 rest (coat, shirt, breeches, stocking, shoe), 1 face skin (head-skin piece, front, above FACE_Z),
2 neck, ears, scalp (rest of the head-skin piece), 3 hair mass, 4 beard pieces (head set, under the mouth),
5 left (open) hand and fingers.
Kept exactly: the staff fist (B_R_Hand / B_R_Finger* dominant faces) so the fitted staff grip does not change, small
pieces of up to REA_SMALL faces (eyes, cuffs, sash, the wooden peg, shoe buckle, brows), the soles (faces below 6 cm)
and the hair/skin border (faces of either piece within BORDER of the other's open rim)."""
import os, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom']; head = info['u'] > .5
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; size = np.bincount(pc)[pc]
big = np.bincount(pc).argsort()[::-1]
g = np.zeros(len(f), int)
# head skin: the largest head-set piece; hair: the head-set piece reaching the top; beard: head-set pieces over 180
# faces below the mouth
skin_p = next(p for p in big if head[pc == p].mean() > .9)
hair_p = next(p for p in big if p != skin_p and head[pc == p].all() and v[f[pc == p]][..., 2].max() > 1.65)
beard = head & (pc != skin_p) & (pc != hair_p) & (size > int(os.environ.get('REA_SMALL', '180'))) & (c[:, 2] < 1.53)
skin = pc == skin_p
FACE_Y, FACE_Z = float(os.environ.get('FACE_Y', '-0.03')), float(os.environ.get('FACE_Z', '1.45'))
face = skin & (c[:, 1] < FACE_Y) & (c[:, 2] > FACE_Z)
g[skin & ~face] = 2; g[face] = 1; g[pc == hair_p] = 3; g[beard] = 4
lhand = np.array([x == 'B_L_Hand' or x.startswith('B_L_Finger') for x in dom]) & (size > 1000)
g[lhand] = 5
fist = np.array([x == 'B_R_Hand' or x.startswith('B_R_Finger') for x in dom])
small = size <= int(os.environ.get('REA_SMALL', '180'))
sole = c[:, 2] < .06


def rim(p):
    ff = f[pc == p]; ee = np.sort(np.concatenate([ff[:, [0, 1]], ff[:, [1, 2]], ff[:, [2, 0]]]), 1)
    u, cnt = np.unique(ee, axis=0, return_counts=True); return np.unique(u[cnt == 1])


BORDER = float(os.environ.get('BORDER', '0.012'))
hair_rim = cKDTree(v[rim(hair_p)])
border = ((pc == hair_p) | skin) & (hair_rim.query(v[f]).__getitem__(0).min(1) < BORDER)
keep = fist | small | sole | border
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('PIECES skin', skin_p, 'hair', hair_p)
print('GROUPS', {k: int((g == k).sum()) for k in range(6)}, 'keep', int(keep.sum()), 'fist', int(fist.sum()),
      'small', int(small.sum()), 'sole', int(sole.sum()), 'border', int(border.sum()),
      'decimated', int((~keep).sum()))
