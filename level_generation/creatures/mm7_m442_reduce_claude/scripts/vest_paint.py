#!/usr/bin/env python3
"""Painted detail on the vest (group 7 of a set) from the base colour: faces whose texture samples (a 6 x 6 barycentric
grid) contain gold/brown trim or seam (hue 20-60 deg, saturation > 0.35, value > 0.3) or white studs (value > 0.7,
saturation < 0.25), grown by REA_RINGS (default 1) edge rings inside the vest -> work/vest_paint.npy (bool per face).
The decimation drags these thin painted lines and dots (the back seam bent into a diagonal at 85 %).
Usage: vest_paint.py <set name>"""
import colorsys, os, sys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
g = np.load(f'work/groups_{sys.argv[1]}.npy'); vest = g == 7
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
k = np.array([(a, b, 1 - a - b) for a in np.linspace(0, 1, 6) for b in np.linspace(0, 1, 6) if a + b <= 1 + 1e-9])
pts = np.einsum('kj,fjc->fkc', k, uv)
px = np.clip((pts[..., 0] % 1) * W, 0, W - 1).astype(int); py = np.clip((1 - pts[..., 1]) * H, 0, H - 1).astype(int)
c = img[py, px]; mx = c.max(-1); mn = c.min(-1); s = (mx - mn) / (mx + 1e-6)
r, gg, b = c[..., 0], c[..., 1], c[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (gg - b), 2 * r - gg - b)) % 360
gold = (hue > 20) & (hue < 60) & (s > .35) & (mx > .3)
white = (mx > .7) & (s < .25)
paint = vest & ((gold.sum(1) >= 2) | (white.sum(1) >= 2))
print('vest', int(vest.sum()), 'gold', int((vest & (gold.sum(1) >= 2)).sum()), 'white', int((vest & (white.sum(1) >= 2)).sum()))
vf = {}
for i, t in enumerate(f):
    for v in t:
        vf.setdefault(v, []).append(i)
for _ in range(int(os.environ.get('REA_RINGS', '1'))):
    vs = np.unique(f[paint]); grow = np.zeros(len(f), bool)
    for v in vs:
        grow[vf[v]] = True
    paint |= grow & vest
np.save('work/vest_paint.npy', paint); print('VEST PAINT kept', int(paint.sum()), 'of', int(vest.sum()))
