#!/usr/bin/env python3
"""Painted straps and trims on the body texture set (work/basecolor.png, work/regions.npy): body faces with any of 16
sample points in the dark-brown leather of the chest strap (value < M222_STRAP_V, red > green > blue), or in the green
cloth (green clearly above red and blue: arm bands, the top's hem). The texture-aware collapse bends such thin painted
lines and smears them over the chain mail. -> work/trims.npy (bool per face), work/trim_labels.npy (1 strap, 2 green).
Usage: trim_faces.py"""
import os
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; reg = np.load('work/regions.npy'); c = v[f].mean(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.vstack([np.eye(3), np.full((1, 3), 1 / 3), np.random.default_rng(2).dirichlet((1, 1, 1), 12)])
uv = d['wuv'].reshape(-1, 3, 2); u = np.einsum('sk,fkc->fsc', B, uv)
col = img[np.clip(((1 - u[..., 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[..., 0] % 1) * W).astype(int), 0, W - 1)]
r, g, b = col[..., 0], col[..., 1], col[..., 2]; val = col.max(-1)
VMAX = float(os.environ.get('M222_STRAP_V', '0.42'))
strap = ((val < VMAX) & (val > 0.08) & (r > g * 1.15) & (g > b * 1.1)).any(1)
green = ((g > r * 1.3) & (g > b * 1.3) & (g > 0.12)).any(1)
body = (reg == 1) & (c[:, 2] > 0.95)  # torso: the strap, the top's hem and the sleeves' bands
lab = np.zeros(len(f), int); lab[body & green] = 2; lab[body & strap] = 1
np.save('work/trims.npy', lab > 0); np.save('work/trim_labels.npy', lab)
print('TRIMS strap', int((lab == 1).sum()), 'green', int((lab == 2).sum()), 'of', int(body.sum()), 'torso faces')
