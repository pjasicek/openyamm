#!/usr/bin/env python3
"""Aligned native pixels for the werewolf's tier ramps (claude_shared/native_shading.transfer_ramps): every opaque
pixel of the standing views (wfigt1a0 front, wwalk1a1..a4 three-quarter, profile, rear three-quarter, back),
classified in palette 831 (tier A), with its colour in 831, 832 and 833. Regions: shorts (rust cloth: hue 8-38,
saturation >= 0.35, value >= 0.15), gold (chain and pendant ring: hue 38-70, saturation >= 0.4, value >= 0.35; the
same in every palette), gem (pendant stone: hue 150-210, saturation >= 0.3, value >= 0.25; cyan / red / blue) and fur
(the rest; unchanged between tiers); gem pixels also from the front fidget, bite and walk frames, with the height in the figure (0 at the feet, 1 at the ear tips). Writes
work/native_shading/pixels.npz and review/native_regions.png (A/B/C rows with the classification)."""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
NAT = HERE.parent / 'mm6_wfigt1' / 'native_variants'
PALS = (831, 832, 833)
NAMES = ['shorts', 'gold', 'gem', 'fur']
FRAMES = ['wfigt1a0', 'wwalk1a1', 'wwalk1a2', 'wwalk1a3', 'wwalk1a4']
# the gem is ~20 pixels per view: front fidget and bite frames add gem pixels only
GEM_FRAMES = ['wfigt1b0', 'wfigt1c0', 'wfigt1d0', 'wfigt1e0', 'wfigt1f0', 'wbite1a0', 'wbite1b0', 'wbite1c0',
              'wbite1d0', 'wbite1e0', 'wwalk1b0', 'wwalk1c0', 'wwalk1d0', 'wwalk1e0', 'wwalk1f0']
region, cols, review, coord = [], {p: [] for p in PALS}, [], []
for fr in FRAMES + GEM_FRAMES:
    gem_only = fr in GEM_FRAMES
    ims = {p: np.asarray(Image.open(NAT / f'{fr}_{p}.png').convert('RGBA'), np.float64) / 255 for p in PALS}
    a = ims[831]
    alpha = a[..., 3] > 0.5
    hsv = np.asarray(Image.fromarray((a[..., :3] * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    rows = np.nonzero(alpha.any(1))[0]; top, bot = rows.min(), rows.max()
    lab = np.full(alpha.shape, -1)
    lab[alpha] = 3
    lab[alpha & (h > 8) & (h < 38) & (s >= 0.35) & (v >= 0.15)] = 0
    lab[alpha & (h >= 38) & (h < 70) & (s >= 0.4) & (v >= 0.35)] = 1
    lab[alpha & (h > 150) & (h < 210) & (s >= 0.3) & (v >= 0.25)] = 2
    if gem_only:
        lab[lab != 2] = -1
    y, x = np.nonzero(lab >= 0)
    region.append(lab[y, x])
    coord.append((bot - y) / (bot - top))
    for p in PALS:
        cols[p].append(ims[p][y, x, :3])
    vis = np.zeros(a.shape[:2] + (3,))
    for k, c in enumerate([(0.9, 0.5, 0.2), (1, 0.85, 0.1), (0.1, 0.9, 0.9), (0.4, 0.4, 0.4)]):
        vis[lab == k] = c
    if not gem_only:
        review.append(np.concatenate([ims[p][..., :3] * ims[p][..., 3:] for p in PALS] + [vis], 0))
region = np.concatenate(region)
np.savez_compressed(HERE / 'work' / 'native_shading' / 'pixels.npz', region=region, region_names=np.array(NAMES),
                    coord=np.concatenate(coord), **{f'p{p}': np.concatenate(cols[p]) for p in PALS})
Image.fromarray((np.concatenate(review, 1) * 255).astype(np.uint8)).save(HERE / 'review' / 'native_regions.png')
print('NATIVE pixels', {n: int((region == k).sum()) for k, n in enumerate(NAMES)})
for k, n in enumerate(NAMES):
    m = region == k
    print('MEDIAN', n, {p: (np.median(np.concatenate(cols[p])[m], 0) * 255).round().tolist() for p in PALS})
