#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Mage (faces -y, staff in the LEFT fist). Pieces come from the production master (mm7_m274_claude/work/rig_v6.blend,
'piece' attribute, mapped by rest position, work/face_piece.npy): 0 head + beard, 1 robe top + sleeves, 2 robe lower,
3 collar + yoke, 4 star cape, 5 legs + shoes, 6 right hand, 7 left fist (staff grip), 8/9 braids, 10 belt medallion,
11-13 mouth and eyes. Labels: 0 unused, 1 face (head piece outside the beard mask), 2 beard (head piece, region mask
B = the beard tier ramp), 3 right hand, 5 robe lower, 6 robe top + sleeves, 7 collar + yoke, 8 cape, 9 legs.
Kept exactly: pieces of up to 250 faces (braids, medallion, mouth, eyes), the left fist (fitted staff grip), shoes
(legs piece below 15 cm) and the hem bands of robe and cape (below 12 cm)."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
fp = np.load('work/face_piece.npy'); size = np.bincount(fp)[fp]
mask = np.asarray(Image.open('work/tex_m274_region_mask_head_atlas.png'))[..., 2].astype(float) / 255; H, W = mask.shape
uv = d['wuv'].reshape(-1, 3, 2); p = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)
x = np.clip((p[..., 0] % 1 * W).astype(int), 0, W - 1); y = np.clip(((1 - p[..., 1] % 1) * H).astype(int), 0, H - 1)
beard = mask[y, x].mean(1) > .5
g = np.zeros(len(f), int)
g[fp == 0] = 1; g[(fp == 0) & beard] = 2
for piece, lab in ((6, 3), (2, 5), (1, 6), (3, 7), (4, 8), (5, 9)):
    g[fp == piece] = lab
keep = (size <= 250) | (fp == 7) | ((fp == 5) & (c[:, 2] < .15)) | (np.isin(fp, [2, 4]) & (c[:, 2] < .12))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(10)}, 'keep', int(keep.sum()), 'beard', int(beard.sum()))
