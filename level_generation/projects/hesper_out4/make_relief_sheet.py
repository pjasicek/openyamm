"""The relief review's before/after contact sheet (2026-10-24): the two hillshades, then each shot of the tour before
and after side by side: review/relief_20261024/before_after.jpg (and a half-size copy).

    python3 level_generation/projects/hesper_out4/make_relief_sheet.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FOLDER = Path(__file__).resolve().parent / 'review/relief_20261024'
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
WIDTH = 640
PAIR = 2 * WIDTH + 12
COLUMNS = 2


def label(draw, x, y, text):
    draw.rectangle((x, y, x + 12 + draw.textlength(text, font=font), y + 26), fill=(0, 0, 0))
    draw.text((x + 6, y + 3), text, font=font, fill=(255, 230, 120))


shots = sorted(p.name for p in (FOLDER / 'before').glob('*.png') if (FOLDER / 'after' / p.name).exists())
cell_h = round(WIDTH * 1080 / 1280)
for path in (FOLDER / 'before' / shots[0],):
    with Image.open(path) as image:
        cell_h = round(WIDTH * image.height / image.width)
shade_h = PAIR // 2
rows = (len(shots) + COLUMNS - 1) // COLUMNS
sheet = Image.new('RGB', (COLUMNS * PAIR + (COLUMNS - 1) * 24, shade_h + 24 + rows * (cell_h + 12)), (16, 14, 20))
draw = ImageDraw.Draw(sheet)
for k, name in enumerate(('hillshade_before.png', 'hillshade_after.png')):
    with Image.open(FOLDER / name) as image:
        sheet.paste(image.convert('RGB').resize((shade_h, shade_h)), (k * (shade_h + 12), 0))
draw.text((2 * (shade_h + 12) + 12, 12), 'The Crown: terrain relief, before | after (2026-10-24)', font=font,
          fill=(255, 230, 120))
for k, name in enumerate(shots):
    x = (k % COLUMNS) * (PAIR + 24)
    y = shade_h + 24 + (k // COLUMNS) * (cell_h + 12)
    for side, which in enumerate(('before', 'after')):
        with Image.open(FOLDER / which / name) as image:
            sheet.paste(image.convert('RGB').resize((WIDTH, cell_h)), (x + side * (WIDTH + 12), y))
        label(draw, x + side * (WIDTH + 12), y, f'{Path(name).stem} ({which})')
sheet.save(FOLDER / 'before_after.jpg', quality=86)
sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS).save(FOLDER / 'before_after_small.jpg', quality=86)
print(FOLDER / 'before_after.jpg', len(shots), sheet.size)
