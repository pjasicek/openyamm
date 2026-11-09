#!/usr/bin/env python3
"""Contact sheet: sheet.py <out.png> <cols> <img>... (images resized to the first one's size; label = file stem)"""
import sys
from PIL import Image, ImageDraw
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (w * cols, h * rows), (20, 20, 20))
for i, (im, f) in enumerate(zip(ims, files)):
    im = im.resize((w, h))
    ImageDraw.Draw(im).text((6, 4), f.rsplit('/', 1)[-1].rsplit('.', 1)[0], fill=(255, 255, 0))
    sh.paste(im, ((i % cols) * w, (i // cols) * h))
sh.save(out)
