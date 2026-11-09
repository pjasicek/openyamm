"""Contact sheet of a review tour's shots: review/<name>/sheet.jpg, each shot labelled.

    python3 level_generation/projects/hesper_out3/make_sheet.py <name>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
folder = PROJECT / 'review' / sys.argv[1]
files = sorted(folder.glob('[0-9][0-9]-*.png'))
w, h, columns = 640, 360, 4
sheet = Image.new('RGB', (w * columns, (h + 24) * ((len(files) + columns - 1) // columns)), (18, 16, 22))
draw = ImageDraw.Draw(sheet)
for i, path in enumerate(files):
    x, y = (i % columns) * w, (i // columns) * (h + 24)
    sheet.paste(Image.open(path).convert('RGB').resize((w, h), Image.LANCZOS), (x, y))
    draw.text((x + 6, y + h + 5), path.stem, fill=(235, 230, 240))
sheet.save(folder / 'sheet.jpg', quality=88)
print(folder / 'sheet.jpg', len(files))
