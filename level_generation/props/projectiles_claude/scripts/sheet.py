"""Review sheet: per model its restored sprite frame, then the side, three-quarter and tail-on renders of review.py,
cropped to the model -> review/<out>.png.
Usage: python3 -I sheet.py <out> <model>:<sprite file stem> [...]"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SPRITE_DIRS = [os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2'),
               os.path.join(REPO, 'assets_legacy', 'projectiles_x2_20261016')]
CELL = 256
BACKGROUND = (90, 96, 110, 255)


def tile(image):
    canvas = Image.new('RGBA', (CELL, CELL), BACKGROUND)
    canvas.alpha_composite(image, ((CELL - image.width) // 2, (CELL - image.height) // 2))
    return canvas.convert('RGB')


def main():
    out_name, pairs = sys.argv[1], [a.split(':') for a in sys.argv[2:]]
    sheet = Image.new('RGB', (CELL * 4, CELL * len(pairs)), BACKGROUND[:3])
    for row, (model, sprite) in enumerate(pairs):
        path = next(os.path.join(d, sprite + '.png') for d in SPRITE_DIRS
                    if os.path.exists(os.path.join(d, sprite + '.png')))
        image = Image.open(path).convert('RGBA')
        image.thumbnail((CELL, CELL))
        sheet.paste(tile(image), (0, row * CELL))
        for column, view in enumerate(('side', 'three_quarter', 'tail_on')):
            render = Image.open(os.path.join(HERE, 'review', model, view + '.png')).convert('RGBA')
            box = render.getbbox() or (0, 0, render.width, render.height)
            cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
            half = max(box[2] - box[0], box[3] - box[1]) // 2 + 10
            crop = render.crop((cx - half, cy - half, cx + half, cy + half)).resize((CELL, CELL))
            sheet.paste(tile(crop), ((column + 1) * CELL, row * CELL))
        ImageDraw.Draw(sheet).text((4, row * CELL + 4), model, fill=(255, 255, 255))
    sheet.save(os.path.join(HERE, 'review', out_name + '.png'))


main()
