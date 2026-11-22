#!/usr/bin/env python3
"""Contact sheets of a tour's shots, 2 x 2 each, labelled (A5). Usage: sheet.py <shots dir> <out prefix>"""
import os
import sys

from PIL import Image, ImageDraw

d, pre = sys.argv[1], sys.argv[2]
files = sorted(f for f in os.listdir(d) if f.endswith('.png'))
for k in range(0, len(files), 4):
    tiles = [Image.open(os.path.join(d, f)).convert('RGB') for f in files[k:k + 4]]
    w, h = 760, int(760 * tiles[0].size[1] / tiles[0].size[0])
    sheet = Image.new('RGB', (2 * w, 2 * h), (0, 0, 0))
    for i, (t, f) in enumerate(zip(tiles, files[k:k + 4])):
        t = t.resize((w, h))
        ImageDraw.Draw(t).text((8, 8), f, fill=(255, 255, 0))
        sheet.paste(t, ((i % 2) * w, (i // 2) * h))
    sheet.save('%s_%d.jpg' % (pre, k // 4 + 1), quality=82)
print(len(files))
