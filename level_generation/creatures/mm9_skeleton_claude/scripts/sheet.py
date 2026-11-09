#!/usr/bin/env python3
"""Paste images into a grid. Args: <out png> <columns> <tile px> <images...>"""
import sys
from PIL import Image
out, col, t = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); ims = sys.argv[4:]
r = (len(ims) + col - 1) // col
s = Image.new('RGB', (col * t, r * t), (40, 40, 40))
for i, p in enumerate(ims):
    m = Image.open(p).convert('RGB'); m.thumbnail((t, t)); s.paste(m, ((i % col) * t, (i // col) * t))
s.save(out)
