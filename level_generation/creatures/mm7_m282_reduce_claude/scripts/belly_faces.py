#!/usr/bin/env python3
"""Lavender belly scutes of the serpent (painted plate lines bend under any collapse: playbook, MM6 Medusa bodice and
the Fire Lizard's belly plates): faces of the skin piece with >= 3 of 7 base-colour samples bluish-lavender (hue
200-290 degrees, value > 0.45) and serpent weight > 0.5 -> work/belly.npy; prints counts by height."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v, w = d['faces'], d['verts'], d['wuv'].reshape(-1, 3, 2)
p = np.load('work/pieces.npy'); g = np.load('work/groups.npz'); names = [str(n) for n in g['names']]
serp = g['W'][:, [i for i, n in enumerate(names) if n.startswith(('Tail_', 'Col_', 'Root'))]].sum(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB')).astype(float) / 255; H, W = img.shape[:2]
bary = np.array([[1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6], [.8, .1, .1], [.1, .8, .1], [.1, .1, .8]])
pts = np.einsum('kj,fjc->fkc', bary, w)
px = np.clip((pts[..., 0] * W).astype(int), 0, W - 1); py = np.clip(((1 - pts[..., 1]) * H).astype(int), 0, H - 1)
rgb = img[py, px]; mx = rgb.max(-1); r, gg, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (gg - b), 2 * r - gg - b)) % 360
lav = ((hue > 200) & (hue < 290) & (mx > 0.45)).sum(1) >= 3
belly = lav & (p == 0) & (serp[f].mean(1) > 0.5)
np.save('work/belly.npy', belly); c = v[f].mean(1)
print('BELLY faces', int(belly.sum()), 'z>0.05', int((belly & (c[:, 2] > 0.05)).sum()), 'z>0.15', int((belly & (c[:, 2] > 0.15)).sum()))
