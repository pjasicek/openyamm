#!/usr/bin/env python3
"""Aligned native pixels for the titan's tier ramps (claude_shared/native_shading.transfer_ramps): every opaque pixel of
the standing views ttn1sta0..4 classified in palette 828 (tier A), with its colour in 828, 829 and 830.
Regions: armour (lavender/periwinkle metal, hue 215-300, saturation >= 0.18), trim (gold, hue 30-65, saturation
>= 0.4, value >= 0.35), crest (red, hue < 15 or > 340, saturation >= 0.55, top 25 % of the figure), skin (the rest of
the low-saturation greys; unchanged between tiers, recorded for checks), and its height in the figure (coord: 0 at the
feet, 1 at the crest tip; native shading transfer in prepare_textures.py). Writes work/native_shading/pixels.npz and
review/native_regions.png (A/B/C rows with the classification)."""
import colorsys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
NAT = HERE.parent / 'mm6_ttn1' / 'native_variants'
PALS = (828, 829, 830)
NAMES = ['armour', 'trim', 'crest', 'skin']
region, cols, review, coord = [], {p: [] for p in PALS}, [], []
for i in range(5):
    ims = {p: np.asarray(Image.open(NAT / f'ttn1sta{i}_{p}.png').convert('RGBA'), np.float64) / 255 for p in PALS}
    a = ims[828]
    alpha = a[..., 3] > 0.5
    hsv = np.asarray(Image.fromarray((a[..., :3] * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    rows = np.nonzero(alpha.any(1))[0]; top, bot = rows.min(), rows.max()
    yy = np.arange(a.shape[0])[:, None] * np.ones(a.shape[1])[None]
    lab = np.full(alpha.shape, -1)
    lab[alpha & (s < 0.18)] = 3
    lab[alpha & (h > 215) & (h < 300) & (s >= 0.18)] = 0
    lab[alpha & (h > 30) & (h < 65) & (s >= 0.4) & (v >= 0.35)] = 1
    lab[alpha & ((h < 15) | (h > 340)) & (s >= 0.55) & (yy < top + 0.25 * (bot - top))] = 2
    y, x = np.nonzero(lab >= 0)
    region.append(lab[y, x])
    coord.append((bot - y) / (bot - top))                      # height: 0 at the feet, 1 at the crest tip
    for p in PALS:
        cols[p].append(ims[p][y, x, :3])
    vis = np.zeros(a.shape[:2] + (3,))
    for k, c in enumerate([(0.6, 0.6, 1), (1, 0.8, 0.1), (1, 0.1, 0.1), (0.5, 0.5, 0.5)]):
        vis[lab == k] = c
    review.append(np.concatenate([ims[p][..., :3] * ims[p][..., 3:] for p in PALS] + [vis], 0))
region = np.concatenate(region)
np.savez_compressed(HERE / 'work' / 'native_shading' / 'pixels.npz', region=region, region_names=np.array(NAMES),
                    coord=np.concatenate(coord),
                    **{f'p{p}': np.concatenate(cols[p]) for p in PALS})
Image.fromarray((np.concatenate(review, 1) * 255).astype(np.uint8)).save(HERE / 'review' / 'native_regions.png')
print('NATIVE pixels', {n: int((region == k).sum()) for k, n in enumerate(NAMES)})
for k, n in enumerate(NAMES[:3]):
    m = region == k
    print('MEDIAN', n, {p: (np.median(np.concatenate(cols[p])[m], 0) * 255).round().tolist() for p in PALS})
