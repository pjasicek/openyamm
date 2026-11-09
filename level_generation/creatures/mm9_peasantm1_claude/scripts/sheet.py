#!/usr/bin/env python3
"""Contact sheet of review/shots PNGs: sheet.py <out png> <cols> <shot name> ... (thumbnails to fit 3000 px wide)"""
import sys
from PIL import Image
out, cols, names = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f'review/shots/{n}.png').convert('RGB') for n in names]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (w * cols, h * rows), (30, 30, 30))
for i, im in enumerate(ims):
    s.paste(im, ((i % cols) * w, (i // cols) * h))
if s.size[0] > 3000:
    s = s.resize((3000, int(s.size[1] * 3000 / s.size[0])), Image.LANCZOS)
s.save(out); print('SHEET', out, s.size)
