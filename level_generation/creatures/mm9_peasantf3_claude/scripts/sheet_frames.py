#!/usr/bin/env python3
"""Contact sheet for glb_frames.py output (<out>.png.list): one labelled row per clip:frame. Args: <out png>"""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]
rows = [l.split('\t') for l in open(out + '.list').read().splitlines()]
ims = [[Image.open(f).convert('RGB') for f in r[1:]] for r in rows]
w, h = ims[0][0].size
sheet = Image.new('RGB', (w * max(len(r) for r in ims), h * len(ims)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, (r, row) in enumerate(zip(rows, ims)):
    for j, im in enumerate(row):
        sheet.paste(im, (j * w, i * h))
    d.text((6, i * h + 6), r[0] + ' (48 fps)', fill=(255, 255, 0))
sheet.save(out)
print('SHEET', out, sheet.size)
