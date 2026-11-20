#!/usr/bin/env python3
"""Contact sheet of retex_views.py renders: rows = spots, columns = label x tier.
Usage: retex_sheet.py <out.png> <label,...> <tiers> <spot,...> [cell px]"""
import sys
from PIL import Image, ImageDraw
out, labels, tiers, spots = sys.argv[1], sys.argv[2].split(','), sys.argv[3], sys.argv[4].split(',')
S = int(sys.argv[5]) if len(sys.argv) > 5 else 300
cols = [(t, l) for t in tiers for l in labels]
sheet = Image.new('RGB', (S * len(cols) + 90, 20 + S * len(spots)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for j, (t, l) in enumerate(cols):
    d.text((90 + j * S + 6, 4), f'{l} {t.upper()}', fill=(255, 230, 120))
for i, s in enumerate(spots):
    d.text((4, 24 + i * S), s, fill=(255, 255, 255))
    for j, (t, l) in enumerate(cols):
        sheet.paste(Image.open(f'review/retex/{l}_{t}_{s}.png').convert('RGB').resize((S, S)), (90 + j * S, 20 + i * S))
sheet.save(out); print('SHEET', out)
