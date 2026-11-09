#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Peasant Human2 Female (faces -y, 1.7 m chain units). Pieces from the production master (face_piece.py): 0 gown
(bodice, bell sleeves and skirt in one shell; split by face_bones.py into skirt on the 14 x 4 robe chains, sleeves on
the Sleeve_ chains / arm bones, bodice), 1 head (face, neck), 2/3 hands, 4 veil, 5/6 lower legs + shoes, 7 belt,
8 hanging cord, 9 headband, 10/11 eyes, 12-45 belt fittings, brows/lashes and beads. Labels: 1 head, 2 veil, 3 hands,
4 headband, 5 skirt, 6 bodice, 7 legs above the shoes, 8 cord, 9 belt, 10 bell sleeves. Kept exactly: pieces of up to
250 faces (eyes, brows, belt fittings, beads), the shoes (legs below 15 cm) and the skirt hem band (below 12 cm)."""
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
fp = np.load('work/face_piece.npy'); fb = np.load('work/face_bone.npy'); size = np.bincount(fp)[fp]
g = np.zeros(len(f), int)
for piece, lab in ((1, 1), (4, 2), (2, 3), (3, 3), (9, 4), (5, 7), (6, 7), (8, 8), (7, 9)):
    g[fp == piece] = lab
gown = fp == 0
g[gown & (fb == 1)] = 5; g[gown & (fb == 2)] = 10; g[gown & (fb == 0)] = 6
keep = (size <= 250) | (np.isin(fp, [5, 6]) & (c[:, 2] < .15)) | ((g == 5) & (c[:, 2] < .12))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(11)}, 'keep', int(keep.sum()))
