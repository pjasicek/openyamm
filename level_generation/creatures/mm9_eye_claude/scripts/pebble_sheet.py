#!/usr/bin/env python3
"""Sheet from review/pebble_viewer/<stage>/<tier>_<shot>.png (review-viewer shots, identical cameras): one row per
tier and shot, columns = stages. Usage: pebble_sheet.py <out.png> <tier,...> <shot,...> [stage,...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
D = HERE / 'review' / 'pebble_viewer'
out, tiers, shots = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
stages = sys.argv[4].split(',') if len(sys.argv) > 4 else ['approved', 'texpass', 'restored']
W, H = 620, 456
s = Image.new('RGB', (W * len(stages), H * len(tiers) * len(shots)), (30, 30, 30))
r = 0
for tier in tiers:
    for shot in shots:
        for c, stage in enumerate(stages):
            im = Image.open(D / stage / f'{tier}_{shot}.png').convert('RGB').resize((W, H), Image.LANCZOS)
            draw = ImageDraw.Draw(im)
            draw.rectangle((0, 0, 230, 20), fill=(0, 0, 0))
            draw.text((8, 5), f'{tier} {shot}: {stage}', fill=(255, 255, 255))
            s.paste(im, (c * W, r * H))
        r += 1
s.save(HERE / out)
print('SHEET', out, s.size)
