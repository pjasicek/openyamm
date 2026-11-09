#!/usr/bin/env python3
"""Close viewer shots (review/shots_close/<model>/cN.png, close_shots.sh) as installed | reduced pairs, centre crops.
Usage: close_sheet.py <tag> <tier> <shots,...> <out png> [crop px]"""
import sys
from PIL import Image, ImageDraw
tag, t, shots, out = sys.argv[1:5]; C = int(sys.argv[5]) if len(sys.argv) > 5 else 560
shots = shots.split(','); sh = Image.new('RGB', (2 * C, len(shots) * (C + 18)), (25, 25, 25)); d = ImageDraw.Draw(sh)
for r, s in enumerate(shots):
    for c, k in enumerate(('inst', 'red')):
        im = Image.open(f'review/shots_close/{k}_{t}/{s}.png').convert('RGB'); w, h = im.size
        sh.paste(im.crop((w // 2 - C // 2, h // 2 - C // 2, w // 2 + C // 2, h // 2 + C // 2)), (c * C, r * (C + 18) + 18))
        d.text((c * C + 4, r * (C + 18) + 3), f'{t} {"installed" if k == "inst" else tag} {s}', fill=(255, 220, 120))
sh.save(out)
