#!/usr/bin/env python3
"""Before/after sheet from review/texpass_viewer/{before,after}/<tier>_<shot>.png (review-viewer shots, identical
cameras): one row per shot, before | after per tier. Usage: texpass_sheet.py <out.png> <tier,...> <shot,...>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
D = HERE / 'review' / 'texpass_viewer'
out, tiers, shots = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
W, H = 500, 368
s = Image.new('RGB', (W * 2 * len(tiers), H * len(shots)), (30, 30, 30))
for r, shot in enumerate(shots):
    for c, tier in enumerate(tiers):
        for k, stage in enumerate(('before', 'after')):
            im = Image.open(D / stage / f'{tier}_{shot}.png').convert('RGB').resize((W, H), Image.LANCZOS)
            ImageDraw.Draw(im).text((8, 6), f'{tier} {shot} {stage}', fill=(255, 255, 255))
            s.paste(im, ((2 * c + k) * W, r * H))
s.save(HERE / out)
print('SHEET', out, s.size)
