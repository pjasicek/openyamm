#!/usr/bin/env python3
"""Fleece armhole trim faces of the 7m452 torso piece: outside the tunic region mask (R < 0.5) with a bright,
unsaturated base colour (max > 0.55, saturation < 0.25) sampled at 4 points per face -> work/fleece.npy, work/facecol.npy."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
bc = np.array([[1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]]); pts = np.einsum('kj,fjc->fkc', bc, uv)
px = np.clip((pts[..., 0] % 1) * W, 0, W - 1).astype(int); py = np.clip((1 - pts[..., 1]) * H, 0, H - 1).astype(int)
col = img[py, px].mean(1); mx = col.max(1); sat = (mx - col.min(1)) / np.maximum(mx, 1e-6)
p = np.load('work/pieces.npy'); rm = np.load('work/regmask.npy')
fleece = (p == 0) & (rm[:, 0] < .5) & (mx > .55) & (sat < .25)
np.save('work/fleece.npy', fleece); np.save('work/facecol.npy', col)
print('FLEECE torso faces', int(fleece.sum()))
