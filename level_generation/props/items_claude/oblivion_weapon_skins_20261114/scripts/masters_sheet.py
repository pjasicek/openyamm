#!/usr/bin/env python3
"""Contact sheet of Codex masters next to their references (README.md step 2). Usage: masters_sheet.py <out.jpg> <dir>..."""
import os
import sys

from PIL import Image

out, dirs = sys.argv[1], sys.argv[2:]
cells = []
for d in dirs:
    row = [os.path.join(d, 'reference_front.png')] + sorted(os.path.join(d, f) for f in os.listdir(d)
                                                            if f[:3] in ('01_', '02_', '03_', '04_') and '_' not in f[3:])
    cells.append(row)
w, h = 256, 384
cols = max(len(r) for r in cells)
sheet = Image.new('RGB', (w * cols, h * len(cells)), (60, 60, 64))
for y, row in enumerate(cells):
    for x, path in enumerate(row):
        im = Image.open(path).convert('RGBA').resize((w, h), Image.LANCZOS)
        sheet.paste(im, (x * w, y * h), im)
sheet.save(out, quality=90)
