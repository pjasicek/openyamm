#!/usr/bin/env python3
"""Native m532 attack frames (views 0 and 2, 125 ms apart) above the Attack v2 renders at the same time (the impact
marker at 1.0 s is the native action length), plus the release and recovery. Usage: native_sheet.py <renders> <out.png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
R, out = Path(sys.argv[1]), Path(sys.argv[2])
N = Path(__file__).resolve().parents[3] / 'mm8_m532_claude/native'
frames = [0, 6, 12, 18, 24, 30, 36, 42, 48, 58, 72]; w, h = 230, 250
rows = [('native v0', '0', None), ('3D front', None, 'front'), ('native v2', '2', None), ('3D right', None, 'rside'),
        ('3D quarter', None, 'quarter')]
sheet = Image.new('RGB', (w * len(frames), h * len(rows)), (40, 40, 44)); d = ImageDraw.Draw(sheet)
for j, (label, view, cam) in enumerate(rows):
    for i, f in enumerate(frames):
        x, y = i * w, j * h; ms = round(f / 48 * 1000)
        if view is not None:
            if f >= 48:
                continue
            im = Image.open(N / f'm532a{"abcdefgh"[f // 6]}{view}.png').convert('RGBA')
            im.thumbnail((w - 10, h - 24)); sheet.paste(im, (x + (w - im.width) // 2, y + h - im.height - 4), im)
        else:
            im = Image.open(R / f'a_{cam}_{f:02d}.png').convert('RGB').crop((40, 20, 480, 500)).resize((w, h))
            sheet.paste(im, (x, y))
        tag = ' release' if f == 48 else ''
        d.text((x + 4, y + 4), f'{label} {ms} ms{tag}', fill='yellow')
out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out); print(out)
