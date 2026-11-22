#!/usr/bin/env python3
"""sheet.py <out.jpg> <cols> <width> <png...>: a labelled contact sheet."""
import sys, os
from PIL import Image, ImageDraw
out, cols, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
ims = [Image.open(f).convert('RGB') for f in files]
w = width // cols
h = int(w * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, h * rows), 'black')
d = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(files, ims)):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im.resize((w, h)), (x, y))
    d.rectangle([x, y, x + 8 * len(os.path.basename(f)) + 6, y + 16], fill='black')
    d.text((x + 3, y + 2), os.path.basename(f), fill='yellow')
sheet.save(out, quality=85)
