#!/usr/bin/env python3
"""Tile named shots: sheet.py <out> <cell> <cols> name ... (review/shots/name.png, centre square, label)"""
import sys
from PIL import Image, ImageDraw
out, cell, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); names = sys.argv[4:]
W = Image.new('RGB', (cell * cols, cell * ((len(names) + cols - 1) // cols)), (40, 40, 40))
for i, n in enumerate(names):
    im = Image.open(f'review/shots/{n}.png').convert('RGB'); w, h = im.size; m = min(w, h)
    im = im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((cell, cell), Image.LANCZOS)
    ImageDraw.Draw(im).text((4, 4), n, fill=(255, 255, 0)); W.paste(im, ((i % cols) * cell, (i // cols) * cell))
W.save(out)
