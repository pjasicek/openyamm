#!/usr/bin/env python3
"""Fre head paint (2026-11-04): Meshy's hair came out a saturated copper red (median HSV 18 deg / 0.94 / 0.33 on the cap); MM9's skin's
hair is chestnut-auburn (22 deg / 0.83 / 0.42 median of three hair areas). Hair texels of the cap and the braid (not the gold circlet and
bands: gold-yellow hues and light texels are left) get hue +DH, saturation x SAT, value x VAL, eased by darkness so the gold stays.
Args: <in png> <out png> [DH SAT VAL]   (project folder; faces from work/uv.npz)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
def rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; mx = a.max(-1); mn = a.min(-1); d = mx - mn; v = mx; s = np.where(mx > 0, d / np.maximum(mx, 1e-9), 0)
    dd = np.maximum(d, 1e-9); h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) / 6
    return np.stack([np.where(d > 0, h, 0), s, v], -1)
def hsv_to_rgb(a):
    h, s, v = a[..., 0] % 1, a[..., 1], a[..., 2]; i = np.floor(h * 6).astype(int) % 6; f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    r = np.choose(i, [v, q, p, p, t, v]); g = np.choose(i, [t, v, v, q, p, p]); b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)
SRC, DST = sys.argv[1:3]; DH, SAT, VAL = (float(x) for x in (sys.argv[3:6] if len(sys.argv) > 5 else (0.012, 0.88, 1.12)))
D = np.load('work/uv.npz'); tri, uv, mat, comp = D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
cv = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cv)
for f in np.where((mat == 1) & np.isin(comp[tri[:, 0]], [names.index('hood4'), names.index('braids')]))[0]:
    dr.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in tri[f]], fill=255)
m = np.asarray(cv) > 0
from scipy import ndimage as ni
cv2 = Image.new('L', (S, S), 0); dr2 = ImageDraw.Draw(cv2)
for f in np.where((mat == 1) & ~np.isin(comp[tri[:, 0]], [names.index('hood4'), names.index('braids')]))[0]:
    dr2.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in tri[f]], fill=255)
m &= ~ni.binary_dilation(np.asarray(cv2) > 0, iterations=2)      # never the face islands' border texels
hsv = rgb_to_hsv(im); h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
gold = (h > 0.085) & (h < 0.2) & (v > 0.45)
w = m & ~gold & (h < 0.085)
k = np.clip((0.55 - v) / 0.15, 0, 1) * w          # full on dark hair, fading out on light texels
hsv2 = hsv.copy(); hsv2[..., 0] = np.where(w, h + DH * k, h); hsv2[..., 1] = np.where(w, s * (1 - (1 - SAT) * k), s)
hsv2[..., 2] = np.where(w, np.clip(v * (1 + (VAL - 1) * k), 0, 1), v)
Image.fromarray((np.clip(hsv_to_rgb(hsv2), 0, 1) * 255 + .5).astype('u1')).save(DST); print('HAIRTONE texels', int(w.sum()))
