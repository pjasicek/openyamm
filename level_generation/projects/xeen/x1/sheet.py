#!/usr/bin/env python3
"""Contact sheet of a folder of PNGs: sheet.py <folder> <out.jpg> [names...] (4 per row, 560 wide each, labelled)."""
import os, sys
from PIL import Image, ImageDraw

D, OUT = sys.argv[1], sys.argv[2]
want = sys.argv[3:]
files = sorted(f for f in os.listdir(D) if f.endswith('.png'))
if want:
    files = [f for f in files if any(w in f for w in want)]
W, H, N = 560, 315, 4
rows = (len(files) + N - 1) // N
sheet = Image.new('RGB', (W * N, H * rows))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(os.path.join(D, f)).convert('RGB').resize((W, H))
    x, y = (i % N) * W, (i // N) * H
    sheet.paste(im, (x, y))
    d.text((x + 6, y + 4), f, fill=(255, 255, 0))
sheet.save(OUT, quality=88)
print(OUT, len(files))
