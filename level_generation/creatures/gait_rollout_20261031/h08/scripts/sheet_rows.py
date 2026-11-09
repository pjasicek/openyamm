#!/usr/bin/env python3
"""Sheets of viewer shots written by shots.sh: <out>_<clip>_<view>.png, six phases per row (body cropped).
    sheet_rows.py <shots dir> <out prefix> <clip>:<length> [...]"""
import sys
from pathlib import Path

import os

from PIL import Image, ImageDraw

X0, X1 = (float(v) for v in os.environ.get('CROP_X', '0.25,0.75').split(','))

shots, prefix = Path(sys.argv[1]), sys.argv[2]
for item in sys.argv[3:]:
    clip = item.split(':')[0].lower()
    for view in ('left', 'quarter', 'front', 'rear'):
        tiles = [Image.open(shots / f'{clip}_{view}_{i}.png').convert('RGB') for i in range(6)]
        w0, h0 = tiles[0].size
        box = (int(w0 * X0), int(h0 * 0.05), int(w0 * X1), int(h0 * 0.95))
        tiles = [t.crop(box) for t in tiles]
        w, h = tiles[0].size
        th = 420
        tw = int(w * th / h)
        sheet = Image.new('RGB', (tw * 6, th + 18), 'white')
        for c, t in enumerate(tiles):
            sheet.paste(t.resize((tw, th)), (c * tw, 18))
        ImageDraw.Draw(sheet).text((4, 3), f'{prefix.split("/")[-1]} {clip} {view}: phases 0..5/6', fill='black')
        out = f'{prefix}_{clip}_{view}.png'
        sheet.save(out)
        print(out)
