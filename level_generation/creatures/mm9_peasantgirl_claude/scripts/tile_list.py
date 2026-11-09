#!/usr/bin/env python3
"""Tile a clay_frames.py .list into one sheet with row labels. Args: <list> <out png> [cell]"""
import sys
from PIL import Image, ImageDraw
rows = [l.split('\t') for l in open(sys.argv[1]).read().splitlines() if l.strip()]
c = int(sys.argv[3]) if len(sys.argv) > 3 else 300
W = Image.new('RGB', (c * (len(rows[0]) - 1), c * len(rows)), (30, 30, 30)); d = ImageDraw.Draw(W)
for r, row in enumerate(rows):
    for k, f in enumerate(row[1:]): W.paste(Image.open(f).convert('RGB').resize((c, c)), (k * c, r * c))
    d.text((4, r * c + 4), row[0], fill=(255, 255, 0))
W.save(sys.argv[2]); print('TILED', sys.argv[2])
