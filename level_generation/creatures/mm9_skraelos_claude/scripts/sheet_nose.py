#!/usr/bin/env python3
"""Nose/lip before-after sheet (nose fix 2026-11-02): per tier two rows (before, after) of MM9's face, front close-up, 3/4, side and party
view (22 deg above); viewer shots <before dir>/<t>_<view>.png and <after dir>/<t>_<view>.png, cropped round the head.
Args: <out png> <before dir> <after dir> <tier:mm9 face png>... (project folder)"""
import sys
from PIL import Image, ImageDraw
OUT, BEF, AFT = sys.argv[1:4]; tiers = [a.split(':', 1) for a in sys.argv[4:]]
import os
SIDE = os.environ.get('SIDE_LABEL', 'side'); C = 300; VIEWS = tuple(os.environ.get('VIEWS', 'close,q34,side,party').split(','))
# crop boxes in the 1036x763 viewer shot (centre x, centre y, half size)
BOX = {'close': (518, 381, 330), 'q34': (518, 381, 330), 'side': (518, 381, 330), 'party': (518, 330, 150), 'eye': (518, 381, 381)}
rows = []
for t, mm9 in tiers:
    for lab, d in (('before', BEF), ('after', AFT)):
        row = [Image.open(mm9).convert('RGB').resize((C, C))]
        for v in VIEWS:
            im = Image.open(f'{d}/{t}_{v}.png').convert('RGB'); cx, cy, h = BOX[v]
            row.append(im.crop((cx - h, cy - h, cx + h, cy + h)).resize((C, C), Image.LANCZOS))
        rows.append((f'{t} {lab}', row))
s = Image.new('RGB', (C * (1 + len(VIEWS)), (C + 18) * len(rows)), (30, 30, 30)); dr = ImageDraw.Draw(s)
for r, (lab, row) in enumerate(rows):
    y = r * (C + 18)
    dr.text((4, y + 3), f'{lab}:  MM9 face | ' + ' | '.join({'close': 'front close-up', 'q34': '3/4', 'side': SIDE, 'party': 'party view 22 deg above', 'eye': os.environ.get('EYE_LABEL', 'lower lid close-up')}.get(v, v) for v in VIEWS), fill=(255, 255, 0))
    for i, im in enumerate(row): s.paste(im, (i * C, y + 18))
s.save(OUT); print('SHEET', OUT)
