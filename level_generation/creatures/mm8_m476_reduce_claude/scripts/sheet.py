#!/usr/bin/env python3
"""Contact sheet: rows = spot x mode, columns = labels. Usage: sheet.py <dir> <out.png> <label,...> <spot,...> [mode,...] [size]"""
import sys
from PIL import Image, ImageDraw
d, out, labels, spots = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4].split(',')
modes = sys.argv[5].split(',') if len(sys.argv) > 5 else ['tex', 'clay']; S = int(sys.argv[6]) if len(sys.argv) > 6 else 300
rows = [(s, m) for s in spots for m in modes]
sh = Image.new('RGB', (S * len(labels), 20 + S * len(rows)), (20, 20, 20)); dr = ImageDraw.Draw(sh)
for j, l in enumerate(labels):
    dr.text((j * S + 6, 4), l, fill=(255, 230, 120))
for i, (s, m) in enumerate(rows):
    for j, l in enumerate(labels):
        sh.paste(Image.open(f'{d}/{l}_{s}_{m}.png').convert('RGB').resize((S, S)), (j * S, 20 + i * S))
    dr.text((4, 24 + i * S), f'{s} {m}', fill=(255, 255, 255))
sh.save(out); print('SHEET', out)
