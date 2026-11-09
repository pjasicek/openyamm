#!/usr/bin/env python3
"""Full-resolution crops of viewer shots, installed | reduced side by side, per tier rows.
Usage: crop_pairs.py <shots dir under review/> <out png> <shot>:<x0>,<y0>,<x1>,<y1> ... (fractions of the image)"""
import sys
from PIL import Image, ImageDraw
d, out = sys.argv[1:3]; specs = sys.argv[3:]
rows = []
for t in 'ab':
    for s in specs:
        name, box = s.split(':'); x0, y0, x1, y1 = map(float, box.split(','))
        pair = []
        for k in ('inst', 'red'):
            im = Image.open(f'review/{d}/{k}_{t}/{name}.png').convert('RGB'); W, H = im.size
            pair.append(im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))))
        rows.append((f'{t} {name}', pair))
w = max(p[0].width for _, p in rows); h = sum(p[0].height + 18 for _, p in rows)
sh = Image.new('RGB', (2 * w + 6, h), (25, 25, 25)); dr = ImageDraw.Draw(sh); y = 0
for lab, (a, b) in rows:
    dr.text((4, y + 2), f'{lab} installed | reduced', fill=(255, 220, 120)); sh.paste(a, (0, y + 18)); sh.paste(b, (w + 6, y + 18)); y += a.height + 18
sh.save(out); print('CROPS', out, sh.size)
