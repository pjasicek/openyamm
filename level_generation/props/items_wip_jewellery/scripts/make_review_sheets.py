"""Make labelled comparison sheets; images are review evidence, never texture sources."""
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
mode = sys.argv[1]
assert mode in ('baseline', 'replacement')
rows = json.loads((PROJECT / 'ownership.json').read_text())
for family in ('gems', 'rings', 'belts'):
    entries = [r for r in rows if r['family'] == family]
    for start in range(0, len(entries), 10):
        group = entries[start:start + 10]
        sheet = Image.new('RGB', (900, 210 * len(group)), (36, 39, 45))
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(group):
            icon = row['icon']
            y = index * 210
            draw.text((8, y + 5), icon + '  ' + row['names'][0], fill='white')
            paths = [ROOT / 'assets_dev/engine/icons_x2' / (icon + '.png')]
            paths += [PROJECT / 'review' / mode / (icon + '_' + v + '.png') for v in ('above', 'low')]
            for column, path in enumerate(paths):
                if not path.exists():
                    continue
                im = Image.open(path).convert('RGBA')
                im.thumbnail((270, 175))
                sheet.paste(im, (column * 300 + (300 - im.width) // 2, y + 28), im)
        sheet.save(PROJECT / 'review' / f'{mode}_{family}_{start // 10 + 1:02}.jpg', quality=94)
