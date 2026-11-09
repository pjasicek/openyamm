#!/usr/bin/env python3
"""Montage of review/shots. Args: <out> <cols> <cell> names... (names without .png; full paths allowed)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); names = sys.argv[4:]
rows = (len(names) + cols - 1) // cols
s = Image.new('RGB', (cols * cell, rows * cell), (30, 30, 34)); d = ImageDraw.Draw(s)
for i, n in enumerate(names):
    p = Path(n if n.endswith('.png') else f'review/shots/{n}.png')
    im = Image.open(p).convert('RGB'); w, h = im.size
    k = min(cell / w, cell / h); im = im.resize((int(w * k), int(h * k)), Image.LANCZOS)
    x, y = (i % cols) * cell, (i // cols) * cell
    s.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2)); d.text((x + 6, y + 4), p.stem, fill=(255, 240, 120))
s.save(out)
