#!/usr/bin/env python3
"""A grid of in-game captures: python3 -I ingame_sheet.py <out.jpg> <width per tile> <dir> [<dir> ...]
(rows: directories; columns: the PNGs in name order)."""
import os
import sys

from PIL import Image

out, w = sys.argv[1], int(sys.argv[2])
rows = []
for d in sys.argv[3:]:
    files = sorted(f for f in os.listdir(d) if f.endswith('.png'))
    rows.append([Image.open(os.path.join(d, f)).convert('RGB') for f in files])
h = int(w * 9 / 16)
cols = max(len(r) for r in rows)
sheet = Image.new('RGB', (cols * w, len(rows) * h), (0, 0, 0))
for y, r in enumerate(rows):
    for x, im in enumerate(r):
        sheet.paste(im.resize((w, h), Image.LANCZOS), (x * w, y * h))
sheet.save(out, quality=85)
print(out)
