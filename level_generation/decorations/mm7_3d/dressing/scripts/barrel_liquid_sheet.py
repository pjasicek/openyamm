#!/usr/bin/env python3
"""Sheet of the open stat barrel 7dec32: native sprite, empty barrel and the seven liquids (row 1-2), every LOD empty
and red-filled (row 3), from barrel_liquid_review.py's renders -> review/7dec32_liquids/sheet.png."""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'review', '7dec32_liquids')
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_dev', 'engine', 'decorations_x2', '7dec32_p2.png')
W, H = 240, 320
COLOURS = ['red', 'yellow', 'blue', 'orange', 'green', 'purple', 'white']
rows = [[('native 7dec32', X2), ('empty (open top)', os.path.join(SRC, 'empty.png'))] +
        [(f'{c} ({s})', os.path.join(SRC, f'liquid_{c}.png')) for c, s in zip(COLOURS[:3], ('Might', 'Accuracy',
                                                                                          'Personality'))],
        [(f'{c} ({s})', os.path.join(SRC, f'liquid_{c}.png')) for c, s in zip(COLOURS[3:], ('Intellect', 'Endurance',
                                                                                          'Speed', 'Luck'))],
        [(f'LOD{k} {kind}', os.path.join(SRC, f'lod{k}_{kind}.png')) for k in range(4) for kind in ('empty', 'red')]]
cols = max(len(r) for r in rows)
sheet = Image.new('RGB', (W * cols, (H + 18) * len(rows)), (255, 255, 255))
draw = ImageDraw.Draw(sheet)
for r, row in enumerate(rows):
    for c, (label, path) in enumerate(row):
        im = Image.open(path).convert('RGBA')
        im = im.crop(im.split()[-1].getbbox())
        s = min(W * 0.92 / im.width, H * 0.92 / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        tile = Image.new('RGBA', (W, H), (110, 110, 120, 255))
        tile.alpha_composite(im, ((W - im.width) // 2, H - im.height - 6))
        sheet.paste(tile.convert('RGB'), (c * W, r * (H + 18) + 18))
        draw.text((c * W + 4, r * (H + 18) + 3), label, fill=(0, 0, 0))
sheet.save(os.path.join(SRC, 'sheet.png'))
print('SHEET', os.path.join(SRC, 'sheet.png'))
