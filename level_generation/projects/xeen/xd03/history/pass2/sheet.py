#!/usr/bin/env python3
"""sheet.py <out.jpg> <cols> <width> <png...>: a contact sheet with file names."""
import sys
from PIL import Image, ImageDraw
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
ims = []
for f in files:
    im = Image.open(f).convert('RGB')
    h = int(im.height * w / im.width)
    ims.append((f.split('/')[-1], im.resize((w, h))))
h = max(i.height for _, i in ims) + 18
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for n, (name, im) in enumerate(ims):
    x, y = (n % cols) * w, (n // cols) * h
    sheet.paste(im, (x, y + 18))
    d.text((x + 4, y + 3), name, fill=(255, 255, 0))
sheet.save(out, quality=88)
