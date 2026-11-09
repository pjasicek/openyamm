#!/usr/bin/env python3
"""Per-face share of region-mask samples in each channel (work/regionmask.png, 24 samples per face) ->
work/face_regions.npy (faces x 4, 0-1). Used to find painted trims (guard: gold, mask B) for exact keeps."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v, uv = d['faces'], d['verts'], d['wuv'].reshape(-1, 3, 2)
m = np.asarray(Image.open('work/regionmask.png').convert('RGBA'), np.float32) / 255; H, W = m.shape[:2]
B = np.random.default_rng(2).dirichlet((1, 1, 1), 24)
u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
share = (m[y, x] > .5).mean(1)
np.save('work/face_regions.npy', share)
print('REGIONS faces with >30 %:', [int((share[:, c] > .3).sum()) for c in range(4)])
