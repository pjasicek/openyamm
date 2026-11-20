#!/usr/bin/env python3
"""Face shots per tier: installed | reduced | |difference| x4 (review/shots, shot_sheets.py diffs).
Usage: face_diff_sheet.py <tag> -> review/sheet_face_diff_<tag>.png"""
import sys
from PIL import Image, ImageDraw
tag = sys.argv[1]; RED = sys.argv[2] if len(sys.argv) > 2 else 'red'; W = 360; H = int(W * 1060 / 1440)
shots = ['f0', 'f1', 'f2', 'f3', 'f4']
sh = Image.new('RGB', (W * 3 * 2, (H + 16) * 3 * 5 // 2 + H), (25, 25, 25)); d = ImageDraw.Draw(sh)
sh = Image.new('RGB', (W * 3, (H + 16) * 15), (25, 25, 25)); d = ImageDraw.Draw(sh)
r = 0
for t in 'abc':
    for s in shots:
        for j, p in enumerate((f'review/shots/inst_{t}/{s}.png', f'review/shots/{RED}_{t}/{s}.png', f'review/shots/diff_{t}_{s}.png')):
            sh.paste(Image.open(p).convert('RGB').resize((W, H)), (j * W, r * (H + 16) + 16))
            d.text((j * W + 4, r * (H + 16) + 2), f'{t} {s} {["installed", tag, "diff x4"][j]}', fill=(255, 220, 120))
        r += 1
sh.save(f'review/sheet_face_diff_{tag}.png'); print('SHEET')
