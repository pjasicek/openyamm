#!/usr/bin/env python3
"""Side-by-side of viewer shots: compare.py <out.png> <scale> <row names,...> <label=pattern with {n}> ..."""
import sys
from PIL import Image, ImageDraw
out, scale, names = sys.argv[1], float(sys.argv[2]), sys.argv[3].split(',')
cols = [a.split('=', 1) for a in sys.argv[4:]]
ims = [[Image.open(p.format(n=n)).convert('RGB') for _, p in cols] for n in names]
w, h = int(ims[0][0].width * scale), int(ims[0][0].height * scale)
c = Image.new('RGB', (w * len(cols), (h + 18) * len(names)), (24, 26, 30)); d = ImageDraw.Draw(c)
for r, row in enumerate(ims):
    for k, im in enumerate(row):
        c.paste(im.resize((w, h)), (k * w, r * (h + 18) + 18)); d.text((k * w + 4, r * (h + 18) + 3), f'{names[r]} {cols[k][0]}', fill=(235, 235, 235))
c.save(out); print('SHEET', out, c.size)
