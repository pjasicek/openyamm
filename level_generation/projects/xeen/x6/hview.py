#!/usr/bin/env python3
"""A quick shaded relief of land.py (A5, X6): run/hview.png, 4 px a cell, with the places of gen_l1 marked."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import land as LD, gen_l1 as L1
S = 4
N = 128 * S
h = np.zeros((N, N))
for j in range(N):
    for i in range(N):
        h[j, i] = LD.raw_height((i + 0.5) / S, (j + 0.5) / S)
gy, gx = np.gradient(h)
shade = np.clip(0.6 + (-gx - gy) / 160.0, 0, 1)
lo, hi = 900, 3800
c = np.clip((h - lo) / (hi - lo), 0, 1)
rgb = np.stack([0.35 + 0.65 * c, 0.3 + 0.5 * c, 0.2 + 0.3 * c], -1) * shade[..., None]
rgb[h < 1] = [0.05, 0.05, 0.15]
img = Image.fromarray((rgb * 255).astype(np.uint8))
d = ImageDraw.Draw(img)
for pid, at, f, n in L1.POINTS:
    x, y = at[0] * S, at[1] * S
    d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(255, 0, 0))
for link, line, w, s in L1.ROADS:
    d.line([(a * S, b * S) for a, b in line], fill=(255, 255, 255), width=1)
d.rectangle([19 * S, 19 * S, 109 * S, 109 * S], outline=(0, 255, 0))
out = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../run/hview.png')
img.save(out)
box = h[24 * S:109 * S, 24 * S:109 * S]
print('saved', out, 'box min %.0f max %.0f' % (box[box > 1].min(), box.max()))
