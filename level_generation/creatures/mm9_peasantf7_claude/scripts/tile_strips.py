#!/usr/bin/env python3
"""Tile strip frames <dir>/<prefix><clip>_<k>.png: one row per clip, a label per row. Args: <dir> <prefix> <out> <cell> <n> <clip[=label]>..."""
import sys
from PIL import Image, ImageDraw
d, pre, out, cell, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]); clips = sys.argv[6:]
W = Image.new('RGB', (cell * n, cell * len(clips)), (40, 40, 40)); dr = ImageDraw.Draw(W)
for r, c in enumerate(clips):
    c, lab = (c.split('=') + [c])[:2]
    for k in range(n):
        im = Image.open(f'{d}/{pre}{c}_{k:02d}.png').convert('RGB'); w, h = im.size; m = min(w, h)
        im = im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((cell, cell))
        W.paste(im, (k * cell, r * cell))
    dr.text((4, r * cell + 4), lab, fill=(255, 255, 0))
W.save(out); print('SHEET', out)
