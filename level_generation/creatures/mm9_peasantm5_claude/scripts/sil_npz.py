"""Silhouette overlay of two meshes dumped as npz (co, tris; Blender frame, z up, front = -y).
Usage: sil_npz.py A.npz B.npz out.png [labelA labelB]. Red = A only, green = B only, yellow = both."""
import sys
import numpy as np
from PIL import Image, ImageDraw
A, B = np.load(sys.argv[1]), np.load(sys.argv[2])
out = sys.argv[3]; la, lb = (sys.argv[4], sys.argv[5]) if len(sys.argv) > 5 else ('A', 'B')
S = 1000
allp = np.concatenate([A['co'], B['co']]); lo, hi = allp.min(0), allp.max(0); span = (hi - lo).max() * 1.04; c = (lo + hi) / 2
def mask(m, axes):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    h = (m['co'][:, axes[0]] - c[axes[0]]) / span * S + S / 2; v = S / 2 - (m['co'][:, 2] - c[2]) / span * S
    q = np.stack([h, v], 1)
    for t in m['tris']:
        d.polygon([tuple(q[i]) for i in t], fill=255)
    return np.asarray(im) > 0
panels = []
for axes in ((0,), (1,)):
    a, b = mask(A, axes), mask(B, axes)
    rgb = np.full((S, S, 3), 50, np.uint8); rgb[a & ~b] = (230, 40, 40); rgb[b & ~a] = (40, 200, 40); rgb[a & b] = (200, 200, 90)
    panels.append(Image.fromarray(rgb))
sheet = Image.new('RGB', (2 * S, S)); sheet.paste(panels[0], (0, 0)); sheet.paste(panels[1], (S, 0))
ImageDraw.Draw(sheet).text((8, 8), f'red = {la} only, green = {lb} only (front | side)', fill=(255, 255, 255))
sheet.save(out)
