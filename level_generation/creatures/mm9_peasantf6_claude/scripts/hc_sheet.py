#!/usr/bin/env python3
"""Compose head_closeups.py .list files into one labelled sheet, wrapping at COLS cells per row.
Args: <out png> <cell px> <cols> <views comma> <list> [<list> ...]"""
import sys
from PIL import Image, ImageDraw
out, C, COLS, views = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4].split(',')
cells = []
for lf in sys.argv[5:]:
    tag = lf.split('/')[-1].replace('.png.list', '')
    for r in [l.split('\t') for l in open(lf).read().splitlines()]:
        cells += [(f'{tag} {r[0]} {views[i]}', f) for i, f in enumerate(r[1:])]
nr = (len(cells) + COLS - 1) // COLS; S = Image.new('RGB', (COLS * C, nr * (C + 18)), (20, 20, 20)); d = ImageDraw.Draw(S)
for k, (lab, f) in enumerate(cells):
    x, y = (k % COLS) * C, (k // COLS) * (C + 18)
    S.paste(Image.open(f).convert('RGB').resize((C, C)), (x, y + 18)); d.text((x + 4, y + 3), lab, fill=(255, 255, 0))
S.save(out); print('SHEET', out, len(cells))
