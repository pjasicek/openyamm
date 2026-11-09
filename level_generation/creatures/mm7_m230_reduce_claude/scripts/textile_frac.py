#!/usr/bin/env python3
"""Share of each face's base-colour samples that are tabard cloth (green, white or red stain; not steel or gold)
-> work/textile_frac.npy (work/mesh_in.npz, work/basecolor.png)."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz')
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 12); uv = d['wuv'].reshape(-1, 3, 2)
u = np.einsum('sk,fkc->fsc', B, uv)
col = img[np.clip(((1 - u[..., 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[..., 0] % 1) * W).astype(int), 0, W - 1)]
r, g, b = col[..., 0], col[..., 1], col[..., 2]
green = (g > r + .05) & (g > b + .02); white = (col.min(-1) > .62) & (np.ptp(col, -1) < .15); red = (r > g + .2) & (r > b + .2)
tex = (green | white | red).mean(1); np.save('work/textile_frac.npy', tex); print('TEXTILE faces > 0.3:', int((tex > .3).sum()))
