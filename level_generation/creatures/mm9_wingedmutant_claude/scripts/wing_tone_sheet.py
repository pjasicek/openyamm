#!/usr/bin/env python3
"""Wing tone acceptance sheet from review-viewer shots (review/shots/wt_{before,after}_<tier>_<shot>.png, taken with
tools/run_creature_review.py at identical cameras): every tier, approved | new for each shot.
Writes review/wing_tone_sheet.png. Usage: wing_tone_sheet.py [shot,shot,...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
D = HERE / 'review' / 'shots'
shots = (sys.argv[1] if len(sys.argv) > 1 else 'side,closeA,back').split(',')
W, H = 620, 457
rows = []
for t in 'abc':
    row = []
    for s in shots:
        for st, label in (('before', 'approved'), ('after', 'new')):
            im = Image.open(D / f'wt_{st}_{t}_{s}.png').convert('RGB').resize((W, H), Image.LANCZOS)
            ImageDraw.Draw(im).rectangle((0, 0, 190, 18), fill=(0, 0, 0))
            ImageDraw.Draw(im).text((6, 4), f'{label}  tier {t.upper()}  {s}', fill=(255, 255, 255))
            row.append(im)
    rows.append(row)
sheet = Image.new('RGB', (W * len(rows[0]), H * 3))
for r, row in enumerate(rows):
    for c, im in enumerate(row):
        sheet.paste(im, (c * W, r * H))
sheet.save(HERE / 'review' / 'wing_tone_sheet.png')
print('SHEET', sheet.size)
