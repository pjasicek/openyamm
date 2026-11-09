#!/usr/bin/env python3
"""Aligned native pixels for the thief's tier ramps (claude_shared/native_shading.transfer_ramps): every opaque pixel
of the standing views thfstaa0..4 in palettes 825 (tier A, green), 826 (B, purple) and 827 (C, brown). The tiers are
deterministic recolours of one image (mm6_thf/README.md), so the recolourable cloth region (hood, mantle, cloak, the
jade undershirt cuffs and hem) is exactly the set of pixels whose colour differs between the palettes; everything
else (skin, hair, leather, trousers, boots) is 'fixed'. Height coordinate: 0 at the feet, 1 at the hood tip.
Writes work/native_shading/pixels.npz and review/native_regions.png (A/B/C rows and the classification)."""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
NAT = HERE.parent / 'mm6_thf' / 'native_variants'
PALS = (825, 826, 827)
NAMES = ['cloth', 'fixed']
region, cols, review, coord = [], {p: [] for p in PALS}, [], []
for i in range(5):
    ims = {p: np.asarray(Image.open(NAT / f'thfstaa{i}_{p}.png').convert('RGBA'), np.float64) / 255 for p in PALS}
    a = ims[825]
    alpha = a[..., 3] > 0.5
    diff = np.maximum(np.abs(ims[826][..., :3] - a[..., :3]).max(-1), np.abs(ims[827][..., :3] - a[..., :3]).max(-1))
    rows = np.nonzero(alpha.any(1))[0]; top, bot = rows.min(), rows.max()
    lab = np.full(alpha.shape, -1)
    lab[alpha] = 1
    lab[alpha & (diff > 4 / 255)] = 0
    y, x = np.nonzero(lab >= 0)
    region.append(lab[y, x]); coord.append((bot - y) / (bot - top))
    for p in PALS:
        cols[p].append(ims[p][y, x, :3])
    vis = np.zeros(a.shape[:2] + (3,))
    vis[lab == 0] = (0.3, 0.9, 0.3); vis[lab == 1] = (0.5, 0.5, 0.5)
    review.append(np.concatenate([ims[p][..., :3] * ims[p][..., 3:] for p in PALS] + [vis], 0))
region = np.concatenate(region)
np.savez_compressed(HERE / 'work' / 'native_shading' / 'pixels.npz', region=region, region_names=np.array(NAMES),
                    coord=np.concatenate(coord), **{f'p{p}': np.concatenate(cols[p]) for p in PALS})
Image.fromarray((np.concatenate(review, 1) * 255).astype(np.uint8)).save(HERE / 'review' / 'native_regions.png')
print('NATIVE pixels', {n: int((region == k).sum()) for k, n in enumerate(NAMES)})
m = region == 0
print('MEDIAN cloth', {p: (np.median(np.concatenate(cols[p])[m], 0) * 255).round().tolist() for p in PALS})
