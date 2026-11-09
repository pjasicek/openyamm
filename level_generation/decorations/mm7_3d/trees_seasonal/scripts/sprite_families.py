#!/usr/bin/env python3
"""Native x2 sprites of every seasonal family side by side on a grey ground (review/families_sprites.png)."""
import json, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
X2 = os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016')
inv = {d['name']: d for d in json.load(open(os.path.join(HERE, '..', 'inventory.json')))}
FAMILIES = [['7tree13', '7tree14', '7tree15'], ['7tree16', '7tree17', '7tree18'], ['7tree19', '7tree20', '7tree21'],
            ['7tree07', '7tree08', '7tree09'], ['7tree25', 'tree26', 'tree27'], ['7tree22', '7tree24'],
            ['7tree28', '7tree30'], ['tree38', 'tree37', '7tree30']]
CELL = 300
sheet = Image.new('RGB', (CELL * 3, CELL * len(FAMILIES)), (128, 128, 128))
d = ImageDraw.Draw(sheet)
for r, fam in enumerate(FAMILIES):
    for c, name in enumerate(fam):
        e = inv[name]; im = Image.open(os.path.join(X2, e['x2'])).convert('RGBA')
        s = min((CELL - 30) / im.width, (CELL - 30) / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        sheet.paste(im, (c * CELL + (CELL - im.width) // 2, r * CELL + CELL - 10 - im.height), im)
        d.text((c * CELL + 4, r * CELL + 4), f"{name} n={e['count']} sc={e['scale']} {im.size}", fill=(255, 255, 0))
sheet.save(os.path.join(HERE, 'review', 'families_sprites.png'))
