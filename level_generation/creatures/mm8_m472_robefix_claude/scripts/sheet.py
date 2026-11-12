#!/usr/bin/env python3
"""Tile shots.mjs output into one sheet: one row per view, one column per time, each scaled by --scale.
    sheet.py <prefix> <out.png> --views side,three-quarter --ts 0,0.25,0.5,0.75 [--scale 0.5]"""
import argparse
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument('prefix'); ap.add_argument('out')
ap.add_argument('--views', default='side,three-quarter'); ap.add_argument('--ts', default='0,0.25,0.5,0.75')
ap.add_argument('--scale', type=float, default=0.5); a = ap.parse_args()
views, ts = a.views.split(','), a.ts.split(',')
ims = [[Image.open(f'{a.prefix}_{v}_t{t}.png').convert('RGB') for t in ts] for v in views]
w, h = (int(x * a.scale) for x in ims[0][0].size)
sheet = Image.new('RGB', (w * len(ts), h * len(views)), 'white')
d = ImageDraw.Draw(sheet)
for r, row in enumerate(ims):
    for c, im in enumerate(row):
        sheet.paste(im.resize((w, h), Image.LANCZOS), (c * w, r * h))
        d.text((c * w + 8, r * h + h - 18), f'{views[r]} t={ts[c]}', fill='yellow')
sheet.save(a.out)
