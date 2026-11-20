#!/usr/bin/env python3
"""Native pixels for the cleric's tier ramps (claude_shared/native_shading.transfer_ramps): every opaque pixel of the
original indexed standing views clesta0..4 (the retired runtime BMPs), read in palettes 674 (tier A: green tunic,
rust cloak), 675 (B: blue tunic, grey cloak) and 676 (C: tan tunic, red cloak). Regions by palette index, as the
restoration defines them (../mm6_cle/materials.py): tunic and sleeves 39-80, trousers and boots 81-121, cloak and
mantle the neutral-grey entries of 675; everything else (skin, hair, belt, gold, staff) is 'fixed'.
Height coordinate: 0 at the feet, 1 at the top of the hair (the staff columns are left out of the extent).
Writes work/native_shading/pixels.npz and review/native_regions.png (A/B/C rows and the classification)."""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parents[2]
BMP = REPO / 'assets_source/creatures/mm6/backups/20261004/native_runtime_retired/engine/sprites'
PALS = (674, 675, 676)
NAMES = ['tunic', 'legs', 'cloak', 'fixed']
pal = {p: np.fromfile(REPO / f'assets_dev/worlds/mm6/textures/pal{p}.act', np.uint8)[:768].reshape(256, 3) / 255
       for p in PALS}
ids = np.arange(256)
base = pal[675]
label_of = np.full(256, 3)
label_of[(ids >= 39) & (ids <= 80)] = 0
label_of[(ids >= 81) & (ids <= 121)] = 1
label_of[(base.max(1) - base.min(1) < 0.002) & (label_of == 3) & (ids > 0)] = 2
region, cols, coord, review = [], {p: [] for p in PALS}, [], []
for i in range(5):
    im = Image.open(BMP / f'clesta{i}.bmp')
    idx = np.asarray(im)
    alpha = idx != 0
    lab = label_of[idx]
    body = alpha & (lab != 3) | (alpha & (np.abs(np.arange(idx.shape[1])[None, :] - idx.shape[1] / 2) < 60))
    rows = np.nonzero(body.any(1))[0]; top, bot = rows.min(), rows.max()
    y, x = np.nonzero(alpha)
    region.append(lab[y, x]); coord.append(np.clip((bot - y) / (bot - top), 0, 1))
    for p in PALS:
        cols[p].append(pal[p][idx[y, x]])
    vis = np.zeros(idx.shape + (3,))
    for k, c in enumerate(((0.3, 0.5, 1.0), (0.6, 0.2, 0.9), (0.9, 0.9, 0.9), (0.4, 0.4, 0.4))):
        vis[alpha & (lab == k)] = c
    review.append(np.concatenate([pal[p][idx] * alpha[..., None] for p in PALS] + [vis], 0))
region = np.concatenate(region)
(HERE / 'work' / 'native_shading').mkdir(parents=True, exist_ok=True)
np.savez_compressed(HERE / 'work' / 'native_shading' / 'pixels.npz', region=region, region_names=np.array(NAMES),
                    coord=np.concatenate(coord), **{f'p{p}': np.concatenate(cols[p]) for p in PALS})
Image.fromarray((np.concatenate(review, 1) * 255).astype(np.uint8)).save(HERE / 'review' / 'native_regions.png')
print('NATIVE pixels', {n: int((region == k).sum()) for k, n in enumerate(NAMES)})
for k, n in enumerate(NAMES[:3]):
    m = region == k
    print('MEDIAN', n, {p: (np.median(np.concatenate(cols[p])[m], 0) * 255).round().tolist() for p in PALS})
