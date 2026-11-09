#!/usr/bin/env python3
"""Native sprites / installed before / candidate in-game sheets per creature, outdoor and indoor, same cameras.
Usage: compose_ingame.py <candidate label> -> review/ingame/compare_<creature>_<label>.jpg"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
project = Path(__file__).resolve().parents[1]; creatures = project.parent; label = sys.argv[1]
SPRITES = {'dragon': {'out': creatures / 'mm8_m548_codex/review/ingame/out_sprites/front.png',
                      'in': creatures / 'mm8_m548_codex/review/ingame/in_far_sprites/front.png'},
           'walker': {'out': creatures / 'mm8_m596_claude/review/ingame/out_sprites/front.png',
                      'in': creatures / 'mm8_m596_claude/review/ingame/in_sprites/front.png'}}
for creature, sprites in SPRITES.items():
    W, H = 960, 540
    sheet = Image.new('RGB', (W * 3, (H + 24) * 2), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    for row, place in enumerate(('out', 'in')):
        cells = [('native sprites', sprites[place]),
                 ('installed before', project / f'review/ingame/before/{place}_{creature}/front.png'),
                 (f'candidate: {label}', project / f'review/ingame/{label}/{place}_{creature}/front.png')]
        for col, (title, path) in enumerate(cells):
            im = Image.open(path).convert('RGB').resize((W, H))
            sheet.paste(im, (col * W, row * (H + 24) + 24)); d.text((col * W + 8, row * (H + 24) + 6),
                                                                  f'{place}door: {title}', fill=(255, 255, 255))
    out = project / f'review/ingame/compare_{creature}_{label}.jpg'; sheet.save(out, quality=90); print(out)
