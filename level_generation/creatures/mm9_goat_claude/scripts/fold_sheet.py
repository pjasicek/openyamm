#!/usr/bin/env python3
"""Before/after sheet of fold_views.py renders: rows are shots, columns before/after (textured, then clay).
Usage: fold_sheet.py <before dir> <after dir> <out.png> <shot> [<shot> ...] [--clay]"""
import sys
from PIL import Image, ImageDraw
args = [a for a in sys.argv[1:] if a != '--clay']
before, after, out, shots = args[0], args[1], args[2], args[3:]
kinds = ['tex', 'clay'] if '--clay' in sys.argv else ['tex']
cols = [(d, k, lbl) for k in kinds for d, lbl in ((before, 'before'), (after, 'after'))]
ims = [[Image.open(f'{d}/{s}_{k}.png').convert('RGB') for d, k, _ in cols] for s in shots]
w, h = ims[0][0].size
sheet = Image.new('RGB', (w * len(cols), (h + 18) * len(shots)), (40, 40, 46))
dr = ImageDraw.Draw(sheet)
for r, (s, row) in enumerate(zip(shots, ims)):
    for c, (im, (_, k, lbl)) in enumerate(zip(row, cols)):
        x, y = c * w, r * (h + 18)
        sheet.paste(im, (x, y + 18))
        dr.text((x + 4, y + 3), f'{s}  {lbl} ({k})', fill=(255, 255, 255))
sheet.save(out)
print('SHEET', out, sheet.size)
