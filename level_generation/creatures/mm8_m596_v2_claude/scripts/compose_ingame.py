#!/usr/bin/env python3
"""Native sprites / installed now / candidate, outdoor and indoor, same cameras; plus the candidate's walk/later
shots. Usage: compose_ingame.py <label> -> review/ingame/compare_walker_<label>.jpg, review/ingame/motion_<label>.jpg"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[1]; C = P.parent; L = sys.argv[1]
M = C / 'mm8_crystal_material_claude/review/ingame'
SPR = {'out': C / 'mm8_m596_claude/review/ingame/out_sprites/front.png', 'in': C / 'mm8_m596_claude/review/ingame/in_sprites/front.png'}
W, H = 960, 540
for name, cols in (('compare_walker', lambda place: [('native sprites', SPR[place]), ('installed now', M / f'full2/{place}_walker/front.png'),
                                                    (f'v2 ({L})', P / f'review/ingame/{L}/{place}_walker/front.png')]),
                   ('motion', lambda place: [(f'v2 {s}', P / f'review/ingame/{L}/{place}_walker/{s}.png') for s in ('front', 'walk', 'later')])):
    sheet = Image.new('RGB', (W * 3, (H + 24) * 2), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    for row, place in enumerate(('out', 'in')):
        for col, (title, path) in enumerate(cols(place)):
            sheet.paste(Image.open(path).convert('RGB').resize((W, H)), (col * W, row * (H + 24) + 24))
            d.text((col * W + 8, row * (H + 24) + 6), f'{place}door: {title}', fill=(255, 255, 255))
    sheet.save(P / f'review/ingame/{name}_{L}.jpg', quality=90)
