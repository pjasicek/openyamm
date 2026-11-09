#!/usr/bin/env python3
"""Clip strips from viewer shots review/shots/s_<clip>_<i>.png: one row per clip, four times, cropped to the figure.
Usage: strip_sheet.py <out png> <clip> [...]"""
import sys
from PIL import Image, ImageDraw
out, clips = sys.argv[1], sys.argv[2:]
cw, ch = 260, 315
sheet = Image.new('RGB', (cw * 4 + 120, ch * len(clips)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for r, c in enumerate(clips):
    d.text((6, r * ch + ch // 2), c, fill=(255, 255, 255))
    for i in range(4):
        im = Image.open(f'review/shots/s_{c}_{i}.png').convert('RGB').crop((318, 260, 718, 745))
        sheet.paste(im.resize((cw, ch)), (120 + i * cw, r * ch))
sheet.save(out)
