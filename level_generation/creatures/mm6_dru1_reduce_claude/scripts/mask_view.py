"""Flat depth-sorted view of a per-face mask over the upper body (front from -Y, side from -X).
Usage: python3 scripts/mask_view.py <mask.npy> <out.png> [zmin]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; m = np.load(sys.argv[1])
zmin = float(sys.argv[3]) if len(sys.argv) > 3 else 1.3; s = 600 / (1.75 - zmin)
c = v[f].mean(1); im = Image.new('RGB', (1800, 600), (40, 40, 40)); dr = ImageDraw.Draw(im)
for k, (ax, depth, sign) in enumerate([(0, 1, 1), (1, 0, -1), (0, 1, -1)]):  # front, side, back
    order = np.argsort(-c[:, depth] * (1 if k != 2 else -1)) if k != 1 else np.argsort(c[:, 0])
    for i in order:
        if c[i, 2] < zmin: continue
        xy = [(k * 600 + 300 + sign * p[ax] * s, 600 - (p[2] - zmin) * s) for p in v[f[i]]]
        dr.polygon(xy, fill=(230, 120, 90) if m[i] else (90, 90, 110), outline=(20, 20, 20))
im.save(sys.argv[2])
