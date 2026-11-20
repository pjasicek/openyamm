#!/usr/bin/env python3
"""Contact grid of images with their file names as captions. Usage: grid.py <out.png> <columns> <cell px> <img...>"""
import os, sys
from PIL import Image, ImageDraw
out, cols, S, paths = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
rows = (len(paths) + cols - 1) // cols
sheet = Image.new('RGB', (cols * S, rows * (S + 16)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for k, p in enumerate(paths):
    x, y = (k % cols) * S, (k // cols) * (S + 16)
    sheet.paste(Image.open(p).convert('RGB').resize((S, S)), (x, y + 16))
    d.text((x + 3, y + 2), os.path.splitext(os.path.basename(p))[0], fill=(255, 230, 120))
sheet.save(out); print('GRID', out, sheet.size)
