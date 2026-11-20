"""Review sheets: per icon its inventory icon beside its review renders (review/<kind>/<icon>_{high,low}.png), six rows
a sheet, into review/<kind>_sheet_<n>.png.
Usage: python3 -I sheet.py clay|textured <icon> [icon ...]"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ART = os.path.join(REPO, 'design', 'kreegan_world', 'art', 'item_icons')
CELL = 300
ROWS = 6


def fit(image, size):
    image = image.convert('RGBA')
    image = image.crop(image.getbbox())
    image.thumbnail((size, size))
    return image


def main():
    kind, icons = sys.argv[1], sys.argv[2:]
    designs = json.load(open(os.path.join(HERE, 'classification.json')))
    for page in range(0, len(icons), ROWS):
        chunk = icons[page:page + ROWS]
        sheet = Image.new('RGB', (CELL * 3, (CELL + 20) * len(chunk)), (70, 72, 78))
        draw = ImageDraw.Draw(sheet)
        for row, icon in enumerate(chunk):
            y = row * (CELL + 20)
            pictures = [Image.open(os.path.join(ART, designs[icon]['master']))]
            pictures += [Image.open(os.path.join(HERE, 'review', kind, f'{icon}_{view}.png'))
                         for view in ('high', 'low')]
            for column, picture in enumerate(pictures):
                picture = fit(picture, CELL - 12)
                sheet.paste(picture, (column * CELL + (CELL - picture.width) // 2, y + (CELL - picture.height) // 2),
                            picture)
            draw.text((6, y + CELL + 3), icon, fill=(255, 255, 210))
        path = os.path.join(HERE, 'review', f'{kind}_sheet_{page // ROWS + 1}.png')
        sheet.save(path)
        print(path)


main()
