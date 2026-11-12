#!/usr/bin/env python3
"""UV-space review textures from a trial's faces npz: islands in pastel colours with every seam edge drawn as a thick
line, coloured by its visibility (red exposed, orange mid, blue hidden); or (--vis) the per-face visibility.

    seam_texture.py <faces.npz> <out png> [--vis] [--size 2048] [--width 7]
"""
import argparse
import colorsys
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uvlib  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument('faces')
parser.add_argument('out')
parser.add_argument('--vis', action='store_true')
parser.add_argument('--size', type=int, default=2048)
parser.add_argument('--width', type=int, default=7)
args = parser.parse_args()
d = np.load(args.faces)
pos, tri, uv, vis = d['pos'], d['tri'], d['uv'].copy(), d['vis']
uv[..., 1] = 1.0 - uv[..., 1]            # Blender v up -> image rows
S = args.size
img = Image.new('RGB', (S, S), (90, 90, 90))
draw = ImageDraw.Draw(img)
tri_pos = pos[tri]
isl = uvlib.island_ids(uv, tri_pos)
rng = np.random.default_rng(3)
pal = [tuple(int(255 * c) for c in colorsys.hsv_to_rgb(rng.random(), 0.25, 0.95)) for _ in range(isl.max() + 1)]
for t, (f_uv, i) in enumerate(zip(uv, isl)):
    if args.vis:
        v = float(vis[t])
        col = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(0.66 * (1 - v), 0.8, 0.95))
    else:
        col = pal[i]
    draw.polygon([(float(a) * S, float(b) * S) for a, b in f_uv], fill=col)
if not args.vis:
    # seam edges: corners of a face whose edge is a seam
    seam_set = {tuple(sorted(e)): sv for e, sv in zip(d['seams'].tolist(), d['seam_vis'])}
    for f, t in enumerate(tri):
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            sv = seam_set.get((min(a, b), max(a, b)))
            if sv is None:
                continue
            col = (230, 20, 20) if sv >= 0.5 else (245, 150, 20) if sv >= 0.15 else (30, 80, 230)
            p, q = uv[f, k] * S, uv[f, (k + 1) % 3] * S
            draw.line([tuple(p), tuple(q)], fill=col, width=args.width)
img.save(args.out)
