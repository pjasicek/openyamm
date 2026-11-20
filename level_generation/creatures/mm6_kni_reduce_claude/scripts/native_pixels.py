#!/usr/bin/env python3
"""Aligned native pixels for the knight's tier ramps and saturation targets (claude_shared/native_shading): every
opaque pixel of the standing views knistaa0..4 classified in palette 760 (tier A), with its colour in 760, 761, 762.
Regions: trim (the tier colour: violet in A, red in B, ivory in C; hue 200-320 and saturation >= 0.25 in 760, and
the pixel must change between the palettes), chrome (the black armour: everything else that the palettes keep),
and its height in the figure (coord: 0 at the feet, 1 at the horn tips). The sword is cut away by its position
(left of the hips in views 0-1). Writes work/native/pixels.npz, review/retex/native_regions.png and prints medians."""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
NAT = HERE.parent / 'mm6_kni' / 'native_variants'
PALS = (760, 761, 762)
NAMES = ['trim', 'chrome']
(HERE / 'work' / 'native').mkdir(parents=True, exist_ok=True)
region, cols, coord, review = [], {p: [] for p in PALS}, [], []
for i in range(5):
    ims = {p: np.asarray(Image.open(NAT / f'knistaa{i}_{p}.png').convert('RGBA'), np.float64) / 255 for p in PALS}
    a = ims[760]; alpha = a[..., 3] > .5
    hsv = np.asarray(Image.fromarray((a[..., :3] * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    changes = np.abs(ims[761][..., :3] - a[..., :3]).sum(-1) > .08
    rows = np.nonzero(alpha.any(1))[0]; top, bot = rows.min(), rows.max()
    lab = np.full(alpha.shape, -1)
    lab[alpha] = 1
    lab[alpha & changes & (h > 200) & (h < 320) & (s >= .25)] = 0
    # the curved sword (silver blade, wooden grip) crosses the body in the front views: drop its pixels
    if i in (0, 1):
        sword = alpha & (s < .15) & (v > .55) & (np.arange(a.shape[0])[:, None] > top + .45 * (bot - top))
        lab[sword] = -1
    y, x = np.nonzero(lab >= 0)
    region.append(lab[y, x]); coord.append((bot - y) / (bot - top))
    for p in PALS:
        cols[p].append(ims[p][y, x, :3])
    vis = np.zeros(a.shape[:2] + (3,))
    vis[lab == 0] = (.7, .4, 1); vis[lab == 1] = (.35, .35, .35)
    review.append(np.concatenate([ims[p][..., :3] * ims[p][..., 3:] for p in PALS] + [vis], 0))
region = np.concatenate(region)
np.savez_compressed(HERE / 'work' / 'native' / 'pixels.npz', region=region, region_names=np.array(NAMES),
                    coord=np.concatenate(coord), **{f'p{p}': np.concatenate(cols[p]) for p in PALS})
(HERE / 'review' / 'retex').mkdir(parents=True, exist_ok=True)
Image.fromarray((np.concatenate(review, 1) * 255).astype(np.uint8)).save(HERE / 'review' / 'retex' / 'native_regions.png')
print('NATIVE pixels', {n: int((region == k).sum()) for k, n in enumerate(NAMES)})
for k, n in enumerate(NAMES):
    m = region == k
    print('MEDIAN', n, {p: (np.median(np.concatenate(cols[p])[m], 0) * 255).round().tolist() for p in PALS})
