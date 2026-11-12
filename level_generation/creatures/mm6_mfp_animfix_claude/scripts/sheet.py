#!/usr/bin/env python3
"""Compose render_clip.py tiles (<prefix>_<clip>__<view>__<i>.png) into <prefix>_<clip>.png (rows = views) and
delete the tiles.  sheet.py <prefix> <clip> [<clip> ...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

prefix = Path(sys.argv[1])
for clip in sys.argv[2:]:
    tiles = sorted(prefix.parent.glob(f'{prefix.name}_{clip}__*__*.png'))
    rows = {}
    for t in tiles:
        view, i = t.stem.split('__')[1:]
        rows.setdefault(view, []).append(t)
    images = [[Image.open(t).convert('RGB') for t in sorted(v)] for v in rows.values()]
    w, h = images[0][0].size
    sheet = Image.new('RGB', (w * max(len(r) for r in images), h * len(images) + 22), 'white')
    for r, row in enumerate(images):
        for c, im in enumerate(row):
            sheet.paste(im, (c * w, 22 + r * h))
    ImageDraw.Draw(sheet).text((6, 4), f'{prefix.name} {clip}', fill='black')
    sheet.save(f'{prefix}_{clip}.png')
    for t in tiles:
        t.unlink()
    print('SHEET', f'{prefix}_{clip}.png')
