#!/usr/bin/env python3
"""Join review renders side by side: sheet_v2.py out.png in1.png in2.png ... (grey background)."""
import sys
from PIL import Image
ims = [Image.open(p).convert('RGBA') for p in sys.argv[2:]]
h = max(i.height for i in ims)
sheet = Image.new('RGBA', (sum(i.width for i in ims), h), (150, 160, 175, 255))
x = 0
for im in ims:
    sheet.alpha_composite(im, (x, h - im.height)); x += im.width
sheet.convert('RGB').save(sys.argv[1])
