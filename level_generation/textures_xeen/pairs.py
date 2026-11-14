#!/usr/bin/env python3
"""Before | after pairs of one dungeon's tour: pairs.py <xd0N> <out.jpg> [width] [name filter...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
root = Path(__file__).resolve().parents[2] / 'output/studio_cal' / sys.argv[1] / 'textures_gen'
out, width = sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 520
filters = sys.argv[4:]
names = sorted(p.name for p in (root / 'after').glob('*.png') if not filters or any(f in p.name for f in filters))
rows = []
for name in names:
    pair = []
    for side in ('before', 'after'):
        path = root / side / name
        im = Image.open(path).convert('RGB') if path.exists() else Image.new('RGB', (1600, 900))
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        ImageDraw.Draw(im).text((6, 4), f'{side} {name}', fill=(255, 255, 0))
        pair.append(im)
    rows.append(pair)
h = rows[0][0].height
sheet = Image.new('RGB', (2 * width + 6, len(rows) * (h + 4)), (20, 20, 20))
for i, (a, b) in enumerate(rows):
    sheet.paste(a, (0, i * (h + 4)))
    sheet.paste(b, (width + 6, i * (h + 4)))
sheet.save(out, quality=88)
