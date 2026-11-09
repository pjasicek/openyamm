#!/usr/bin/env python3
"""Compose a clay_sheet.py rows.json ([[clip, [png, ...]], ...]) into one labelled sheet. Args: <rows.json> <out.png>"""
import json, sys
from PIL import Image, ImageDraw
rows = json.load(open(sys.argv[1]))
W, H = Image.open(rows[0][1][0]).size
n = max(len(r[1]) for r in rows)
s = Image.new('RGB', (W * n, H * len(rows)), 'white'); d = ImageDraw.Draw(s)
for y, (c, ims) in enumerate(rows):
    for x, p in enumerate(ims):
        s.paste(Image.open(p).convert('RGB'), (x * W, y * H))
    d.text((4, y * H + 4), c, fill=(200, 0, 0))
s.save(sys.argv[2]); print('SHEET', sys.argv[2], s.size)
