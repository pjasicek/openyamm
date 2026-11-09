#!/usr/bin/env python3
"""Rasterise the source mesh's UV triangles (work/mesh_in.npz) into a face-id map at the atlas size
-> work/uv_faceid.npy (-1 = no face). Used by mask_fix.py to find texels by the face (and bone) they belong to."""
import numpy as np
from PIL import Image
W, H = Image.open('work/img0.png').size
d = np.load('work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2).astype(np.float64)
fid = -np.ones((H, W), np.int32)
px = np.stack([uv[..., 0] * W - .5, (1 - uv[..., 1]) * H - .5], -1)
for i, t in enumerate(px):
    x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W - 1), min(y1, H - 1)
    if x1 < x0 or y1 < y0:
        continue
    X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
    a, b, c = t; v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-12:
        continue
    px_ = X - a[0]; py_ = Y - a[1]
    u = (px_ * v1[1] - v1[0] * py_) / den; v = (v0[0] * py_ - px_ * v0[1]) / den
    ins = (u >= -.02) & (v >= -.02) & (u + v <= 1.02)
    fid[Y[ins], X[ins]] = i
np.save('work/uv_faceid.npy', fid); print('UVFACEID', (fid >= 0).sum(), 'texels covered')
