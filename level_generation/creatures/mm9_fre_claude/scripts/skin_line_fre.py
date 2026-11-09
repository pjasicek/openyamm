#!/usr/bin/env python3
"""Fre head paint fix (2026-11-04): Meshy's 4K head paint carries a thin dark line across her left cheek and down the neck (a projection
seam inside a chart; visible in Meshy's own returned model, review/geo/texonly/meshy_front.png). Skin texels of the head shell (warm, light,
not the eyes, brows, lips, nostrils or hairline: excluded by 3D zones) that are darker than 0.86 of their 9-px median take the median's
colour plus a third of their own fine detail. Args: <in png> <out png>   (project folder; positions from work/uv_tex2.npz)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
POS = np.full((S, S, 3), np.nan)
for f in np.where((mat == 1) & (comp[tri[:, 0]] == names.index('head')))[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); b = np.vstack([l, 1 - l.sum(0)]); ok = (b >= -1e-4).all(0)
    if ok.any(): POS[gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)] = (b[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1)
x, y, z = POS[..., 0], POS[..., 1], POS[..., 2]; on = ~np.isnan(x); ax = np.abs(np.nan_to_num(x, nan=9)); z = np.nan_to_num(z, nan=-9); y = np.nan_to_num(y, nan=9)
feat = ((z > 0.655) & (z < 0.74) & (ax < 0.065) & (y < -0.06)) | ((z > 0.585) & (z < 0.632) & (ax < 0.032) & (y < -0.08)) | \
       ((z > 0.625) & (z < 0.66) & (ax < 0.022) & (y < -0.09)) | (z > 0.74)
r, g, b_ = im[..., 0], im[..., 1], im[..., 2]; lum = 0.2126 * r + 0.7152 * g + 0.0722 * b_
med = np.stack([ni.median_filter(im[..., c], size=9) for c in range(3)], -1); mlum = med @ [0.2126, 0.7152, 0.0722]
skin = on & ~feat & (med[..., 0] > 0.45) & (med[..., 0] > med[..., 1]) & (med[..., 1] > med[..., 2])      # the neighbourhood is skin
line = skin & (lum < float(__import__("os").environ.get("SKINLINE_T", "0.93")) * mlum)
line = ni.binary_dilation(line, iterations=1) & skin
out = im.copy(); out[line] = med[line] + (im[line] - med[line]) * 0.33
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST); print('SKINLINE texels', int(line.sum()))
