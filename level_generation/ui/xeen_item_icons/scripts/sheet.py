"""Review sheet: per target its icon at 1x (halved, as drawn at 640x480) and at 2x, on the inventory's dark parchment
tone, beside an engine icon of the same kind (slot_like) at the same scales.
Usage: python3 -I sheet.py <out.png> [--candidate a] [<key> ...]"""
import os
import sys

import yaml
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ICONS = os.path.join(REPO, 'assets_dev/engine/icons_x2')
BACK = (58, 50, 40)


def main():
    args = sys.argv[1:]
    out = args.pop(0)
    candidate = 'a'
    if '--candidate' in args:
        index = args.index('--candidate')
        candidate = args[index + 1]
        del args[index:index + 2]
    wanted = set(args)
    manifest = yaml.safe_load(open(os.path.join(HERE, 'manifest.yml')))
    cells = []
    for target in manifest['targets']:
        if wanted and target['key'] not in wanted:
            continue
        path = os.path.join(HERE, 'items', target['file'], f'icon_{candidate}_x2.png')
        if not os.path.exists(path):
            continue
        icon = Image.open(path).convert('RGBA')
        ref = Image.open(os.path.join(ICONS, target['slot_like'] + '.png')).convert('RGBA')
        cells.append((target['key'], icon, ref))
    if not cells:
        raise SystemExit('no icons')
    tall = max(max(c[1].height, c[2].height) for c in cells)
    scale = 1.0 if tall <= 300 else 300 / tall
    cell_w = 40 + int(1.5 * scale * max(c[1].width + c[2].width for c in cells)) + 80
    cell_h = int(scale * tall) + 40
    columns = max(1, min(len(cells), 2400 // cell_w))
    rows = (len(cells) + columns - 1) // columns
    sheet = Image.new('RGB', (columns * cell_w, rows * cell_h), BACK)
    draw = ImageDraw.Draw(sheet)
    for index, (name, icon, ref) in enumerate(cells):
        x0 = index % columns * cell_w + 10
        y0 = index // columns * cell_h + 4
        x = x0
        for image in (icon, ref):
            small = image.resize((max(1, image.width // 2), max(1, image.height // 2)), Image.LANCZOS)
            big = image if scale == 1.0 else image.resize((round(image.width * scale), round(image.height * scale)),
                                                          Image.LANCZOS)
            sheet.paste(small, (x, y0), small)
            x += small.width + 8
            sheet.paste(big, (x, y0), big)
            x += big.width + 24
        draw.text((x0, y0 + cell_h - 18), name, fill=(235, 225, 200))
    sheet.save(out)
    print(out, sheet.size, len(cells), 'icons')


main()
