"""Builds review/compare.png: per item, the original MM9 PCX, the current MM9 icon (both nearest-enlarged to the x2
scale), the two new candidates at x2, and an MM7/MM8 x2 icon of the same family, on an inventory-dark background.
Usage: python3 -I compare.py"""
import json
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BG = (30, 27, 24)
COL = 220
HEAD = ['MM9 original', 'current MM9 icon', 'new A', 'new B', 'MM7/MM8 reference']


def x2(path):
    image = Image.open(path).convert('RGBA')
    return image.resize((image.width * 2, image.height * 2), Image.NEAREST)


def main():
    items = json.load(open(os.path.join(HERE, 'designs.json')))
    rows = []
    for item in items:
        folder = os.path.join(HERE, 'items', str(item['design_id']))
        cells = [x2(os.path.join(folder, 'source_pcx.png')).resize((116, 116), Image.NEAREST),
                 x2(os.path.join(REPO, 'assets_dev/worlds/mm9/icons', f'mm9_item_{item["design_id"]}.png'))]
        for c in 'ab':
            path = os.path.join(folder, f'icon_{c}_x2.png')
            cells.append(Image.open(path).convert('RGBA') if os.path.exists(path) else None)
        cells.append(Image.open(os.path.join(REPO, 'assets_dev/engine/icons_x2', item['style_refs'][0] + '.png'))
                     .convert('RGBA'))
        rows.append((item, cells))
    width = COL * len(HEAD)
    height = 30 + sum(max(c.height for c in cells if c) + 40 for _, cells in rows)
    sheet = Image.new('RGBA', (width, height), BG + (255,))
    draw = ImageDraw.Draw(sheet)
    for i, h in enumerate(HEAD):
        draw.text((i * COL + 8, 8), h, fill=(230, 210, 160))
    y = 30
    for item, cells in rows:
        tall = max(c.height for c in cells if c)
        draw.text((8, y + 2), f'{item["design_id"]} {item["name"]}', fill=(255, 255, 255))
        for i, cell in enumerate(cells):
            if cell is None:
                continue
            sheet.alpha_composite(cell, (i * COL + (COL - cell.width) // 2, y + 18 + (tall - cell.height) // 2))
        y += tall + 40
        draw.line((0, y - 6, width, y - 6), fill=(70, 62, 52))
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    sheet.convert('RGB').save(os.path.join(HERE, 'review', 'compare.png'))
    print(sheet.size)


main()
