#!/usr/bin/env python3
"""The approved maps resampled onto the texture-pass layout at the same surface points: both dumps hold the same triangles
in the same order, only the UVs differ. Writes work/approved_graded_on_new.png, work/approved_classes_on_new.png (nearest,
compose.py's class * 80 values) and work/approved_cover_on_new.png.
Usage: approved_on_new.py <body> <old uv3d npz> <new uv3d npz>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
body, old_npz, new_npz = sys.argv[1:4]
B = HERE / 'work/before_texpass/textures'
old = np.asarray(Image.open(B / f'{body}_basecolor_graded.png').convert('RGB'), np.float32)
cls = np.asarray(Image.open(B / f'{body}_material_classes.png').convert('L').resize(old.shape[1::-1], Image.NEAREST))
A, N = np.load(HERE / old_npz), np.load(HERE / new_npz)
assert len(A['uv']) == len(N['uv'])
coeff = [ndimage.spline_filter(old[..., c], order=3, mode='nearest') for c in range(3)]
S = 2048
out, cover = np.zeros((S, S, 3), np.float32), np.zeros((S, S), bool)
outc = np.zeros((S, S), np.uint8)
for to, tn in zip(A['uv'].astype(np.float64), N['uv'].astype(np.float64)):
    p = np.stack([tn[:, 0] * S, (1 - tn[:, 1]) * S], 1)
    lo, hi = np.floor(p.min(0)).astype(int), np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if not xs.size:
        continue
    q = np.stack([xs.ravel() + .5, ys.ravel() + .5], 1)
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9:
        continue
    st = (q - p[0]) @ np.linalg.inv(T).T
    w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
    ins = (w >= -0.01).all(1)
    if not ins.any():
        continue
    uv = w[ins] @ to
    x, y = uv[:, 0] * old.shape[1] - .5, (1 - uv[:, 1]) * old.shape[0] - .5
    yy, xx = ys.ravel()[ins], xs.ravel()[ins]
    out[yy, xx] = np.stack([ndimage.map_coordinates(c, [y, x], order=3, mode='nearest', prefilter=False) for c in coeff], -1)
    outc[yy, xx] = cls[np.clip(np.round(y).astype(int), 0, cls.shape[0] - 1), np.clip(np.round(x).astype(int), 0, cls.shape[1] - 1)]
    cover[yy, xx] = True
W = HERE / 'work'
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(W / 'approved_graded_on_new.png')
Image.fromarray(outc).save(W / 'approved_classes_on_new.png')
Image.fromarray((cover * 255).astype(np.uint8)).save(W / 'approved_cover_on_new.png')
print('APPROVED_ON_NEW', int(cover.sum()), np.unique(outc, return_counts=True))
