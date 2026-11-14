#!/usr/bin/env python3
"""Composite the view-model renders over a 1600x900 scene; a labelled sheet.

python3 compose_claws.py <render_dir> <background.jpg> <sheet.jpg> [columns]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

renders, background, sheet = Path(sys.argv[1]), Image.open(sys.argv[2]).convert('RGB'), Path(sys.argv[3])
columns = int(sys.argv[4]) if len(sys.argv) > 4 else 3
background = background.resize((800, 450))
tiles = []
for path in sorted(renders.glob('*.png')):
    if path.name.startswith('comp_'):
        continue
    frame = Image.open(path).convert('RGBA')
    composite = background.copy().convert('RGBA')
    composite.alpha_composite(frame.resize(composite.size))
    composite = composite.convert('RGB')
    composite.save(renders / f'comp_{path.stem}.jpg', quality=88)
    draw = ImageDraw.Draw(composite)
    draw.rectangle((0, 0, 260, 22), fill=(0, 0, 0))
    draw.text((6, 5), path.stem, fill=(255, 240, 200))
    tiles.append(composite)
rows = (len(tiles) + columns - 1) // columns
out = Image.new('RGB', (800 * columns, 450 * rows), (20, 20, 20))
for index, tile in enumerate(tiles):
    out.paste(tile, ((index % columns) * 800, (index // columns) * 450))
out.save(sheet, quality=85)
print(sheet, len(tiles))
