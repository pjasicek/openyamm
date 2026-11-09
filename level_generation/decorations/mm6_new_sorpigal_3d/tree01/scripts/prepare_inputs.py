#!/usr/bin/env python3
"""Inputs for build_tree.py: work/bark_basecolor.png (Poly Haven bark_brown_02, linear-scaled so its mean matches the
sprite's reddish-brown trunk), work/bark_normal.png (its GL normal map) and work/profile.json (the canopy envelope:
the upscaled 6tree01 sprite's half-width per height, both as fractions of the tree height)."""
import os, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work'); S = os.path.join(HERE, 'source', 'bark_brown_02')
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
bark = lin(np.asarray(Image.open(os.path.join(S, 'bark_brown_02_diff_1k.png')).convert('RGB'), np.float32) / 255)
target = lin(np.array([104, 66, 46]) / 255.0)
bark = bark / bark.reshape(-1, 3).mean(0) * target
Image.fromarray((np.clip(srgb(bark), 0, 1) * 255).astype(np.uint8)).save(os.path.join(W, 'bark_basecolor.png'))
Image.open(os.path.join(S, 'bark_brown_02_nor_gl_1k.png')).convert('RGB').save(os.path.join(W, 'bark_normal.png'))
sprite = np.asarray(Image.open(os.path.join(HERE, '..', '..', 'mm6_new_sorpigal', 'enhanced', '6tree01.png')).convert('RGBA'))
a = sprite[..., 3] > 128
rows = np.where(a.any(1))[0]; top, bottom = rows.min(), rows.max(); H = bottom - top + 1
profile = []
for k in range(51):
    y = int(bottom - k / 50 * (H - 1))
    cols = np.where(a[y])[0]
    profile.append([k / 50, float((cols.max() - cols.min() + 1) / 2 / H) if cols.size else 0.0])
json.dump({'height_px': int(H), 'width_px': int(a.any(0).sum()), 'half_width_by_height': profile},
          open(os.path.join(W, 'profile.json'), 'w'), indent=1)
print('PROFILE', [(p[0], round(p[1], 3)) for p in profile[::5]])
