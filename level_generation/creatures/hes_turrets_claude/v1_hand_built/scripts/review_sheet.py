#!/usr/bin/env python3
"""Join each turret's review renders (scripts/render_review.py) into review/turrets_sheet.png, one row per turret."""
import os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ('rest', 'yaw60_up15', 'ring_closeup', 'attack_shot', 'dead')
rows = []
for name in ('hes_ward_turret_actor', 'hes_gate_bastion_actor'):
    row = Image.new('RGB', (450 * len(VIEWS), 350))
    for i, view in enumerate(VIEWS):
        im = Image.open(os.path.join(HERE, 'review', f'{name}_{view}.png')).convert('RGB').resize((450, 350))
        ImageDraw.Draw(im).text((6, 6), f'{name} {view}', fill='yellow')
        row.paste(im, (i * 450, 0))
    rows.append(row)
sheet = Image.new('RGB', (rows[0].width, 350 * len(rows)))
for i, row in enumerate(rows):
    sheet.paste(row, (0, i * 350))
sheet.save(os.path.join(HERE, 'review', 'turrets_sheet.png'))
print('SHEET', os.path.join(HERE, 'review', 'turrets_sheet.png'))
