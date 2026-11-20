#!/usr/bin/env python3
"""Sheet of review/glbclose renders: rows spot x mode, columns labels. Usage: glb_sheet.py <out> <labels> <spots> [modes]"""
import sys
from PIL import Image, ImageDraw
out, labels, spots = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
modes = sys.argv[4].split(',') if len(sys.argv) > 4 else ['tex', 'clay']
S = 330; rows = [(s, m) for s in spots for m in modes]
sh = Image.new('RGB', (S * len(labels), 20 + S * len(rows)), (20, 20, 20)); d = ImageDraw.Draw(sh)
for j, l in enumerate(labels):
    d.text((j * S + 6, 4), l, fill=(255, 230, 120))
for i, (s, m) in enumerate(rows):
    for j, l in enumerate(labels):
        sh.paste(Image.open(f'review/glbclose/{l}_{s}_{m}.png').convert('RGB').resize((S, S)), (j * S, 20 + i * S))
    d.text((4, 24 + i * S), f'{s} {m}', fill=(255, 255, 255))
sh.save(out); print('SHEET', out)
