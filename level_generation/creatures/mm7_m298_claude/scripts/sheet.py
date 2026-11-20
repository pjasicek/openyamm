#!/usr/bin/env python3
"""Join review/<tag>/f_NNN_<view>.png (render_clip.py) into review/<tag>_sheet.png: one column per frame, rows
front / side / three-quarter, frame numbers on top. Args: <tag> [scale]"""
import sys, glob, os
from pathlib import Path
from PIL import Image, ImageDraw
tag = sys.argv[1]
k = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
d = Path(__file__).resolve().parents[1] / 'review' / tag
frames = sorted({p.name.split('_')[1] for p in d.glob('f_*_front.png')})
views = ('front', 'side', 'three_quarter')
w, h = Image.open(d / f'f_{frames[0]}_front.png').size
s = Image.new('RGB', (w * len(frames), h * 3 + 16), (25, 25, 25))
dr = ImageDraw.Draw(s)
for i, f in enumerate(frames):
    dr.text((i * w + 4, 2), f'{tag} f{int(f)}', fill=(255, 255, 255))
    for j, v in enumerate(views):
        s.paste(Image.open(d / f'f_{f}_{v}.png').convert('RGB'), (i * w, 16 + j * h))
s = s.resize((int(s.width * k), int(s.height * k)), Image.LANCZOS)
s.save(d.parent / f'{tag}_sheet.png')
print(d.parent / f'{tag}_sheet.png', s.size)
