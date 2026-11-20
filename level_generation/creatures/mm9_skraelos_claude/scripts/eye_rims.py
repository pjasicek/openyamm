#!/usr/bin/env python3
"""Eye rims without red (face lesson: no heavy red rims, no dark wedges under the eyes): around each eye (|x| 1.0-5.2 cm,
EY0 < y < EY1, front; head_texel_pos.py positions) texels redder than the cheek (r/g above the cheek's x 1.06) move 70 %
toward the cheek's hue at their own luminance, feathered 1 px; texels under the eyes darker than 0.78 x the cheek's
luminance (bags) are lifted 40 % toward it. Runs on textures/<p>_head_basecolor.png after face_fix_dboy.py.
Usage (project folder): eye_rims.py <prefix> <ey0> <ey1>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
P, EY0, EY1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
pos = np.load('work/head_texel_pos.npz')['pos']; ok = np.isfinite(pos[..., 0])
X, Y, Z = [np.nan_to_num(pos[..., i]) for i in range(3)]
path = f'textures/{P}_head_basecolor.png'
img = np.asarray(Image.open(path).convert('RGB')).astype(np.float64)
ck = np.array([float(v) for v in open(f'work/hand_ref_{P}.txt').read().split(',')])
lum = img @ np.array([0.2126, 0.7152, 0.0722]); lck = ck @ np.array([0.2126, 0.7152, 0.0722])
zone = ok & (Z > 0.05) & (np.abs(X) > 0.010) & (np.abs(X) < 0.052) & (Y > EY0) & (Y < EY1)
red = zone & (img[..., 0] / np.maximum(img[..., 1], 1) > ck[0] / ck[1] * 1.06)
w = np.clip(ndimage.gaussian_filter(red.astype(float), 1.0) * 1.4, 0, 1) * zone * 0.7
target = ck[None, None] * (lum / lck)[..., None]
out = img * (1 - w[..., None]) + target * w[..., None]
under = zone & (Y < (EY0 + EY1) / 2) & (lum < 0.78 * lck)
wb = np.clip(ndimage.gaussian_filter(under.astype(float), 1.2) * 1.3, 0, 1) * zone * 0.4
lum2 = out @ np.array([0.2126, 0.7152, 0.0722])
out = out * (1 - wb[..., None]) + (out * (lck / np.maximum(lum2, 1))[..., None]) * wb[..., None]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(path)
print('EYERIMS', P, {'red_texels': int(red.sum()), 'under_dark': int(under.sum())})
