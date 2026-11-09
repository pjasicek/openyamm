#!/usr/bin/env python3
"""Tile review-viewer shots into one labelled sheet. Usage: accept_sheet.py <out.png> <cols> <width> <shot.png> ..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, cols, w, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
ims = [Image.open(f).convert('RGB') for f in files]
ims = [i.crop((0, 24, i.width, i.height - 44)) for i in ims]
h = int(ims[0].height * w / ims[0].width)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, (h + 16) * rows), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for k, (im, f) in enumerate(zip(ims, files)):
    x, y = (k % cols) * w, (k // cols) * (h + 16)
    sheet.paste(im.resize((w, h)), (x, y + 16))
    d.text((x + 4, y + 2), Path(f).stem, fill=(255, 230, 150))
sheet.save(out)
