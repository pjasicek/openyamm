#!/usr/bin/env python3
"""Contact sheet of review/flat renders: one row per spot, one column per label. Usage: pair_sheet.py <mode> <labels,> <spots,> <out.png>"""
import sys
from PIL import Image, ImageDraw
mode, labels, spots, out = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(','), sys.argv[4]
S = 400
sheet = Image.new('RGB', (S * len(labels), (S + 18) * len(spots)), (30, 30, 30)); dr = ImageDraw.Draw(sheet)
for j, sp in enumerate(spots):
    for i, lb in enumerate(labels):
        im = Image.open(f'review/glbclose/{lb}_{sp}_{mode}.png').convert('RGB').resize((S, S))
        sheet.paste(im, (i * S, j * (S + 18) + 18)); dr.text((i * S + 4, j * (S + 18) + 3), f'{lb} {sp} {mode}', fill=(255, 220, 120))
sheet.save(out); print('SHEET', out)
