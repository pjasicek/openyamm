"""Compare every installed design with its icon and four culling-enabled model views."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[1]
owned = json.loads((P / 'ownership.json').read_text())
for family, batch in [('amulets', 5), ('gauntlets', 6)]:
    entries = [e for e in owned if e['family'] == family]
    assert len(entries) == (20 if family == 'amulets' else 18)
    for start in range(0, len(entries), batch):
        sheet = Image.new('RGB', (1500, batch * 260), (31, 34, 40))
        draw = ImageDraw.Draw(sheet)
        for row, entry in enumerate(entries[start:start + batch]):
            icon = entry['icon']
            draw.text((4, row * 260 + 3), icon + ' ' + entry['items'][0]['name'], fill='white')
            paths = [P / 'references/icons' / f'{icon}.png']
            paths += [P / 'review/finished' / f'{icon}_{view}.png'
                      for view in ['above', 'three_quarter', 'low', 'underside']]
            for column, path in enumerate(paths):
                picture = Image.open(path).convert('RGBA')
                picture.thumbnail((290, 235))
                sheet.paste(picture, (column * 300 + (300 - picture.width) // 2,
                                     row * 260 + 25 + (235 - picture.height) // 2), picture)
        sheet.save(P / 'review' / f'{family}_finished_{start // batch + 1}.png')
