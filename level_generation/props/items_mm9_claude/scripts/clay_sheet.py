"""Clay review sheet: per design its icon and the clay above view and three-quarter view (review/plain/<d>_*.png).
Usage: python3 -I scripts/clay_sheet.py <out.jpg> <design> [...]"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
DESIGNS = json.loads((HERE / 'designs.json').read_text())
CELL = 200
out, names = sys.argv[1], sys.argv[2:]
columns = 4
tiles = []
for name in names:
    row = Image.new('RGB', (CELL * 3, CELL + 14), (40, 42, 50))
    pictures = [DESIGNS[name]['icon_path']] + [HERE / 'review' / 'plain' / f'{name}_{v}.png' for v in ('above', 'three_quarter')]
    for k, path in enumerate(pictures):
        if Path(path).exists():
            image = Image.open(path).convert('RGBA')
            image.thumbnail((CELL - 6, CELL - 6))
            row.paste(image, (k * CELL + (CELL - image.width) // 2, 14 + (CELL - image.height) // 2), image)
    ImageDraw.Draw(row).text((3, 1), f"{name} {DESIGNS[name]['title']}", fill=(255, 255, 0))
    tiles.append(row)
sheet = Image.new('RGB', (CELL * 3 * columns, (CELL + 14) * ((len(tiles) + columns - 1) // columns)), (20, 20, 24))
for k, tile in enumerate(tiles):
    sheet.paste(tile, ((k % columns) * CELL * 3, (k // columns) * (CELL + 14)))
sheet.save(out, quality=85)
print(out)
