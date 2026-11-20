#!/usr/bin/env python3
"""Side (y, z) and front (x, z) projections of a dumped mesh with a labelled 0.05 grid (flat-shaded triangles, darker
= farther), for picking cut planes by number. Args: <npz> <out png> [px per unit]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); co, tri = d['co'], d['tri']; S = float(sys.argv[3]) if len(sys.argv) > 3 else 700
lo, hi = co.min(0) - 0.05, co.max(0) + 0.05
panels = []
for ax_h, ax_d, flip in ((1, 0, -1), (0, 1, 1)):           # side: horizontal = -y (snout right); front: x
    w = int((hi[ax_h] - lo[ax_h]) * S) + 60; h = int((hi[2] - lo[2]) * S) + 40
    im = Image.new('RGB', (w, h), (235, 235, 235)); dr = ImageDraw.Draw(im)
    X = lambda v: 40 + ((hi[ax_h] - v) if flip < 0 else (v - lo[ax_h])) * S
    Z = lambda v: 20 + (hi[2] - v) * S
    for g in np.arange(np.floor(lo[ax_h] * 20) / 20, hi[ax_h], 0.05):
        dr.line([(X(g), 0), (X(g), h)], fill=(200, 200, 255) if round(g * 20) % 2 else (150, 150, 230))
        if round(g * 20) % 2 == 0:
            dr.text((X(g) + 2, 2), f'{g:+.1f}', fill=(60, 60, 160))
    for g in np.arange(np.floor(lo[2] * 20) / 20, hi[2], 0.05):
        dr.line([(0, Z(g)), (w, Z(g))], fill=(200, 200, 255) if round(g * 20) % 2 else (150, 150, 230))
        if round(g * 20) % 2 == 0:
            dr.text((2, Z(g) + 2), f'{g:+.1f}', fill=(60, 60, 160))
    depth = co[tri].mean(1)[:, ax_d] * (1 if ax_h == 1 else -1)
    for t in np.argsort(-depth if ax_h == 1 else depth):
        P = co[tri[t]]; n = np.cross(P[1] - P[0], P[2] - P[0]); n /= max(np.linalg.norm(n), 1e-12)
        c = int(90 + 140 * abs(n[ax_d]))
        dr.polygon([(X(p[ax_h]), Z(p[2])) for p in P], fill=(c, c, c))
    panels.append(im)
W = sum(p.width for p in panels); H = max(p.height for p in panels)
out = Image.new('RGB', (W, H), (255, 255, 255)); x = 0
for p in panels:
    out.paste(p, (x, 0)); x += p.width
out.save(sys.argv[2]); print('PLOT', out.size)
