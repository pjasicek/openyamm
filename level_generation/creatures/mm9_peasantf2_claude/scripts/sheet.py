#!/usr/bin/env python3
"""Tile PNGs. Args: <out> <cols> <cell> path[:label] ..."""
import sys
from PIL import Image, ImageDraw
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); names = sys.argv[4:]
rows = (len(names) + cols - 1) // cols
s = Image.new('RGB', (cols * cell, rows * cell), (40, 40, 40))
for i, n in enumerate(names):
    k, _, lab = n.partition(':')
    im = Image.open(k).convert('RGB'); w, h = im.size
    m = min(w, h); im = im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((cell, cell), Image.LANCZOS)
    if lab: ImageDraw.Draw(im).text((5, 5), lab, fill=(255, 255, 0))
    s.paste(im, ((i % cols) * cell, (i // cols) * cell))
s.save(out)
