#!/usr/bin/env python3
"""Before/after sheet of the bow hand: columns clip:frame, rows before/after from the left side and left front.
Usage: carry_sheet.py <renders> <out.png> <clip:f,f,...> [...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
R, out = Path(sys.argv[1]), Path(sys.argv[2])
cols = [(c, int(f)) for spec in sys.argv[3:] for c, fs in [spec.split(':')] for f in fs.split(',')]
rows = [('b', 'lside', 'before'), ('n', 'lside', 'after'), ('b', 'lfront', 'before'), ('n', 'lfront', 'after')]
w, h = 250, 270; sheet = Image.new('RGB', (w * len(cols), h * len(rows)), (60, 60, 64)); d = ImageDraw.Draw(sheet)
for i, (c, f) in enumerate(cols):
    for j, (tag, v, label) in enumerate(rows):
        v = {'lside': 'quarter', 'lfront': 'front'}[v] if c == 'Death' else v      # whole body while falling
        im = Image.open(R / f'{tag}_{c}_{v}_{f:02d}.png').convert('RGB')
        im = (im.crop((60, 60, 460, 490)) if c != 'Death' else im).resize((w, h)); sheet.paste(im, (i * w, j * h))
        d.text((i * w + 4, j * h + 4), f'{label} {c} f{f}', fill='yellow' if tag == 'b' else 'cyan')
out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out); print(out)
