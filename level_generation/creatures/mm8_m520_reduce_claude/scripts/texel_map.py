#!/usr/bin/env python3
"""Rasterise the source rest mesh (work/mesh_in.npz) into the atlas: per-texel face id and rest-pose position ->
work/retex/texel_map.npz (face: -1 where no face). Used to find region-mask blobs by their place on the body."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); v, f, w = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
H, W = np.asarray(Image.open('work/retex/img3.png')).shape[:2]
face = -np.ones((H, W), np.int32); pos = np.zeros((H, W, 3), np.float32)
for i, (t, uv) in enumerate(zip(v[f], w)):
    p = np.c_[(uv[:, 0] % 1) * W - .5, (1 - uv[:, 1] % 1) * H - .5]
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W - 1), min(y1, H - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
    q = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float64)
    a, b, c = p; m = np.array([b - a, c - a]).T
    if abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T; l = np.c_[1 - l.sum(1), l]
    ok = (l >= -1e-6).all(1)
    face[gy.ravel()[ok], gx.ravel()[ok]] = i; pos[gy.ravel()[ok], gx.ravel()[ok]] = l[ok] @ t
np.savez_compressed('work/retex/texel_map.npz', face=face, pos=pos); print('TEXELS', int((face >= 0).sum()))
