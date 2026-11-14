#!/usr/bin/env python3
"""Joins render_check.py's shots into one sheet: python3 sheet.py <out.png> (reads _*.png beside it)."""
import os
import sys

from PIL import Image

out = sys.argv[1]
d = os.path.dirname(out)
row1 = [Image.open(os.path.join(d, f'_{n}.png')) for n in ('front', 'edge', 'quarter')]
row2 = [Image.open(os.path.join(d, f'_{n}.png')) for n in ('head_front', 'head_quarter', 'grip')]
w = max(sum(i.width for i in row1), 560)
sheet = Image.new('RGB', (sum(i.width for i in row1) + 560, 1200), (40, 40, 44))
x = 0
for i in row1:
    sheet.paste(i, (x, 0)); x += i.width
sheet.paste(row2[0].resize((560, 600)), (x, 0))
sheet.paste(row2[1].resize((560, 600)), (x, 600))
sheet = sheet.resize((sheet.width, sheet.height))
sheet.save(out)
row2[2].save(out.replace('.png', '_grip.png'))
for n in ('front', 'edge', 'quarter', 'head_front', 'head_quarter', 'grip'):
    os.remove(os.path.join(d, f'_{n}.png'))
print(out)
