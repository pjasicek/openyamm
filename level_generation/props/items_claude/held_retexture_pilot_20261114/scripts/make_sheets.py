#!/usr/bin/env python3
"""Before/after sheet per sword (README.md, "In-game checks"): rows outdoor idle, outdoor swing, outdoor swing 2,
indoor idle, indoor swing; columns before | after, each the whole 1600x900 capture at 2/3 size, plus the ground shot of all four before | after at the bottom.
Usage: python3 -I make_sheets.py   -> review/sheet_<icon>.jpg"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
ICONS = [('item001', 10), ('7item010', 20), ('item005', 30), ('7item012', 40)]
ROWS = [('outdoor', 0, 'idle'), ('outdoor', 1, 'swing'), ('outdoor', 2, 'swing2'), ('indoor', 0, 'idle'),
        ('indoor', 1, 'swing')]
W, H = 1066, 600
for icon, base in ICONS:
    sheet = Image.new('RGB', (2 * W + 10, (len(ROWS) + 1) * (H + 30)), (25, 25, 25))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for place, k, name in ROWS:
        for c, phase in enumerate(('before', 'after')):
            path = os.path.join(PROJECT, 'ingame', phase, place, f'{base + k}_{icon}_{name}.png')
            im = Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS)
            sheet.paste(im, (c * (W + 10), y + 30))
            draw.text((c * (W + 10) + 8, y + 8), f'{icon} {phase} - {place} {name}', fill=(255, 255, 255))
        y += H + 30
    for c, phase in enumerate(('before', 'after')):
        im = Image.open(os.path.join(PROJECT, 'ingame', phase, 'ground', '00_ground.png')).convert('RGB')
        sheet.paste(im.resize((W, H), Image.LANCZOS), (c * (W + 10), y + 30))
        draw.text((c * (W + 10) + 8, y + 8), f'ground (all four) {phase}', fill=(255, 255, 255))
    out = os.path.join(PROJECT, 'review', f'sheet_{icon}.jpg')
    sheet.save(out, quality=90)
    print(out)
