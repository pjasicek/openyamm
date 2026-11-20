#!/usr/bin/env python3
import sys, os
from PIL import Image, ImageDraw
out = sys.argv[1]
rows = [l.split('\t') for l in open(out + '.list').read().splitlines()]
ims = [[Image.open(f).convert('RGB') for f in r[1:]] for r in rows]
cols = int(sys.argv[2]) if len(sys.argv) > 2 else len(rows)
w, h = ims[0][0].size; nv = len(ims[0])
lines = (len(rows) + cols - 1) // cols
s = Image.new('RGB', (w * nv * cols, h * lines), (40, 40, 40)); d = ImageDraw.Draw(s)
for i, (r, row) in enumerate(zip(rows, ims)):
    for j, im in enumerate(row):
        s.paste(im, ((i % cols) * nv * w + j * w, (i // cols) * h))
    d.text(((i % cols) * nv * w + 6, (i // cols) * h + 6), r[0], fill=(255, 255, 0))
s.save(out)
for r in rows:
    for f in r[1:]: os.remove(f)
print(s.size)
