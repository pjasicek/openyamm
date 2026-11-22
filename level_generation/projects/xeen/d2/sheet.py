#!/usr/bin/env python3
"""A6: contact sheet of a tour folder. sheet.py <dir> <out.jpg> [cols] [width] [first] [last]"""
import os, sys
from PIL import Image, ImageDraw
D, O = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
w = int(sys.argv[4]) if len(sys.argv) > 4 else 640
fs = sorted(f for f in os.listdir(D) if f.endswith('.png'))
if len(sys.argv) > 6:
    fs = fs[int(sys.argv[5]):int(sys.argv[6])]
ims = [Image.open(os.path.join(D, f)).convert('RGB') for f in fs]
h = int(w * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * w, rows * h), (0, 0, 0))
d = ImageDraw.Draw(S)
for k, (f, im) in enumerate(zip(fs, ims)):
    x, y = (k % cols) * w, (k // cols) * h
    S.paste(im.resize((w, h)), (x, y))
    d.text((x + 6, y + 6), f, fill=(255, 255, 0))
S.save(O, quality=85)
