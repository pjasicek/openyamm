#!/usr/bin/env python3
"""Labelled contact grid. Usage: grid.py out.png cols cell 'label=path' ... ; label '-' starts nothing (blank cell)."""
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = [a.split('=', 1) for a in sys.argv[4:]]
rows = (len(items) + cols - 1) // cols
img = Image.new('RGB', (cols * cell, rows * (cell + 18)), (30, 30, 30))
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
except Exception:
    font = ImageFont.load_default()
for i, (lab, path) in enumerate(items):
    x, y = (i % cols) * cell, (i // cols) * (cell + 18)
    if path and path != '-':
        im = Image.open(path).convert('RGB')
        im.thumbnail((cell, cell))
        img.paste(im, (x + (cell - im.width) // 2, y + 18 + (cell - im.height) // 2))
    d.text((x + 4, y + 2), lab, fill=(240, 240, 200), font=font)
img.save(out)
print('GRID', out, img.size)
