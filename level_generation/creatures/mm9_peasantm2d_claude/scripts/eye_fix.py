#!/usr/bin/env python3
"""Eye area (wave-1 lessons: no heavy red rims, no crescent under the lower lids). The head paint drew a saturated pink-red ring round both
eyes (lower rims and inner corners) and dark grey-violet circles under them (a tired look). Head texels (texel_pos rest positions):
- rims: in the eye boxes (|x| 0.010-0.060, z 0.776-0.810, front-facing y < -0.05) texels redder than the cheek skin (r/g over the cheek's
  by > 0.10, not iris, not lashes) move K_RIM of the way to the cheek skin's r/g and r/b at their own luminance;
- circles: below each eye (Gaussian falloff about |x| 0.031, z 0.7765: sigma 15 x 7.5 mm, cut above z 0.786-0.789) texels darker than the cheek skin take K_DARK of
  the missing luminance back, with the cheek's colour ratios.
Usage (project folder): eye_fix.py <in head png> <out head png> [K_RIM 0.65] [K_DARK 0.6]"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, dst = sys.argv[1:3]; KR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.65; KD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
img = np.asarray(Image.open(src).convert('RGB')).astype(np.float64)
TP = np.load('work/texpos_head.npz'); pos, ok, fid = TP['pos'], TP['ok'], TP['face']
Z = np.load('work/faces.npz'); PART = Z['part']
shell = ok & (PART[np.maximum(fid, 0)] == 20)
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]; ax = np.abs(x)
box = shell & (ax > 0.010) & (ax < 0.060) & (y < -0.05) & (z > 0.776) & (z < 0.810)
cheek = shell & (ax > 0.03) & (ax < 0.055) & (y < -0.05) & (z > 0.745) & (z < 0.765)
r, g, b = img[..., 0] + 1, img[..., 1] + 1, img[..., 2] + 1
rg0, rb0 = np.median((r / g)[cheek]), np.median((r / b)[cheek])
W = np.array([0.299, 0.587, 0.114]); lum = img @ W; L0 = float(np.median(lum[cheek]))
red = box & (r / g > rg0 + 0.10) & (b < r * 0.85) & (lum > 50)
w = ndi.gaussian_filter(red.astype(float), 1.0) * box * KR
skin = np.stack([r, r / rg0, r / rb0], -1) - 1
skin *= (lum / np.maximum(skin @ W, 1))[..., None]
out = img * (1 - w[..., None]) + skin * w[..., None]
ramp = lambda v, a, c: np.clip((v - a) / (c - a), 0, 1)
zone = shell & (y < -0.05) & (np.abs(ax - 0.031) < 0.04) & (z > 0.760) & (z < 0.790)
# smooth elliptical falloff (a 2 mm ramp drew a pale crescent with a hard lower edge)
fz = np.exp(-((ax - 0.031) / 0.015) ** 2 - ((z - 0.7765) / 0.0075) ** 2) * (1 - ramp(z, 0.786, 0.789))
lum2 = out @ W
need = np.clip(L0 - lum2, 0, None) * KD * fz * zone
tone = np.stack([np.ones_like(lum2), 1 / rg0 * np.ones_like(lum2), 1 / rb0 * np.ones_like(lum2)], -1)
tone /= (tone @ W)[..., None]
target = out * (1 - (fz * zone * KD * 0.5)[..., None]) + (tone * (lum2 + need)[..., None]) * (fz * zone * KD * 0.5)[..., None]
target *= ((lum2 + need) / np.maximum(target @ W, 1))[..., None]
out = np.where((zone & (need > 0))[..., None], target, out)
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(dst)
print('EYES', json.dumps(dict(box=int(box.sum()), red=int(red.sum()), zone=int(zone.sum()), cheek_rg=round(float(rg0), 3), cheek_rb=round(float(rb0), 3), cheek_lum=round(L0, 1))))
