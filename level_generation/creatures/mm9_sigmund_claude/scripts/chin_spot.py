#!/usr/bin/env python3
"""Chin speck (face lesson: no dirty specks): the head paint's small dark dot on the chin midline (|x| < 7 mm, rest y
1.503-1.524, front) is replaced by a wide low-pass of the surrounding skin (the dot's own texels excluded) plus the paint's
fine detail. Runs after eye_rims.py on textures/<p>_head_basecolor.png. Usage (project folder): chin_spot.py <prefix>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
P = sys.argv[1]
pos = np.load('work/head_texel_pos.npz')['pos']; ok = np.isfinite(pos[..., 0])
X, Y, Z = [np.nan_to_num(pos[..., i]) for i in range(3)]
path = f'textures/{P}_head_basecolor.png'
img = np.asarray(Image.open(path).convert('RGB')).astype(np.float64)
zone = ok & (np.abs(X) < 0.007) & (Y > 1.503) & (Y < 1.524) & (Z > 0.05)
ring = ok & (np.abs(X) < 0.02) & (Y > 1.495) & (Y < 1.535) & (Z > 0.04) & ~zone
w = ring.astype(float)
low = np.stack([ndimage.gaussian_filter(img[..., c] * w, 12) / np.maximum(ndimage.gaussian_filter(w, 12), 1e-6) for c in range(3)], -1)
lum = img @ np.array([0.299, 0.587, 0.114])
fine = (lum - ndimage.gaussian_filter(lum, 2))[..., None] * 0.6
zw = np.clip(ndimage.gaussian_filter(zone.astype(float), 1.5) * 1.3, 0, 1) * ok
out = img * (1 - zw[..., None]) + (low + fine) * zw[..., None]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(path)
print('CHINSPOT', P, int(zone.sum()))
