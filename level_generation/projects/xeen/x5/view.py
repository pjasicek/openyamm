#!/usr/bin/env python3
"""A6: a hillshaded height view of the built X5 (export of build/xeen_x5.odm), 8 px a cell, with water, the ground
tiles' kinds (snow white, ice cyan, dirt brown) and contour lines every 500. Usage: view.py <build> <out.png>"""
import json, math, subprocess, sys
from PIL import Image, ImageDraw
B, OUTP = sys.argv[1], sys.argv[2]
subprocess.run(['openyamm-studio/build-xeen/oymap', 'export', B + '/xeen_x5.odm', '--out', B + '/export.json'],
               check=True, stdout=subprocess.DEVNULL)
m = json.load(open(B + '/export.json'))['map']
t = m['terrain']
hm = t['height_map']
H = lambda i, j: hm[max(0, min(127, j)) * 128 + max(0, min(127, i))] * 32
tiles = t.get('tile_map') or []
S = 8
img = Image.new('RGB', (128 * S, 128 * S))
px = img.load()
for j in range(128):
    for i in range(128):
        h = H(i, j)
        dx = H(i + 1, j) - H(i - 1, j); dy = H(i, j + 1) - H(i, j - 1)
        shade = max(0.25, min(1.0, 0.75 - (dx * 0.6 + dy * 0.8) / 1400.0))
        base = (235, 238, 245)
        if tiles:
            tl = tiles[j * 128 + i]
        g = min(1.0, h / 4000.0)
        c = tuple(int(b * shade * (0.75 + 0.25 * g)) for b in base)
        if h <= 0:
            c = (30, 40, 90)
        for y in range(S):
            for x in range(S):
                px[i * S + x, j * S + y] = c
d = ImageDraw.Draw(img)
for j in range(128):
    for i in range(127):
        for lvl in range(500, 4500, 500):
            if (H(i, j) < lvl) != (H(i + 1, j) < lvl):
                d.line([((i + 1) * S, j * S), ((i + 1) * S, (j + 1) * S)], fill=(200, 80, 40) if lvl % 1000 == 0 else (150, 110, 90))
for j in range(127):
    for i in range(128):
        for lvl in range(500, 4500, 500):
            if (H(i, j) < lvl) != (H(i, j + 1) < lvl):
                d.line([(i * S, (j + 1) * S), ((i + 1) * S, (j + 1) * S)], fill=(200, 80, 40) if lvl % 1000 == 0 else (150, 110, 90))
for b in m.get('bmodels', []):
    vs = b['vertices']
    if not vs: continue
    xs = [(v[0] / 512 + 64) * S for v in vs]; ys = [(64 - v[1] / 512) * S for v in vs]
    d.rectangle([min(xs), min(ys), max(xs), max(ys)], outline=(255, 140, 0))
for k in range(0, 128, 8):
    d.text((k * S + 1, 1), str(k), fill=(0, 0, 0)); d.text((1, k * S + 1), str(k), fill=(0, 0, 0))
img.save(OUTP)
print('ok', list(t.keys())[:12])
