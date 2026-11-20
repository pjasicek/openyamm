#!/usr/bin/env python3
"""Grid of review/close renders, one cell per spot with the labels side by side.
Usage: pair_sheet.py <out.png> <label,...> <mode> <spot,...> [columns]"""
import os, sys
from PIL import Image, ImageDraw
out, labels, mode, spots = sys.argv[1], sys.argv[2].split(','), sys.argv[3], sys.argv[4].split(',')
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 3; S = 240; W = S * len(labels) + 8
rows = (len(spots) + cols - 1) // cols
sheet = Image.new('RGB', (W * cols, rows * (S + 18)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for k, spot in enumerate(spots):
    x0, y0 = (k % cols) * W, (k // cols) * (S + 18)
    d.text((x0 + 4, y0 + 3), f'{spot}: ' + ' | '.join(labels), fill=(255, 230, 120))
    for j, l in enumerate(labels):
        im = Image.open(f'review/{os.environ.get("SHEET_DIR","close")}/{l}_{spot}_{mode}.png').convert('RGB').resize((S, S))
        sheet.paste(im, (x0 + j * S, y0 + 18))
sheet.save(out); print('SHEET', out, sheet.size)
