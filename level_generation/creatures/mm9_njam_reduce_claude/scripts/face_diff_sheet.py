#!/usr/bin/env python3
"""|installed - reduced| x4 of the five face shots of every tier (review/shots/diff_<tier>_<shot>.png, shot_sheets.py) on one
sheet: the face skin must be black. Usage: face_diff_sheet.py <tag> -> review/sheet_face_diff_<tag>.png"""
import sys
from PIL import Image, ImageDraw
tag = sys.argv[1]; W = 360; H = int(W * 1060 / 1440); shots = ['f0', 'f1', 'f2', 'f3', 'f4']
sh = Image.new('RGB', (W * 5, (H + 18) * 1), (25, 25, 25)); d = ImageDraw.Draw(sh)
for r, t in enumerate(['nj']):
    for i, s in enumerate(shots):
        sh.paste(Image.open(f'review/shots/diff_{t}_{s}.png').convert('RGB').resize((W, H)), (i * W, r * (H + 18) + 18))
        d.text((i * W + 4, r * (H + 18) + 3), f'{t} {s} |installed - {tag}| x4', fill=(255, 220, 120))
sh.save(f'review/sheet_face_diff_{tag}.png')
