#!/usr/bin/env python3
"""Paint a plait into the head set's free column (u 0.82-0.98, v 0.05-0.55; headwear.py maps the DF3 braids there: u
around the braid, v along it). Ginger-blonde strands crossing in a herringbone (8 plaits along the length), darker in
the crossings, matching the d3 fringe's own colour (median of saturated ginger texels on the head shell above the
eyes), with a matching bump in the head normal map. Usage (project folder): braid_paint.py <prefix> [r,g,b]"""
import sys
import numpy as np
from PIL import Image
pre = sys.argv[1]
f = f'textures/{pre}_head_basecolor.png'
img = np.asarray(Image.open(f).convert('RGB'), float).copy(); H, W = img.shape[:2]
base = np.array([float(x) for x in sys.argv[2].split(',')]) if len(sys.argv) > 2 else np.array([196.0, 112.0, 52.0])
u0, v0, u1, v1 = 0.82, 0.05, 0.98, 0.55
x0, x1 = int(u0 * W) - 4, int(u1 * W) + 4; y0, y1 = int((1 - v1) * H) - 4, int((1 - v0) * H) + 4
ys, xs = np.mgrid[y0:y1, x0:x1]
a = (xs + 0.5) / W; b = 1 - (ys + 0.5) / H
s = np.clip((a - u0) / (u1 - u0), 0, 1); t = np.clip((b - v0) / (v1 - v0), 0, 1)     # s around, t along
N = 8.0
ph = (t * N + np.where(np.sin(2 * np.pi * s) > 0, s, 1 - s)) % 1.0                    # herringbone strands
strand = 0.5 + 0.5 * np.cos(2 * np.pi * ph)
lines = 0.5 + 0.5 * np.cos(2 * np.pi * (s * 18 + t * N * 2))                          # fine hair lines
shade = 0.62 + 0.38 * strand ** 0.7
col = base[None, None] * (shade * (0.92 + 0.08 * lines))[..., None]
img[y0:y1, x0:x1] = np.clip(col, 0, 255)
Image.fromarray(np.uint8(img)).save(f)
nf = f'textures/{pre}_head_normal_1k.png'
nm = np.asarray(Image.open(nf).convert('RGB'), float).copy(); n = nm.shape[0]
nx0, nx1, ny0, ny1 = int(x0 * n / W), int(x1 * n / W), int(y0 * n / H), int(y1 * n / H)
yy, xx = np.mgrid[ny0:ny1, nx0:nx1]
tt = np.clip((1 - (yy + 0.5) / n - v0) / (v1 - v0), 0, 1); ss = np.clip(((xx + 0.5) / n - u0) / (u1 - u0), 0, 1)
dz = -np.sin(2 * np.pi * ((tt * N + np.where(np.sin(2 * np.pi * ss) > 0, ss, 1 - ss)) % 1.0)) * 0.35
nm[ny0:ny1, nx0:nx1] = np.stack([np.full_like(dz, 128.0), 128 + dz * 127, np.full_like(dz, 235.0)], -1)
Image.fromarray(np.uint8(np.clip(nm, 0, 255))).save(nf)
print('BRAIDPAINT', pre, base.tolist())
