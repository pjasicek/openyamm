#!/usr/bin/env python3
"""Before/after sheet of mouth_views.py renders: rows = shots, columns = the given render dirs.
Usage: mouth_sheet.py <out.png> <cell px> <shots comma> <label=dir:prefix> ..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

out, cell, shots = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(',')
cols = [a.split('=', 1) for a in sys.argv[4:]]
head = 34
img = Image.new('RGB', (cell * len(cols) + 150, head + cell * len(shots)), (30, 30, 30))
d = ImageDraw.Draw(img)
for c, (label, _) in enumerate(cols):
    d.text((150 + c * cell + 8, 10), label, fill=(240, 240, 240))
for r, shot in enumerate(shots):
    d.text((8, head + r * cell + cell // 2), shot, fill=(240, 240, 240))
    for c, (_, spec) in enumerate(cols):
        folder, prefix = spec.split(':')
        p = Path(folder) / f'{prefix}_{shot}.png'
        if p.exists():
            img.paste(Image.open(p).convert('RGB').resize((cell, cell), Image.LANCZOS), (150 + c * cell, head + r * cell))
img.save(out)
print('SHEET', out)
