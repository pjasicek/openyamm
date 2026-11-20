#!/usr/bin/env python3
"""Largest free circle in the body atlas (from uv_xyz.py's dump) and the parts near the neck. Args: <uv npz> [size 2048]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
D = np.load(sys.argv[1])
S = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
im = Image.new('L', (S, S), 0)
d = ImageDraw.Draw(im)
for uv, h, k in zip(D['uv'], D['head'], D['hand']):
    if h or k:
        continue
    d.polygon([(u * S, (1 - v) * S) for u, v in uv], fill=255)
cov = np.asarray(im) > 0
cov = cov.copy()
cov[:2], cov[-2:], cov[:, :2], cov[:, -2:] = True, True, True, True
dist = ndimage.distance_transform_edt(~cov)
y, x = np.unravel_index(dist.argmax(), dist.shape)
print('FREE centre u,v', round(x / S, 4), round(1 - y / S, 4), 'radius px', round(float(dist.max()), 1), 'of', S, 'cover', round(cov.mean(), 3))
c = D['comp']; X = D['xyz']
for k in np.unique(c):
    m = c == k
    if m.sum() > 400 or (D['head'][m].any() or D['hand'][m].any()):
        continue
    p = X[m].reshape(-1, 3)
    print('part', int(k), 'tris', int(m.sum()), 'x', p[:, 0].min().round(3), p[:, 0].max().round(3), 'y', p[:, 1].min().round(3), p[:, 1].max().round(3), 'z', p[:, 2].min().round(3), p[:, 2].max().round(3))
