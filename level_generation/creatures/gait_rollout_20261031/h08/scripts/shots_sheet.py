#!/usr/bin/env python3
"""Rows of viewer shots (tools/run_creature_review.py shots) per model: review/<m>_shots_<row>.png for the rows
sprint_left, jog_left, sprint_quarter (six phases each) and the arm/feet close-ups. Usage: shots_sheet.py"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
ROWS = {'sprint_left': [f'sprint_left_{i}' for i in range(6)], 'jog_left': [f'jog_left_{i}' for i in range(6)],
        'sprint_quarter': [f'sprint_quarter_{i}' for i in range(6)],
        'closeups': ['sprint_arms_a', 'sprint_arms_b', 'sprint_feet_a', 'jog_feet_a']}
for m in ('ogr', 'kni'):
    shots = HERE.parent / f'mm6_{m}_sprint_claude/review/shots'
    for row, names in ROWS.items():
        tiles = [Image.open(shots / f'{n}.png').convert('RGB') for n in names]
        if row != 'closeups':
            # the body fills the middle of a wide frame: crop to it
            w0, h0 = tiles[0].size
            tiles = [t.crop((int(w0 * 0.3), int(h0 * 0.3), int(w0 * 0.7), int(h0 * 0.92))) for t in tiles]
        w, h = tiles[0].size
        th = 420
        tw = int(w * th / h)
        sheet = Image.new('RGB', (tw * len(tiles), th + 18), 'white')
        for c, t in enumerate(tiles):
            sheet.paste(t.resize((tw, th)), (c * tw, 18))
        ImageDraw.Draw(sheet).text((4, 3), f'{m} {row}: ' + ', '.join(names), fill='black')
        sheet.save(HERE / f'review/{m}_shots_{row}.png')
        print(f'review/{m}_shots_{row}.png')
