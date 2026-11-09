#!/usr/bin/env python3
"""Contact sheet of viewer shots. Args: <out png> <cols> <cell px> <png...>"""
import sys
from PIL import Image, ImageDraw
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
rows = (len(fs) + cols - 1) // cols
s = Image.new('RGB', (cols * cell, rows * cell), (30, 30, 30)); d = ImageDraw.Draw(s)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB'); im.thumbnail((cell, cell))
    s.paste(im, ((i % cols) * cell, (i // cols) * cell)); d.text(((i % cols) * cell + 5, (i // cols) * cell + 4), f.split('/')[-1], fill=(255, 255, 0))
s.save(out); print(s.size)
