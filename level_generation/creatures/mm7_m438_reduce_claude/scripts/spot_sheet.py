#!/usr/bin/env python3
"""Sheet of spot_blend.py renders: one row per spot, labels side by side for 'out' and 'side'.
Usage: spot_sheet.py <dir> <label,...> <n spots> <out.png>"""
import sys
from PIL import Image, ImageDraw
d, labels, n, out = sys.argv[1], sys.argv[2].split(','), int(sys.argv[3]), sys.argv[4]
S = 200; sheet = Image.new('RGB', (S * len(labels) * 2 + 10, n * (S + 16)), (20, 20, 20)); dr = ImageDraw.Draw(sheet)
for i in range(n):
    y = i * (S + 16); dr.text((4, y + 2), f'p{i}: ' + ' | '.join(labels) + '  (out, then side)', fill=(255, 230, 120))
    for k, side in enumerate(('out', 'side')):
        for j, l in enumerate(labels):
            sheet.paste(Image.open(f'{d}/{l}_p{i}_{side}.png').convert('RGB').resize((S, S)), (k * (S * len(labels) + 10) + j * S, y + 16))
sheet.save(out); print('SHEET', out)
