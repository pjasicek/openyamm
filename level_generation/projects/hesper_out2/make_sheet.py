"""Contact sheet of a review tour: every shot of review/<name>/, labelled, as review/<name>/sheet.jpg.

    python3 level_generation/projects/hesper_out2/make_sheet.py <name> [columns]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parent
name = sys.argv[1]
columns = int(sys.argv[2]) if len(sys.argv) > 2 else 4
folder = PROJECT / 'review' / name
shots = sorted(p for p in folder.glob('*.png'))
width = 640
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
tiles = []
for path in shots:
    with Image.open(path) as image:
        image = image.convert('RGB')
        tiles.append((path.stem, image.resize((width, round(image.height * width / image.width)))))
tile_h = max(t.height for _, t in tiles) + 30
rows = (len(tiles) + columns - 1) // columns
sheet = Image.new('RGB', (columns * width, rows * tile_h), (18, 16, 20))
draw = ImageDraw.Draw(sheet)
for k, (label, tile) in enumerate(tiles):
    x, y = (k % columns) * width, (k // columns) * tile_h
    sheet.paste(tile, (x, y + 30))
    draw.text((x + 8, y + 5), label, font=font, fill=(236, 226, 200))
sheet.save(folder / 'sheet.jpg', quality=88)
print(folder / 'sheet.jpg', len(tiles))
