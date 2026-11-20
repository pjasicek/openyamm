"""A labelled contact sheet of a review folder's shots: review/<name>/sheet.jpg.

    python3 level_generation/projects/hesper_out4/make_sheet.py <name> [columns]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parent
folder = PROJECT / 'review' / sys.argv[1]
columns = int(sys.argv[2]) if len(sys.argv) > 2 else 4
shots = sorted(p for p in folder.glob('*.png'))
width = 640
images = []
for path in shots:
    with Image.open(path) as image:
        images.append((path.stem, image.convert('RGB').resize((width, round(width * image.height / image.width)))))
cell_h = max(image.height for _, image in images)
rows = (len(images) + columns - 1) // columns
sheet = Image.new('RGB', (columns * width, rows * cell_h), (16, 14, 20))
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
for k, (label, image) in enumerate(images):
    x, y = (k % columns) * width, (k // columns) * cell_h
    sheet.paste(image, (x, y))
    draw.rectangle((x, y, x + 12 + draw.textlength(label, font=font), y + 26), fill=(0, 0, 0))
    draw.text((x + 6, y + 3), label, font=font, fill=(255, 230, 120))
sheet.save(folder / 'sheet.jpg', quality=88)
print(folder / 'sheet.jpg', len(images))
