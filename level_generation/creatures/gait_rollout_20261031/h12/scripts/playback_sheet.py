#!/usr/bin/env python3
"""Contact sheet of the browser playback frames (half speed, six per clip) of one review viewer:
review/<m>_playback_sheet.png.  playback_sheet.py <m> <clip,clip,...>"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
m, rows = sys.argv[1], sys.argv[2].split(',')
playback = HERE.parents[1] / f'mm7_{m}_gait_h12_claude/review/playback'
tiles = [[Image.open(playback / f'{clip}-0.5-{i}.png').convert('RGB') for i in range(6)] for clip in rows]
w, h = tiles[0][0].size
box = (int(w * 0.28), int(h * 0.06), int(w * 0.72), int(h * 0.94))
cw, ch = box[2] - box[0], box[3] - box[1]
tw, th = int(cw * 300 / ch), 300
sheet = Image.new('RGB', (tw * 6, (th + 18) * len(rows)), 'white')
draw = ImageDraw.Draw(sheet)
for r, (clip, row) in enumerate(zip(rows, tiles)):
    for c, tile in enumerate(row):
        sheet.paste(tile.crop(box).resize((tw, th)), (c * tw, r * (th + 18) + 18))
    draw.text((4, r * (th + 18) + 3), f'{m} {clip} (half speed, 6 phases)', fill='black')
out = HERE / f'review/{m}_playback_sheet.png'
sheet.save(out)
print(out)
