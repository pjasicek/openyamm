#!/usr/bin/env python3
"""Labelled sheet of images in rows. Usage: compose_sheet.py <out png> <height> "row label|img1,img2,..." ..."""
import sys
from PIL import Image, ImageDraw
out, h = sys.argv[1], int(sys.argv[2])
rows = []
for spec in sys.argv[3:]:
    label, files = spec.split('|')
    ims = [Image.open(f).convert('RGB') for f in files.split(',')]
    ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    rows.append((label, ims))
W = max(sum(i.width for i in ims) for _, ims in rows)
S = Image.new('RGB', (W, h * len(rows)), (60, 60, 60)); d = ImageDraw.Draw(S)
for r, (label, ims) in enumerate(rows):
    x = 0
    for i in ims:
        S.paste(i, (x, r * h)); x += i.width
    d.rectangle((0, r * h, 8 * len(label) + 10, r * h + 18), fill=(0, 0, 0)); d.text((5, r * h + 3), label, fill=(255, 255, 0))
S.save(out); print('SHEET', out, S.size)
