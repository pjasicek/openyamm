#!/usr/bin/env python3
"""Per-face base colour of the rest mesh (work/basecolor.png sampled at each face's mean UV -> work/facecol.npy) and the
gold trims (work/gold.npy): hue 0.08-0.17, saturation > 0.45, value > 0.45 on the shells that carry gold (boots 1/2,
legs 6, helmet 8, bracers 11/12, horns 17/18, buckle 23; the ginger beard shares the hue, so the torso/head shell is
excluded), and on the horns saturation > 0.6 (the ivory reads 0.32-0.53)."""
import colorsys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); p = np.load('work/pieces.npy')
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), float); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2).mean(1)
x = np.clip((uv[:, 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - uv[:, 1] % 1) * H, 0, H - 1).astype(int)
col = img[y, x]; np.save('work/facecol.npy', col)
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in col / 255])
gold = (hsv[:, 0] > 0.08) & (hsv[:, 0] < 0.17) & (hsv[:, 1] > 0.45) & (hsv[:, 2] > 0.45) & np.isin(p, (1, 2, 6, 8, 11, 12, 17, 18, 23))
gold &= ~(np.isin(p, (17, 18)) & (hsv[:, 1] < 0.6))
old = np.load('work/gold.npy') if __import__('os').path.exists('work/gold.npy') else None
np.save('work/gold.npy', gold); print('GOLD', int(gold.sum()), 'faces', '(unchanged)' if old is not None and (old == gold).all() else '')
