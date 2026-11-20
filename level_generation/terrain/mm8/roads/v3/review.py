"""Rebuild the full cobble comparison sheets and bind them to current PNG hashes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
from PIL import ImageDraw
from common import *

F = Path(__file__).resolve().parent
build = json.loads((F / 'build.json').read_text())
for group in ('roads_dirt', 'roads_grey'):
    tiles = [r for r in build['tiles'] if r['family'] == group]
    sheet = Image.new('RGB', (1152, 216 * ((len(tiles) + 2) // 3)), '#202933'); draw = ImageDraw.Draw(sheet)
    for i, record in enumerate(tiles):
        name = record['name']; x, y = i % 3 * 384, i // 3 * 216
        assert sha(F / 'runtime' / (name + '.png')) == record['runtime_sha256']
        draw.text((x + 3, y + 4), name + ' native / x2', fill='white')
        for col, path in enumerate((P / 'references' / (name + '.png'), F / 'runtime' / (name + '.png'))):
            sheet.paste(Image.open(path).convert('RGB').resize((192, 192)), (x + col * 192, y + 24))
    sheet.save(F / (group + '_review.png'))
report = dict(status='offline_candidate_sheets_not_native_acceptance', build_sha256=sha(F / 'build.json'),
              sheets={g + '_review.png': sha(F / (g + '_review.png')) for g in ('roads_dirt', 'roads_grey')},
              remaining=['Controlled native road directions, diagonal networks and camera movement',
                         'Twelve separate desert stepping-stone paths belong to the remaining road set'])
(F / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Refreshed native/candidate sheets for all36 cobble roads')
