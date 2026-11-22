"""Contact sheet: per design its icon beside review renders. python3 -I sheet.py <out.png> <kind> <design> [...]
kind: master (icon + HD painting), plain (icon + painting + clay renders of the build), final (icon + painting + PBR
renders)."""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
CELL = int(os.environ.get('SHEET_CELL', 300))


def tile(path):
    image = Image.new('RGBA', (CELL, CELL), (40, 42, 50, 255))
    if os.path.exists(path):
        source = Image.open(path).convert('RGBA')
        source.thumbnail((CELL - 12, CELL - 12))
        image.alpha_composite(source, ((CELL - source.width) // 2, (CELL - source.height) // 2))
    return image


def main():
    out, kind, names = sys.argv[1], sys.argv[2], sys.argv[3:]
    columns = []
    for name in names:
        icon = DESIGNS[name]['icon_path']
        master = os.path.join(HERE, 'meshy', name, 'references_hd', 'design_painting.png')
        if not os.path.exists(master):
            master = DESIGNS[name]['painting']
        row = [icon, master]
        if kind in ('plain', 'final'):
            prefix = os.path.join(HERE, 'review', kind, name)
            row += [f'{prefix}_{view}.png' for view in ('above', 'three_quarter', 'low')]
        columns.append((name, row))
    width = max(len(row) for _, row in columns) * CELL
    sheet = Image.new('RGBA', (width, len(columns) * (CELL + 22)), (28, 30, 36, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (name, row) in enumerate(columns):
        y = index * (CELL + 22)
        draw.text((6, y + 4), f"{name}  {DESIGNS[name]['title']}", fill=(235, 235, 235, 255))
        for column, path in enumerate(row):
            sheet.alpha_composite(tile(path), (column * CELL, y + 22))
    sheet.convert('RGB').save(out)
    print(out)


main()
