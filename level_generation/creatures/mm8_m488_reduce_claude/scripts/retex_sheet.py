#!/usr/bin/env python3
"""Contact sheet of review/retex renders: rows = spots, columns = tier x tag. Usage: retex_sheet.py <out> <spot,...> [tiers] [tags]"""
import sys
from PIL import Image, ImageDraw
out, spots = sys.argv[1], sys.argv[2].split(',')
tiers = sys.argv[3].split(',') if len(sys.argv) > 3 else ['a', 'b', 'c']
tags = sys.argv[4].split(',') if len(sys.argv) > 4 else ['r100', 'r62']
cols = [(t, g) for t in tiers for g in tags]; S = 320
sh = Image.new('RGB', (S * len(cols), 18 + S * len(spots)), (20, 20, 20)); d = ImageDraw.Draw(sh)
for j, (t, g) in enumerate(cols):
    d.text((j * S + 4, 3), f'tier {t} {"installed" if g == "r100" else g}', fill=(255, 230, 120))
for i, s in enumerate(spots):
    for j, (t, g) in enumerate(cols):
        sh.paste(Image.open(f'review/retex/{t}_{g}_{s}.png').convert('RGB').resize((S, S)), (j * S, 18 + i * S))
    d.text((4, 22 + i * S), s, fill=(255, 255, 255))
sh.save(out); print('SHEET', out)
