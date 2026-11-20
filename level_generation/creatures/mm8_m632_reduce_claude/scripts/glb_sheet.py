#!/usr/bin/env python3
"""Sheet of review/glbclose renders: columns = spots, rows = label x mode. Usage: glb_sheet.py <out.png> <labels> <spots> [modes]"""
import sys
from PIL import Image, ImageDraw
out, labels, spots = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
modes = sys.argv[4].split(',') if len(sys.argv) > 4 else ['tex', 'clay']
S = 300; rows = [(l, m) for m in modes for l in labels]
sheet = Image.new('RGB', (S * len(spots), 20 + S * len(rows)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for j, s in enumerate(spots):
    d.text((j * S + 6, 4), s, fill=(255, 230, 120))
    for i, (l, m) in enumerate(rows):
        sheet.paste(Image.open(f'review/glbclose/{l}_{s}_{m}.png').convert('RGB').resize((S, S)), (j * S, 20 + i * S))
        d.text((j * S + 6, 24 + i * S), f'{l} {m}', fill=(255, 255, 255))
sheet.save(out); print('SHEET', out)
