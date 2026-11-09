#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Peasant Human1 Female (faces -y, 1.70 m). Pieces from the production master (face_piece.py; mm7_m342_claude
creature.json): 0 skin shell (head, neck, shoulders, blouse sleeves), 1 bodice + green skirt (skirt on the 14 x 4 robe
chains below the waist), 2 white petticoat (robe chains), 3 legs + shoes (on the leg bones under the skirt), 4/5 hands
(fitted fingers), 7 dagger + scabbard, 10 belt, 15/16 eyes, 46-48 buckle, hair strands (31 pieces), lashes/mouth bits.
Labels: 1 head skin above the neck cut (1.43 m), 2 shoulders + blouse, 4 hair strands over KEEP_N faces, 5 green skirt
(below the waist, 0.95 m), 6 bodice, 7 petticoat, 8 hidden legs above the shoes, 9 dagger, 10 belt.
Kept exactly: pieces of up to KEEP_N faces (small hair locks, lashes, mouth bits, buckle), both hands and forearms
(fitted fingers), the eyes, the face front (head skin within 7 cm of the face centre, front half), the shoes (legs piece
below 15 cm), the petticoat hem band (below 12 cm) and the green skirt's hem band (below 25 cm)."""
import os
import numpy as np
KEEP_N = int(os.environ.get('KEEP_N', '80'))
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
fp = np.load('work/face_piece.npy'); size = np.bincount(fp)[fp]
MOUTH = [21, 23, 29, 38, 39, 41, 43, 49, 51, 52, 54]                 # lashes, lips, teeth: kept
HAIR = [6, 8, 9, 11, 12, 13, 14, 17, 18, 19, 20, 22, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 40, 42, 44, 45, 50, 53]
g = np.zeros(len(f), int)
sk = fp == 0
g[sk & (c[:, 2] > 1.43)] = 1; g[sk & (c[:, 2] <= 1.43)] = 2
g[np.isin(fp, HAIR)] = 4
g[(fp == 1) & (c[:, 2] < .95)] = 5; g[(fp == 1) & (c[:, 2] >= .95)] = 6
g[fp == 2] = 7; g[(fp == 3) & (c[:, 2] >= .15)] = 8; g[fp == 7] = 9; g[fp == 10] = 10
FACE = np.array([0.0, -0.09, 1.55])
face_front = sk & (np.linalg.norm(c - FACE, axis=1) < 0.07) & (c[:, 1] < -0.03)
keep = ((size <= KEEP_N) | np.isin(fp, [4, 5, 15, 16]) | face_front | ((fp == 3) & (c[:, 2] < .15))
        | ((fp == 2) & (c[:, 2] < .12)) | ((fp == 1) & (c[:, 2] < .25)) | np.isin(fp, MOUTH))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(11)}, 'keep', int(keep.sum()), 'face front', int(face_front.sum()))
