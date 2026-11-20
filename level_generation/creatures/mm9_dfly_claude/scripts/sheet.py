#!/usr/bin/env python3
"""Compose pose_frames.py output: rows = clip x view, columns = times. Usage: sheet.py <dir> <out> <clips> <n> <views>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
d, out, clips, n, views = sys.argv[1:6]
n = int(n)
rows = [(c, v) for c in clips.split(',') for v in views.split(',')]
first = Image.open(Path(d) / f'{rows[0][0]}_{rows[0][1]}_00.png')
w, h = first.size
s = Image.new('RGB', (110 + n * w, len(rows) * h), (20, 20, 20))
g = ImageDraw.Draw(s)
for r, (c, v) in enumerate(rows):
    g.text((4, r * h + h // 2), f'{c}\n{v}', fill=(230, 230, 230))
    for k in range(n):
        s.paste(Image.open(Path(d) / f'{c}_{v}_{k:02d}.png').convert('RGB'), (110 + k * w, r * h))
s.save(out)
