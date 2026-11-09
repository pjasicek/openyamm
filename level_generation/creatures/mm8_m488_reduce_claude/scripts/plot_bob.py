#!/usr/bin/env python3
"""Head / pelvis height and lowest foot vertex per viewer frame (48 fps) for walk_heights.py outputs, drawn with PIL.
Usage: plot_bob.py <out.png> <label=json> ...  (first = reference, drawn grey)"""
import json, sys
from PIL import Image, ImageDraw
out, items = sys.argv[1], [a.split('=') for a in sys.argv[2:]]
W, H, M = 1100, 760, 60
img = Image.new('RGB', (W, H), (250, 250, 250)); d = ImageDraw.Draw(img)
cols = [(150, 150, 150), (30, 110, 220), (220, 80, 30), (40, 160, 70)]
data = [(l, json.load(open(f))['samples']['48']) for l, f in items]
n = len(data[0][1]) - 1
panels = [(('B_Head', 'B_Pelvis'), 30, 450, 'head (upper) and pelvis (lower) height, m'), (('L_sole', 'R_sole'), 490, 730, 'lowest left / right foot vertex, m')]
for keys, y0, y1, title in panels:
    vals = [r[k] for _, rows in data for r in rows for k in keys]; lo, hi = min(vals), max(vals); pad = (hi - lo) * .05; lo -= pad; hi += pad
    X = lambda i: M + (W - 2 * M) * i / n; Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    [d.rectangle([X(a), y0, X(b), y1], fill=(255, 230, 190)) for a, b in ((16, 18), (38, 40))]; d.rectangle([M, y0, W - M, y1], outline=(0, 0, 0))
    for f in range(0, n + 1, 4):
        d.line([X(f), y1, X(f), y1 + 4], fill=(0, 0, 0)); d.text((X(f) - 6, y1 + 6), str(f), fill=(0, 0, 0))
    for k in range(6):
        v = lo + (hi - lo) * k / 5; d.text((4, Y(v) - 6), f'{v:.3f}', fill=(0, 0, 0)); d.line([M, Y(v), W - M, Y(v)], fill=(225, 225, 225))
    d.text((M + 4, y0 + 4), title, fill=(0, 0, 0))
    for (lab, rows), c in zip(data, cols):
        for k in keys:
            pts = [(X(i), Y(r[k])) for i, r in enumerate(rows)]
            d.line(pts, fill=c, width=3 if c != cols[0] else 2)
            for p in pts:
                d.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=c)
for j, ((lab, _), c) in enumerate(zip(data, cols)):
    d.rectangle([W - 300, 40 + 18 * j, W - 285, 52 + 18 * j], fill=c); d.text((W - 280, 40 + 18 * j), lab, fill=(0, 0, 0))
d.text((M, H - 18), 'Walking, viewer frames at 48 fps (orange: the installed hitches, frames 16-18 and 38-40)', fill=(0, 0, 0))
img.save(out); print('PLOT', out)
