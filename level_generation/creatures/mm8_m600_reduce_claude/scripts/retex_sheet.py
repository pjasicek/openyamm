#!/usr/bin/env python3
"""Sheets of review/retex renders: rows = spots, columns = source / reduced per tier. Usage: retex_sheet.py <out> <spot,...>"""
import sys
from PIL import Image, ImageDraw
out, spots = sys.argv[1], sys.argv[2].split(',')
cols = [(l, t) for t in 'abc' for l in ('src', 'r55')]; S = 260
sh = Image.new('RGB', (S * len(cols), 20 + S * len(spots)), (20, 20, 20)); d = ImageDraw.Draw(sh)
for j, (l, t) in enumerate(cols):
    d.text((j * S + 6, 4), f'{t.upper()} {"installed" if l == "src" else "reduced"}', fill=(255, 230, 120))
for i, s in enumerate(spots):
    for j, (l, t) in enumerate(cols):
        sh.paste(Image.open(f'review/retex/{l}_{t}_{s}.png').convert('RGB').resize((S, S)), (j * S, 20 + i * S))
    d.text((4, 24 + i * S), s, fill=(255, 255, 255))
sh.save(out); print('SHEET', out)
