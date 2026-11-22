#!/usr/bin/env python3
"""A contact sheet of a tour's shots (two columns, the file name over each). Usage: sheet.py <dir> <out.png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

files = sorted(Path(sys.argv[1]).glob('*.png'))
W = 640
ims = []
for f in files:
    im = Image.open(f).convert('RGB')
    ims.append((f.name, im.resize((W, int(W * im.size[1] / im.size[0])))))
h = ims[0][1].size[1] + 20
rows = (len(ims) + 1) // 2
out = Image.new('RGB', (2 * W, rows * h), (20, 20, 20))
d = ImageDraw.Draw(out)
for k, (name, im) in enumerate(ims):
    x, y = (k % 2) * W, (k // 2) * h
    d.text((x + 6, y + 4), name, fill=(255, 255, 255))
    out.paste(im, (x, y + 20))
out.save(sys.argv[2])
print(sys.argv[2], len(ims))
