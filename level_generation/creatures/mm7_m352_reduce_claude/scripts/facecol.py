#!/usr/bin/env python3
"""Per-face base colour of the rest mesh (work/basecolor.png sampled at each face's mean UV) -> work/facecol.npy
(m352: the colour part of m190's gold_faces.py)."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz')
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), float); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2).mean(1)
x = np.clip((uv[:, 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - uv[:, 1] % 1) * H, 0, H - 1).astype(int)
col = img[y, x]; np.save('work/facecol.npy', col); print('FACECOL', len(col))
