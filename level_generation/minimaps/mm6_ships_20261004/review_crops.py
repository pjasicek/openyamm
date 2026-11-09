"""Build native-pixel ship comparisons and map detail sheets from this revision's exports."""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent


def main():
    ships = json.loads((HERE / 'ships.json').read_text())['records']
    panels = []
    details = []
    for ship in ships:
        directory = HERE / 'maps/mm6' / Path(ship['map']).stem
        x0, y0, x1, y1 = ship['x2_bounds']
        bounds = (math.floor(x0) - 16, math.floor(y0) - 16,
                  math.ceil(x1) + 16, math.ceil(y1) + 16)
        before = Image.open(directory / 'previous.png').crop(bounds)
        after = Image.open(directory / 'x2.png').crop(bounds)
        panel = Image.new('RGB', (280, 170), '#20262a')
        draw = ImageDraw.Draw(panel)
        draw.text((4, 4), f"{ship['map']} - {ship['service']}", fill='white')
        draw.text((4, 23), 'Before', fill='white')
        draw.text((144, 23), 'Current', fill='white')
        panel.paste(before, (4, 43))
        panel.paste(after, (144, 43))
        panels.append(panel)
        master_bounds = tuple(value * 2 for value in bounds)
        detail = Image.open(directory / 'master.png').crop(master_bounds)
        details.append((ship, detail))
    sheet = Image.new('RGB', (840, 680), '#20262a')
    for i, panel in enumerate(panels):
        sheet.paste(panel, (i % 3 * 280, i // 3 * 170))
    sheet.save(HERE / 'ships_before_after.png')
    sheet = Image.new('RGB', (900, 1120), '#20262a')
    draw = ImageDraw.Draw(sheet)
    for i, (ship, detail) in enumerate(details):
        x, y = i % 3 * 300, i // 3 * 280
        draw.text((x + 4, y + 4), f"{ship['map']} - {ship['service']}", fill='white')
        sheet.paste(detail, (x + 4, y + 26))
    sheet.save(HERE / 'ships_master_detail.png')
    scope = json.loads((HERE / 'scope.json').read_text())['records']
    for page in range(3):
        sheet = Image.new('RGB', (1000, 800), '#20262a')
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(scope[page * 5:(page + 1) * 5]):
            x, y = i % 3 * 332, i // 3 * 400
            draw.text((x + 4, y + 4), row['map'] + ' - ' + row['name'], fill='white')
            image = Image.open(HERE / row['directory'] / 'x2.png')
            sheet.paste(image.crop((352, 352, 672, 672)), (x + 4, y + 28))
        sheet.save(HERE / f'map_detail_{page + 1}.png')


if __name__ == '__main__':
    main()
