#!/usr/bin/env python3
"""Grid sheet of label pairs per spot: each cell holds <labels> side by side. Usage: grid.py <dir> <out> <label,...> <spot,...> <mode> [cols] [size]"""
import sys
from PIL import Image, ImageDraw
d, out, labels, spots, mode = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4].split(','), sys.argv[5]
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 3; S = int(sys.argv[7]) if len(sys.argv) > 7 else 300
cw = S * len(labels) + 8; rows = (len(spots) + cols - 1) // cols
sh = Image.new('RGB', (cw * cols, (S + 18) * rows), (20, 20, 20)); dr = ImageDraw.Draw(sh)
for i, s in enumerate(spots):
    x, y = (i % cols) * cw, (i // cols) * (S + 18)
    dr.text((x + 4, y + 3), f"{s} {mode}: {' | '.join(labels)}", fill=(255, 230, 120))
    for j, l in enumerate(labels):
        sh.paste(Image.open(f'{d}/{l}_{s}_{mode}.png').convert('RGB').resize((S, S)), (x + j * S, y + 18))
sh.save(out); print('GRID', out)
