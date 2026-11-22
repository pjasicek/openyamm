#!/usr/bin/env python3
"""sheet.py <out.jpg> <cols> <width> <png...>: a captioned contact sheet."""
import sys, os
from PIL import Image, ImageDraw
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
h = w * 9 // 16
rows = (len(files) + cols - 1) // cols
S = Image.new('RGB', (cols * w, rows * (h + 16)), (20, 20, 20))
d = ImageDraw.Draw(S)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((w, h))
    x, y = (i % cols) * w, (i // cols) * (h + 16)
    S.paste(im, (x, y + 16))
    d.text((x + 4, y + 2), os.path.basename(f)[:60], fill=(255, 255, 0))
S.save(out, quality=85)
