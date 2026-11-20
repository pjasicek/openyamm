#!/usr/bin/env python3
"""Close-up sheet, installed over reduced, at 560 px per shot: review/sheet_close_<tag>_<tier>.png.
Usage: close_sheet.py <tag> <tier> <shot>...   (shots from review/shots/<inst|red>_<tier>/)"""
import sys
from PIL import Image, ImageDraw
tag, t, shots = sys.argv[1], sys.argv[2], sys.argv[3:]
W = 560; H = int(W * 1060 / 1440)
sh = Image.new('RGB', (W * len(shots), (H + 20) * 2), (25, 25, 25)); d = ImageDraw.Draw(sh)
for j, k in enumerate(['inst', 'red']):
    for i, s in enumerate(shots):
        sh.paste(Image.open(f'review/shots/{k}_{t}/{s}.png').convert('RGB').resize((W, H)), (i * W, j * (H + 20) + 20))
        d.text((i * W + 4, j * (H + 20) + 4), f'{t} {"installed" if k == "inst" else tag} {s}', fill=(255, 220, 120))
sh.save(f'review/sheet_close_{tag}_{t}.png'); print('SHEET', sh.size)
