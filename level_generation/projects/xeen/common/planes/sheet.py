#!/usr/bin/env python3
"""Contact sheet of a tour folder: sheet.py <folder> <out.jpg> [columns]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

d, out = Path(sys.argv[1]), sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
files = sorted(d.glob('*.png'))
W = 560
thumbs = []
for f in files:
    im = Image.open(f).convert('RGB')
    h = int(im.height * W / im.width)
    im = im.resize((W, h))
    ImageDraw.Draw(im).text((8, 6), f.stem, fill=(255, 255, 0))
    thumbs.append(im)
H = max(t.height for t in thumbs)
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * W, rows * H), (0, 0, 0))
for i, t in enumerate(thumbs):
    sheet.paste(t, ((i % cols) * W, (i // cols) * H))
sheet.save(out, quality=85)
print(out, sheet.size)
