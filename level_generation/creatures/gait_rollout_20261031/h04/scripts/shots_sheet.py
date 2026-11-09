#!/usr/bin/env python3
"""Crop and tile the viewer shots of a review viewer: shots_sheet.py <m> <out.png> <shot>[,<shot>...]"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
m, out, names = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
shots = HERE.parents[1] / f'mm6_{m}_gait_h02_claude/review/shots'
tiles = [Image.open(shots / f'{n}.png').convert('RGB') for n in names]
w, h = tiles[0].size
box = (int(w * 0.25), int(h * 0.05), int(w * 0.75), int(h * 0.92))
tw, th = int((box[2] - box[0]) * 420 / (box[3] - box[1])), 420
sheet = Image.new('RGB', (tw * len(tiles), th + 18), 'white')
d = ImageDraw.Draw(sheet)
for i, (n, t) in enumerate(zip(names, tiles)):
    sheet.paste(t.crop(box).resize((tw, th)), (i * tw, 18))
    d.text((i * tw + 4, 3), n, fill='black')
sheet.save(HERE / out)
print(out)
