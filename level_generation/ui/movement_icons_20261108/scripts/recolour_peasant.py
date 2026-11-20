"""Recolours the MM6 peasant's body texture to the Water Walk icon's man: green tunic -> off-white shirt, light
trousers -> charcoal. The head atlas (right half) keeps its skin and hair.

python3 recolour_peasant.py <basecolor.png> <out.png>
"""
import sys

import numpy as np
from PIL import Image

src = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32) / 255
hsv = np.asarray(Image.open(sys.argv[1]).convert("HSV")).astype(np.float32) / 255
h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
body = np.zeros(s.shape, bool)
body[:, : src.shape[1] // 2] = True
lum = src @ np.array([0.3, 0.59, 0.11])
out = src.copy()
green = body & (h > 70) & (h < 190) & (s > 0.12)
detail = lum / max(lum[green].mean(), 1e-3)
out[green] = (np.array([0.86, 0.85, 0.82])[None, :] * np.clip(detail[green], 0.6, 1.25)[:, None])
light = body & (s < 0.3) & (v > 0.45) & (h > 26) & ~green
detail = lum / max(lum[light].mean(), 1e-3)
out[light] = (np.array([0.20, 0.20, 0.22])[None, :] * np.clip(detail[light], 0.6, 1.4)[:, None])
Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(sys.argv[2])
print("green", green.sum(), "light", light.sum())
