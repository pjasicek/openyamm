"""Source icon, above render, low render for every owned icon, including retained/deferred items."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]


def main():
    entries = json.loads((PROJECT / 'ownership.json').read_text())
    designs = json.loads((PROJECT / 'designs.json').read_text())
    for start in range(0, len(entries), 18):
        sheet = Image.new('RGB', (1296, 1050), (35, 38, 44))
        draw = ImageDraw.Draw(sheet)
        for j, entry in enumerate(entries[start:start + 18]):
            icon = entry['icon']
            mode = 'revised' if 'props_' + icon in designs else 'baseline'
            x, y = j % 3 * 432, j // 3 * 175
            draw.text((x + 4, y + 3), icon + ' ' + entry['names'][0][:31], fill='white')
            paths = [ROOT / 'assets_dev/engine/icons_x2' / f'{icon}.png']
            paths += [PROJECT / 'review' / mode / f'{icon}_{v}.png' for v in ('above', 'low')]
            for k, path in enumerate(paths):
                if not path.exists():
                    continue
                tile = Image.open(path).convert('RGBA')
                tile.thumbnail((140, 150))
                sheet.paste(tile, (x + k * 144 + (140 - tile.width) // 2,
                                   y + 20 + (150 - tile.height) // 2), tile)
        sheet.save(PROJECT / 'review' / f'comparison_{start // 18 + 1:02}.jpg')
    print('Eight comparison sheets written')


if __name__ == '__main__':
    main()
