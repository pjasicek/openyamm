#!/usr/bin/env python3
"""Join work/clipframes/<clip>_<view>_<k>.png into review/clips_<view>.png (one row per clip). Args: view [clips]"""
import sys, os
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
view = sys.argv[1]
clips = sys.argv[2:] or ['Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget']
rows = []
for c in clips:
    fs = [os.path.join(here, 'work', 'clipframes', f'{c}_{view}_{k}.png') for k in range(7)]
    if not os.path.exists(fs[0]): continue
    ims = [Image.open(f).convert('RGB') for f in fs]
    r = Image.new('RGB', (sum(i.width for i in ims), ims[0].height), 'white')
    x = 0
    for i in ims: r.paste(i, (x, 0)); x += i.width
    ImageDraw.Draw(r).text((4, 4), c, fill=(200, 0, 0)); rows.append(r)
s = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)), 'white')
y = 0
for r in rows: s.paste(r, (0, y)); y += r.height
s.save(os.path.join(here, 'review', f'clips_{view}.png')); print(s.size)
