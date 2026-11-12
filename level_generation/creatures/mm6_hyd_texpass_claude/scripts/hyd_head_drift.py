"""Per-head drift of a heads paint against the approved heads paint at the same texels (2K, both on the study's heads
layout): mean sRGB, mean |difference|, low-pass (sigma 6 texels) difference, hue angle of the mean chroma.
Usage: hyd_head_drift.py <paint png (any size)> [label]"""
import colorsys
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import hyd_heads

P = hyd_heads.PROJECT
S = 2048
r = np.load(P / 'textures' / 'approved' / f'heads_raster{S}.npz')
tri_id = r['tri_id']
cov = tri_id >= 0
head_t, _ = hyd_heads.head_of_triangle()
hmap = np.where(cov, head_t[np.maximum(tri_id, 0)], 0)
appr = np.asarray(Image.open(P / 'textures' / 'approved' / 'heads_basecolor.png').convert('RGB'), np.float32)
img = Image.open(sys.argv[1]).convert('RGB')
if img.size != (S, S):
    img = img.resize((S, S), Image.Resampling.LANCZOS)
new = np.asarray(img, np.float32)


def low(x, m):
    den = np.maximum(ndimage.gaussian_filter(m.astype(np.float32), 6), 1e-4)
    return np.stack([ndimage.gaussian_filter(x[..., c] * m, 6) / den for c in range(3)], -1)


out = {}
for k in range(1, 6):
    m = hmap == k
    la, ln = low(appr, m), low(new, m)
    ma, mn = appr[m].mean(0), new[m].mean(0)
    ha = colorsys.rgb_to_hsv(*(ma.astype(float) / 255))
    hn = colorsys.rgb_to_hsv(*(mn.astype(float) / 255))
    out[k] = {'approved_mean': ma.round(1).tolist(), 'paint_mean': mn.round(1).tolist(),
              'mean_abs': round(float(np.abs(appr[m] - new[m]).mean()), 1),
              'low_abs': round(float(np.abs(la[m] - ln[m]).mean()), 1),
              'hue_deg': [round(float(ha[0]) * 360), round(float(hn[0]) * 360)], 'sat': [round(float(ha[1]), 2), round(float(hn[1]), 2)]}
print(json.dumps({'paint': sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], 'heads': out}, indent=1))
