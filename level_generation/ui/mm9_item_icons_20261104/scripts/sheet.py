"""Builds review/<name>.png for a list of designs: per design the MM9 original, the current MM9 icon (nearest x2) and
the new x2 icon, in a grid on an inventory-dark background.
Usage: python3 -I sheet.py <name> <id|family> [...]"""
import json
import math
import os
import sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def main():
    designs = json.load(open(os.path.join(HERE, 'designs.json')))
    keys = set(sys.argv[2:])
    chosen = [d for d in designs if str(d['design_id']) in keys or d['family'] in keys]
    blocks = []
    for d in chosen:
        folder = os.path.join(HERE, 'items', str(d['design_id']))
        src = Image.open(os.path.join(folder, 'source_pcx.png')).convert('RGBA').resize((116, 116), Image.NEAREST)
        cur = Image.open(os.path.join(REPO, 'assets_dev/worlds/mm9/icons', f'mm9_item_{d["design_id"]}.png'))
        cur = cur.convert('RGBA').resize((cur.width * 2, cur.height * 2), Image.NEAREST)
        path = os.path.join(folder, 'icon_a_x2.png')
        new = Image.open(path).convert('RGBA') if os.path.exists(path) else None
        blocks.append((d, [src, cur, new]))
    cols = 4
    cw = max(sum((c.width if c else 60) + 12 for c in cells) for _, cells in blocks) + 12
    rows = [blocks[i:i + cols] for i in range(0, len(blocks), cols)]
    heights = [max(max(c.height for c in cells if c) for _, cells in row) + 34 for row in rows]
    sheet = Image.new('RGBA', (cw * cols, sum(heights)), (30, 27, 24, 255))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for row, h in zip(rows, heights):
        for i, (d, cells) in enumerate(row):
            x = i * cw + 8
            draw.text((x, y + 4), f'{d["design_id"]} {d["name"]} [{d["family"]}]', fill=(255, 255, 255))
            for c in cells:
                if c is None:
                    draw.text((x, y + 30), 'MISSING', fill=(255, 80, 80))
                    x += 72
                    continue
                sheet.alpha_composite(c, (x, y + 22 + (h - 34 - c.height) // 2))
                x += c.width + 12
            draw.line((i * cw, y, i * cw, y + h), fill=(70, 62, 52))
        y += h
        draw.line((0, y - 1, sheet.width, y - 1), fill=(70, 62, 52))
    os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    sheet.convert('RGB').save(os.path.join(HERE, 'review', sys.argv[1] + '.png'))
    print(sheet.size)


main()
