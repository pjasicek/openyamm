#!/usr/bin/env python3
"""grid.py <out.png> <cols> <png> [...]: half-size contact grid of viewer shots; crop=right keeps the right half."""
import os
import sys
from PIL import Image
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
crop = os.environ.get('CROP')
ims = []
for f in files:
    im = Image.open(f)
    if crop == 'right':
        im = im.crop((im.width // 2, 0, im.width, im.height))
    ims.append(im.resize((im.width // 2, im.height // 2)))
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
g = Image.new('RGB', (w * cols, h * rows))
for i, im in enumerate(ims):
    g.paste(im, ((i % cols) * w, (i // cols) * h))
g.save(out)
