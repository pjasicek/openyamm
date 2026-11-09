#!/usr/bin/env python3
"""Bring each identity's hair to MM9's: the skins do paint hair on all three (work/mm9_hair.json from mm9_head_stats.py), so it stays, but ours came back too white and, on Shadow, too plain.
Back of the head: mean colour and strand contrast set to the skin's, the face untouched. Run from the project folder after head_a.py."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage
m = np.load('work/head_map.npz'); P, F = m['P'], m['F']
_, (iy, ix) = ndimage.distance_transform_edt(F < 0, return_indices=True)
P = P[iy, ix]
y, z = P[..., 1], P[..., 2]
H = json.load(open('work/mm9_hair.json'))
w = np.clip((y + 0.215) / 0.045, 0, 1); w = w * w * (3 - 2 * w)
core = (y > -0.17) & (F >= 0)
LUM = np.array([0.3, 0.59, 0.11])
for key, tier in (('a', '1'), ('b', '2'), ('c', '3')):
    fn = f'textures/ghost_head_{key}_graded.png'
    c = np.asarray(Image.open(fn).convert('RGB'), np.float32) / 255
    h = H[tier]
    mean = c[core].mean(0)
    L = c @ LUM
    fine = L - ndimage.gaussian_filter(L, 12)                # at 1K the skin's 256-texel strands are this wide
    gain = float(np.clip(h['strand_std'] / max(fine[core].std(), 1e-3) * (2.2 if key == 'a' else 1.0), 0.4, 2.2))
    base = ndimage.gaussian_filter(c, (14, 14, 0))
    out = np.array(h['rgb'], np.float32) + (base - mean) * 0.5 + (fine * gain)[..., None]
    c2 = c * (1 - w[..., None]) + out * w[..., None]
    Image.fromarray((c2.clip(0, 1) * 255).astype(np.uint8)).save(fn)
    print('HAIR', key, 'ours', mean.round(3), 'mm9', h['rgb'], 'strand gain', round(gain, 2))
