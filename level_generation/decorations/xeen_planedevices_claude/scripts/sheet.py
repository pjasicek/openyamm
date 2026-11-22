#!/usr/bin/env python3
"""Contact sheet of a tour's captures (half size, two columns, file names as labels).  sheet.py <dir> <out.jpg>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
fs = sorted(Path(sys.argv[1]).glob('*.png'))
ims = [Image.open(f).convert('RGB') for f in fs]
w, h = ims[0].size
W, H = w // 2, h // 2
sheet = Image.new('RGB', (W * 2, H * ((len(ims) + 1) // 2)))
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % 2) * W, (i // 2) * H
    sheet.paste(im.resize((W, H)), (x, y))
    ImageDraw.Draw(sheet).text((x + 10, y + 10), f.stem, fill=(255, 255, 255))
sheet.save(sys.argv[2], quality=85)
print(sys.argv[2], sheet.size)
