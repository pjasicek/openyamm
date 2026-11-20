#!/usr/bin/env python3
"""Pairs of viewer shots: MM9 reference above ours per name. Usage: pair_sheet.py out.png cols prefix_a prefix_b name ..."""
import sys
from PIL import Image, ImageDraw
out, cols, a, b = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
names = sys.argv[5:]
ims = [(Image.open(f'shots/{a}__{n}.png').convert('RGB'), Image.open(f'shots/{b}__{n}.png').convert('RGB')) for n in names]
w, h = ims[0][0].size
w, h = w // 2, h // 2
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (w * cols, (2 * h + 20) * rows), (30, 30, 34))
d = ImageDraw.Draw(S)
for k, ((p, q), n) in enumerate(zip(ims, names)):
    x, y = (k % cols) * w, (k // cols) * (2 * h + 20)
    d.text((x + 6, y + 4), f'{n}: MM9 (top), ours (below)', fill=(255, 255, 255))
    S.paste(p.resize((w, h)), (x, y + 20)); S.paste(q.resize((w, h)), (x, y + 20 + h))
S.save(out)
