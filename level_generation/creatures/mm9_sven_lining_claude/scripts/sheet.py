#!/usr/bin/env python3
"""Grid sheet of review images with labels. Usage: sheet.py <out png> <cols> <cell px> <label=path> [...]"""
import sys
from PIL import Image, ImageDraw

out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = [a.split('=', 1) for a in sys.argv[4:]]
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cell, rows * (cell + 22)), (255, 255, 255))
d = ImageDraw.Draw(sheet)
for k, (label, path) in enumerate(items):
    im = Image.open(path).convert('RGB')
    im.thumbnail((cell, cell))
    x, y = (k % cols) * cell, (k // cols) * (cell + 22)
    sheet.paste(im, (x + (cell - im.width) // 2, y + 22 + (cell - im.height) // 2))
    d.text((x + 4, y + 4), label, fill=(0, 0, 0))
sheet.save(out)
print('SHEET', out, sheet.size)
