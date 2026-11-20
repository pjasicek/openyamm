"""Source and four culling-enabled views for every assigned export, in ownership order."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
family = sys.argv[1] if len(sys.argv) > 1 else 'finished'
owned = json.loads((P / 'ownership.json').read_text())
for start in range(0, len(owned), 6):
    sheet = Image.new('RGB', (2000, 1140), (30, 33, 38))
    draw = ImageDraw.Draw(sheet)
    for n, entry in enumerate(owned[start:start + 6]):
        icon = entry['icon']
        y = n * 190
        draw.text((8, y + 5), icon + ' — ' + entry['items'][0]['name'], fill='white')
        source = Image.open(ROOT / entry['icon_reference']).convert('RGBA').rotate(90, expand=True)
        source.thumbnail((390, 145))
        sheet.paste(source, (5, y + 25), source)
        for k, view in enumerate(['above', 'three_quarter', 'low', 'underside']):
            path = P / 'review' / family / (icon + '_' + view + '.png')
            if not path.exists():
                draw.text(((k + 1) * 400 + 5, y + 50), 'PENDING', fill='orange')
                continue
            image = Image.open(path).convert('RGB')
            image.thumbnail((400, 150))
            sheet.paste(image, ((k + 1) * 400, y + 25))
    sheet.save(P / 'review' / (family + '_contact_' + str(start // 6 + 1) + '.png'))
