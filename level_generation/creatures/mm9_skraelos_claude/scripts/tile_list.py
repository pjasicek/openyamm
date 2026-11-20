#!/usr/bin/env python3
"""Tile a clay_frames .list into one sheet: each clip a block of its views, blocks in COLS columns, labelled. Args: <list> <out> [cell] [cols]"""
import sys
from PIL import Image, ImageDraw
lst, out = sys.argv[1:3]; cell = int(sys.argv[3]) if len(sys.argv) > 3 else 300; cols = int(sys.argv[4]) if len(sys.argv) > 4 else 2
rows = [l.rstrip('\n').split('\t') for l in open(lst) if l.strip()]
nv = max(len(r) - 1 for r in rows); bw = cell * nv; nr = (len(rows) + cols - 1) // cols
S = Image.new('RGB', (bw * cols, cell * nr), (40, 40, 40)); d = ImageDraw.Draw(S)
for i, r in enumerate(rows):
    x0 = (i // nr) * bw; y0 = (i % nr) * cell
    for j, f in enumerate(r[1:]):
        S.paste(Image.open(f).convert('RGB').resize((cell, cell)), (x0 + j * cell, y0))
    d.text((x0 + 4, y0 + 4), r[0], fill=(255, 255, 0))
S.save(out); print(out, S.size)
