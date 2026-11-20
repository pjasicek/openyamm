#!/usr/bin/env python3
"""Sheet of review/glbclose renders: one row per spot, columns <a>_tex, <b>_tex, <a>_clay, <b>_clay.
Usage: pair_sheet.py <a> <b> <out.png> spot [spot ...]"""
import sys
from PIL import Image, ImageDraw
a, b, out, spots = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
S = 300; im = Image.new('RGB', (4 * S, len(spots) * S), (40, 40, 40)); dr = ImageDraw.Draw(im)
for r, spot in enumerate(spots):
    for c, (lab, mode) in enumerate([(a, 'tex'), (b, 'tex'), (a, 'clay'), (b, 'clay')]):
        im.paste(Image.open(f'review/glbclose/{lab}_{spot}_{mode}.png').convert('RGB').resize((S, S)), (c * S, r * S))
        dr.text((c * S + 4, r * S + 4), f'{lab} {spot} {mode}', fill=(255, 255, 0))
im.save(out); print(out)
