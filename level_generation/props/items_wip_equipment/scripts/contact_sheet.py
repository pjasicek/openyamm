"""Contact sheets of a family's review renders: per icon its x2 icon, the three-quarter view and the low view, with the
icon name -> review/<family>_sheet_<n>.png (COLUMNS x ROWS icons per sheet).
Usage: python3 -I contact_sheet.py <family> [view view]   (default views: three_quarter low)"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ICONS = os.path.join(REPO, 'assets_dev', 'engine', 'icons_x2')
TILE = 160
COLUMNS, ROWS = 2, 6


def fit(image, size):
    image = image.convert('RGBA')
    image.thumbnail((size, size))
    canvas = Image.new('RGBA', (size, size), (40, 44, 52, 255))
    canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def main():
    family = sys.argv[1]
    views = sys.argv[2:4] if len(sys.argv) >= 4 else ['three_quarter', 'low']
    designs = json.load(open(os.path.join(HERE, 'designs.json')))
    icons = sorted(name for name in designs if os.path.isfile(
        os.path.join(HERE, 'review', family, f'{name}_{views[0]}.png')))
    validation = os.path.join(HERE, 'review', 'final_validation.json')
    if family == 'codex_tex' and os.path.isfile(validation):
        results = json.load(open(validation))
        icons = [name for name in icons if results[name].get('valid')
                 and not results[name].get('external_retained')
                 and all(os.path.isfile(os.path.join(HERE, 'review', family, f'{name}_{view}.png'))
                         and os.path.getmtime(os.path.join(HERE, 'review', family, f'{name}_{view}.png'))
                         >= os.path.getmtime(os.path.join(HERE, 'work', family, f'{name}_export.glb'))
                         for view in views)]
    per_sheet = COLUMNS * ROWS
    cell_w, cell_h = TILE * 3 + 8, TILE + 18
    for sheet in range(0, len(icons), per_sheet):
        chunk = icons[sheet:sheet + per_sheet]
        image = Image.new('RGBA', (COLUMNS * cell_w, ROWS * cell_h), (20, 22, 26, 255))
        draw = ImageDraw.Draw(image)
        for n, icon in enumerate(chunk):
            x, y = (n % COLUMNS) * cell_w, (n // COLUMNS) * cell_h
            tiles = [Image.open(os.path.join(ICONS, designs[icon]['master_icon'] + '.png'))]
            for view in views:
                path = os.path.join(HERE, 'review', family, f'{icon}_{view}.png')
                tiles.append(Image.open(path) if os.path.exists(path) else Image.new('RGBA', (1, 1)))
            for t, tile in enumerate(tiles):
                image.alpha_composite(fit(tile, TILE), (x + t * TILE, y + 16))
            draw.text((x + 2, y + 2), icon, fill=(230, 230, 230, 255))
        out = os.path.join(HERE, 'review', f'{family}_{views[0]}_{views[1]}_sheet_{sheet // per_sheet + 1}.png')
        image.convert('RGB').save(out)
        print(out)


main()
