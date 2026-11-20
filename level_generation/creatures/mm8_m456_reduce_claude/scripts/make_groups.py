#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy),
MM8 Dragon Hunter (m456). Blender rest pose, z up, front is -y. Pieces are found by size and position (the source has
34 connected pieces): head skin (largest head-set piece under the helmet), helmet cap and crest pieces (head set,
reaching above 1.5 m), the cuirass (largest B_Spine2 piece), the two sleeves (pieces mixing B_Spine2 and an upper
arm: the 2026-10-16 shoulder repair made each one continuous from a root under the cuirass to the forearm), the two
pauldrons, both hands.
Labels: 0 rest (legs, fauld, cuirass, bracers, knee guards, sleeves outside the cuirass), 1 face (head skin, front,
above FACE_Z), 2 rest of the head skin (neck, back of the head under the helmet), 3 helmet cap and crest, 4 right
(free) hand, 5 the knee band of the two leg pieces (KNEE_LO..KNEE_HI m; the production LOD build restores knee
rows so the reduced meshes bend instead of bridging the knee with one large flat triangle, check_knees.py), 6 the two
knee guards (rigid calf pieces, rounded).
Kept exactly: the sword (left) hand and fingers, so the fitted grip does not change; small pieces of up to REA_SMALL
faces (eyes, cheek and nose guards, buckles, rivets, strap ends); the plume (the thin head-set piece reaching the
top, PLUME_Z: decimation smoothed its jagged feather outline); both pauldrons (rigid hinge pieces, 200 faces
each); the sleeves' roots under the cuirass (|x| < ROOT_X, above ROOT_Z: the repair's attachment, checked by
check_shoulders.py); faces of the cuirass, sleeves and pauldrons within BORDER of the cuirass or pauldron open rims;
the soles (faces below 6 cm)."""
import os

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom']; head = info['u'] > 1056 / 2080
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; cnt = np.bincount(pc); size = cnt[pc]
big = np.argsort(-cnt)
SMALL = int(os.environ.get('REA_SMALL', '130'))
share = lambda p, test: np.mean([test(x) for x in dom[pc == p]])
skin_p = next(p for p in big if head[pc == p].mean() > .9)
helmet = [p for p in big if cnt[p] > SMALL and p != skin_p and head[pc == p].mean() > .9 and c[pc == p, 2].max() > 1.5]
cuirass_p = next(p for p in big if share(p, lambda x: x == 'B_Spine2') > .95)
sleeves = [p for p in big if cnt[p] > SMALL and .3 < share(p, lambda x: x == 'B_Spine2') < .9
           and share(p, lambda x: 'UpperArm' in x) > .1]
pauldrons = [p for p in big if share(p, lambda x: 'Pauldron' in x) > .9]
g = np.zeros(len(f), int)
skin = pc == skin_p
FACE_Y, FACE_Z = float(os.environ.get('FACE_Y', '-0.09')), float(os.environ.get('FACE_Z', '1.39'))
face = skin & (c[:, 1] < FACE_Y) & (c[:, 2] > FACE_Z)
g[skin & ~face] = 2; g[face] = 1; g[np.isin(pc, helmet)] = 3
is_hand = lambda side: np.array([x == f'B_{side}_Hand' or x.startswith(f'B_{side}_Finger') for x in dom])
g[is_hand('R') & (size > 1000)] = 4
legs = [p for p in big[:4] if share(p, lambda x: x.endswith(('Thigh', 'Calf', 'Foot', 'Pelvis'))) > .9]
KNEE_LO, KNEE_HI = float(os.environ.get('KNEE_LO', '0.40')), float(os.environ.get('KNEE_HI', '0.62'))
g[np.isin(pc, legs) & (v[f][..., 2].max(1) > KNEE_LO) & (v[f][..., 2].min(1) < KNEE_HI)] = 5
guards = [p for p in big if cnt[p] > SMALL and share(p, lambda x: x.endswith('Calf')) > .95 and .4 < c[pc == p, 2].mean() < .6]
g[np.isin(pc, guards)] = 6
fist = is_hand('L')
small = size <= SMALL
sole = c[:, 2] < .06
ROOT_X, ROOT_Z = float(os.environ.get('ROOT_X', '0.16')), float(os.environ.get('ROOT_Z', '1.1'))
root = np.isin(pc, sleeves) & (np.abs(c[:, 0]) < ROOT_X) & (c[:, 2] > ROOT_Z)


def rim(p):
    ff = f[pc == p]; ee = np.sort(np.concatenate([ff[:, [0, 1]], ff[:, [1, 2]], ff[:, [2, 0]]]), 1)
    u, k = np.unique(ee, axis=0, return_counts=True); return np.unique(u[k == 1])


BORDER = float(os.environ.get('BORDER', '0.012'))
rims = cKDTree(v[np.concatenate([rim(p) for p in [cuirass_p, *pauldrons]])])
armour = np.isin(pc, [cuirass_p, *sleeves, *pauldrons])
border = armour & (rims.query(v[f])[0].min(1) < BORDER)
PLUME_Z = float(os.environ.get('PLUME_Z', '1.65'))
plume = [p for p in helmet if v[f[pc == p]][..., 2].max() > PLUME_Z and np.ptp(c[pc == p, 0]) < .06]
keep = fist | small | sole | root | border | np.isin(pc, pauldrons) | np.isin(pc, plume)
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('PIECES legs', legs, 'guards', guards, 'skin', skin_p, 'helmet', helmet, 'plume', plume, 'cuirass', cuirass_p, 'sleeves', sleeves, 'pauldrons', pauldrons)
print('GROUPS', {k: int((g == k).sum()) for k in range(7)}, 'keep', int(keep.sum()), 'fist', int(fist.sum()),
      'small', int(small.sum()), 'sole', int(sole.sum()), 'root', int(root.sum()), 'border', int(border.sum()),
      'decimated', int((~keep).sum()))
