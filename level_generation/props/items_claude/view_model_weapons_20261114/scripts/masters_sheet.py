#!/usr/bin/env python3
"""Contact sheet of a kind's tier masters over a grey ground: python3 -I masters_sheet.py <kind> <out.png> [tiers]"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
kind, out = sys.argv[1], sys.argv[2]
tiers = sys.argv[3].split(',') if len(sys.argv) > 3 else ['1', '2', '3', '4']
tiles = []
for t in tiers:
    d = os.path.join(PROJECT, 'work', kind, f'masters_t{t}')
    for f in sorted(os.listdir(d)):
        if f[:2].isdigit() and f.endswith('.png') and 'attempt' not in f and 'unselected' not in f:
            im = Image.open(os.path.join(d, f)).convert('RGBA')
            im = im.resize((int(im.width * 700 / im.height), 700))
            tiles.append(im)
sheet = Image.new('RGB', (sum(i.width for i in tiles), 700), (70, 70, 78))
x = 0
for im in tiles:
    sheet.paste(im, (x, 0), im)
    x += im.width
sheet.save(out)
print(out, len(tiles))
