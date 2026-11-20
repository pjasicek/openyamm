#!/usr/bin/env python3
"""Labelled image grid. Usage: sheet.py <out png> <columns> <cell px> <png[=label]> ..."""
import sys
from PIL import Image, ImageDraw
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = [a.split('=', 1) if '=' in a else (a, a.split('/')[-1][:-4]) for a in sys.argv[4:]]
rows = (len(items) + cols - 1) // cols
s = Image.new('RGB', (cols * cell, rows * (cell + 18)), 'white'); dr = ImageDraw.Draw(s)
for k, (p, lab) in enumerate(items):
    im = Image.open(p).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    im = bg.convert('RGB'); im.thumbnail((cell, cell))
    x, y = (k % cols) * cell, (k // cols) * (cell + 18)
    s.paste(im, (x, y + 18)); dr.text((x + 4, y + 3), lab, fill='black')
s.save(out); print('SHEET', out, s.size)
