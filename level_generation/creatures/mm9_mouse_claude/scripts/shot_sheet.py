#!/usr/bin/env python3
"""Contact sheet of viewer shots. Usage: shot_sheet.py <out.png> <columns> <shot png> ... (labels from file names)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
W = 640
ims = []
for f in files:
    im = Image.open(f).convert('RGB')
    im = im.resize((W, im.height * W // im.width))
    ImageDraw.Draw(im).text((6, 6), Path(f).stem, fill=(255, 255, 0))
    ims.append(im)
H = ims[0].height
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (W * cols, H * rows), (20, 20, 20))
for k, im in enumerate(ims):
    sh.paste(im, ((k % cols) * W, (k // cols) * H))
sh.save(out)
print('SHEET', out, len(ims))
