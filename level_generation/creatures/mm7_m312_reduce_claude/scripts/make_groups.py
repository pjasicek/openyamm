#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Peasant Dwarf Female (faces -y, 1.7 m chain units). Pieces from the production master (face_piece.py): 0 bodice +
sleeves, 1 head (face, neck, chest), 2 skirt (12 x 4 robe chains), 3 legs + shoes, 4 bun, 5/6 hands, 7/8 ringlets,
9 apron bow, 10/18-24 lacing, 11 apron, 12 bow tails, 13/14 cuff ruffles, 15/16 earrings, 17 pocket, 20/21 eyes,
25 lips, 26-29 scissors. Labels: 1 head piece, 2 bun, 3 hands, 4 ringlets, 5 skirt, 6 bodice + sleeves, 7 hidden legs
(above the shoes), 8 bow, 9 bow tails. Kept exactly: pieces of up to 250 faces (lacing, cuff ruffles, earrings,
pocket, scissors, eyes, lips, the apron's 299-face panel is labelled 10 and kept too: its painted stains tear), the
shoes (legs piece below 15 cm) and the skirt hem band (below 12 cm)."""
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
fp = np.load('work/face_piece.npy'); size = np.bincount(fp)[fp]
g = np.zeros(len(f), int)
for piece, lab in ((1, 1), (4, 2), (5, 3), (6, 3), (7, 4), (8, 4), (2, 5), (0, 6), (3, 7), (9, 8), (12, 9), (11, 10)):
    g[fp == piece] = lab
keep = (size <= 250) | (fp == 11) | ((fp == 3) & (c[:, 2] < .15)) | ((fp == 2) & (c[:, 2] < .12))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(11)}, 'keep', int(keep.sum()))
