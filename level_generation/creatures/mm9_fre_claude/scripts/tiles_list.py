#!/usr/bin/env python3
"""Contact sheet from a clay_close.py .list file. Args: <list> <out png> [tile px]"""
import sys
from PIL import Image, ImageDraw
rows = [l.split('\t') for l in open(sys.argv[1]).read().splitlines() if l.strip()]
S = int(sys.argv[3]) if len(sys.argv) > 3 else 300
W = max(len(r) - 1 for r in rows)
sh = Image.new('RGB', (S * W, S * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, r in enumerate(rows):
    for j, f in enumerate(r[1:]):
        sh.paste(Image.open(f).convert('RGB').resize((S, S)), (j * S, i * S))
    d.text((4, i * S + 4), r[0], fill=(255, 255, 0))
sh.save(sys.argv[2]); print('SHEET', sys.argv[2])
