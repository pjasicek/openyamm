#!/usr/bin/env python3
"""Contact sheet of the audit renders (three-quarter view): per model one row of LOD0 at 512 px, then LOD1/2/3 as the
player sees them (downscaled to the switch size 450/180/72 and enlarged back with nearest-neighbour), then LOD2 and
LOD3 at full 512 px (texture grain). Usage: sheet.py <split_dir> <out.png> <stem...>"""
import sys

from PIL import Image, ImageDraw

SWITCH = {1: 450, 2: 180, 3: 72}
CELL = 256
split_dir, out, stems = sys.argv[1], sys.argv[2], sys.argv[3:]
columns = ['LOD0', 'LOD1 @450', 'LOD2 @180', 'LOD3 @72', 'LOD2 full', 'LOD3 full']
sheet = Image.new('RGB', (CELL * len(columns) + 170, (CELL + 4) * len(stems) + 24), (120, 120, 128))
draw = ImageDraw.Draw(sheet)
for c, name in enumerate(columns):
    draw.text((170 + c * CELL + 6, 6), name, fill='white')
for r, stem in enumerate(stems):
    y = 24 + r * (CELL + 4)
    draw.text((6, y + CELL // 2), stem, fill='white')
    cells = []
    for level in range(4):
        image = Image.open(f'{split_dir}/{stem}/lod{level}_q34.png').convert('RGBA')
        if level:
            size = SWITCH[level]
            image = image.resize((size, size), Image.LANCZOS).resize((512, 512), Image.NEAREST)
        cells.append(image)
    cells += [Image.open(f'{split_dir}/{stem}/lod{level}_q34.png').convert('RGBA') for level in (2, 3)]
    for c, image in enumerate(cells):
        tile = Image.new('RGBA', image.size, (120, 120, 128, 255))
        tile.alpha_composite(image)
        sheet.paste(tile.convert('RGB').resize((CELL, CELL), Image.LANCZOS), (170 + c * CELL, y))
sheet.save(out)
print(out, sheet.size)
