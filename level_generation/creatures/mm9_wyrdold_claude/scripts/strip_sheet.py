#!/usr/bin/env python3
"""Tile frame strips: one row per clip, cols frames. Args: <prefix> <out png> <cell> <n> <clips...>"""
import sys
from PIL import Image, ImageDraw
pre, out, cell, n = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); clips = sys.argv[5:]
W = Image.new('RGB', (cell * n, cell * len(clips)), (40, 40, 40))
for y, c in enumerate(clips):
    for k in range(n):
        im = Image.open(f'review/shots/{pre}_{c}_{k:02d}.png').convert('RGB'); w, h = im.size; m = min(w, h)
        im = im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((cell, cell), Image.LANCZOS)
        if k == 0: ImageDraw.Draw(im).text((4, 4), c, fill=(255, 255, 0))
        W.paste(im, (k * cell, y * cell))
W.save(out)
