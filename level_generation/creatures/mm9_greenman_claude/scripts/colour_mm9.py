#!/usr/bin/env python3
"""Grade the paint toward MM9's Green Man (mm9_greenman pass 2, orchestrator: "much brighter and more saturated than MM9's
dark olive-and-moss"). Measured on the skins (median HSV; MM9's 256 px skin carries baked shading, so its values are
read x1.3 as albedo): MM9 skin h 0.174 s 0.73 v 0.26 (x1.3 = 0.34), leaves h 0.269 s 0.59 v 0.28 (0.37); ours skin
h 0.17-0.18 s 0.74-0.78 v 0.35, leaves h 0.23 s 0.74-0.80 v 0.35-0.40 (lime). Per texel, by hue weight (smooth bands): skin
(yellow-olive, h 0.12-0.20) v x SKV, s x SKS, a small shift toward olive; leaves (green, h 0.20-0.45) hue toward 0.262,
s x LFS, v x LFV (head set: x LFVH, its leaves were the brighter). Luminance detail is kept (only HSV scaling). The staff
strip and the eyes (two small boxes round the irises in the face chart) are left out.
Usage (project folder): colour_mm9.py <body png> <head png>   (edit in place; run last in the paint chain)"""
import sys
import numpy as np
from PIL import Image
SKV, SKS, LFS, LFV, LFVH = 0.74, 0.86, 0.70, 0.80, 0.74   # pass 2b: the first grade (0.86/0.90/0.80/0.93/0.86) still read bright lime in the viewer
BKV = 0.78   # bark (crown branches, wrist vines): MM9's are dark brown
def rgb2hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx); m = d > 1e-6
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6; h[gm] = (b - r)[gm] / d[gm] + 2; h[bm] = (r - g)[bm] / d[bm] + 4
    return np.stack([h / 6, np.where(mx > 0, d / np.maximum(mx, 1e-6), 0), mx], -1)
def hsv2rgb(x):
    h, s, v = x[..., 0] * 6, x[..., 1], x[..., 2]; i = np.floor(h) % 6; f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.zeros(x.shape)
    for k, (r, g, b) in enumerate(((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))):
        m = i == k; out[m] = np.stack([r[m], g[m], b[m]], -1)
    return out
def band(h, lo, hi, soft=0.02):
    return np.clip((h - lo + soft) / (2 * soft), 0, 1) * np.clip((hi + soft - h) / (2 * soft), 0, 1)
def grade(path, lfv, exclude):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255
    x = rgb2hsv(a); h = x[..., 0]
    ws = band(h, 0.12, 0.20) * (x[..., 1] > 0.25); wl = band(h, 0.20, 0.45) * (x[..., 1] > 0.2)
    y = x.copy()
    y[..., 2] = x[..., 2] * (1 - ws * (1 - SKV)) * (1 - wl * (1 - lfv))
    y[..., 1] = x[..., 1] * (1 - ws * (1 - SKS)) * (1 - wl * (1 - LFS))
    y[..., 0] = h + ws * (0.160 - h) * 0.4 + wl * (0.270 - h) * 0.75
    wb = band(h, 0.03, 0.115) * (x[..., 1] > 0.25)
    y[..., 2] = y[..., 2] * (1 - wb * (1 - BKV))
    out = hsv2rgb(np.clip(y, 0, 1))
    N = a.shape[0]
    for (u0, v0, u1, v1) in exclude:                 # UV boxes (glTF v down = image rows)
        out[int(v0 * N):int(v1 * N), int(u0 * N):int(u1 * N)] = a[int(v0 * N):int(v1 * N), int(u0 * N):int(u1 * N)]
    Image.fromarray(np.uint8(np.clip(np.round(out * 255), 0, 255))).save(path)
    return float(ws.mean()), float(wl.mean())
b = grade(sys.argv[1], LFV, [])
# head set: the staff strip (u 0.82-0.98, v 0.02-0.58 in HeadUV, v up -> rows from the bottom) and the eyes (face chart)
N = 2048
staff = (0.82 - 0.004, 1 - 0.58 - 0.004, 0.98 + 0.004, 1 - 0.02 + 0.004)
eyes = [((121 - 22) / N, (521 - 14) / N, (121 + 22) / N, (521 + 14) / N), ((238 - 22) / N, (521 - 14) / N, (238 + 22) / N, (521 + 14) / N)]
h = grade(sys.argv[2], LFVH, [staff] + eyes)
print('COLOURMM9 body skin/leaf weight %.2f/%.2f head %.2f/%.2f' % (b + h))
