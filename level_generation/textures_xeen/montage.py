#!/usr/bin/env python3
"""Montage of tour pictures: montage.py <out.jpg> <columns> <width> <png>... (labelled with file names)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, cols, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
paths = sys.argv[4:]
ims = []
for p in paths:
    im = Image.open(p).convert('RGB')
    im = im.resize((width, int(im.height * width / im.width)))
    ImageDraw.Draw(im).text((6, 4), Path(p).stem, fill=(255, 255, 0))
    ims.append(im)
h = ims[0].height
sheet = Image.new('RGB', (cols * width, (len(ims) + cols - 1) // cols * h))
for i, im in enumerate(ims):
    sheet.paste(im, (i % cols * width, i // cols * h))
sheet.save(out, quality=88)
