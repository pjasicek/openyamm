#!/usr/bin/env python3
"""Clip strip sheet from glb_frames.py output (<out>.png.list, one image per clip:frame, single view): one row per
clip with its frames side by side, labelled. Args: <list png> <out png> [per row]"""
import sys
from PIL import Image, ImageDraw
rows = [l.split('\t') for l in open(sys.argv[1] + '.list').read().splitlines()]
k = int(sys.argv[3]) if len(sys.argv) > 3 else 3
ims = [(r[0], Image.open(r[1]).convert('RGB')) for r in rows]
w, h = ims[0][1].size
w2, h2 = w // 2, h // 2
n = (len(ims) + k - 1) // k
# two clips per sheet row
cols = 2 * k
sheet = Image.new('RGB', (w2 * cols, h2 * ((n + 1) // 2)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, (lab, im) in enumerate(ims):
    clip, j = divmod(i, k)
    x = (clip % 2) * k + j; y = clip // 2
    sheet.paste(im.resize((w2, h2)), (x * w2, y * h2))
    d.text((x * w2 + 4, y * h2 + 4), lab, fill=(255, 255, 0))
sheet.save(sys.argv[2])
print('STRIPS', sys.argv[2], sheet.size)
