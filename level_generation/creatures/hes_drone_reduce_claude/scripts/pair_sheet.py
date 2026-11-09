#!/usr/bin/env python3
"""Before/after close-up sheet: rows = spots, columns = <label> x modes. Usage: pair_sheet.py <out.png> <labels,>
<modes,> [spots,]  (review/close/<label>_<spot>_<mode>.png)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parents[1] / 'review' / 'close'
out, labels, modes = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
spots = sys.argv[4].split(',') if len(sys.argv) > 4 else ['lens', 'q34', 'ribs', 'flank_r', 'tail', 'belly', 'flank_l']
S = 320; cols = [(l, m) for m in modes for l in labels]
sheet = Image.new('RGB', (S * len(cols), (S + 22) * len(spots) + 22), (24, 24, 24)); d = ImageDraw.Draw(sheet)
for j, (l, m) in enumerate(cols):
    d.text((j * S + 6, 5), f'{l} {m}', fill=(240, 230, 140))
for i, s in enumerate(spots):
    y = 22 + i * (S + 22); d.text((6, y + 4), s, fill=(220, 220, 220))
    for j, (l, m) in enumerate(cols):
        p = R / f'{l}_{s}_{m}.png'
        if p.exists():
            sheet.paste(Image.open(p).convert('RGB').resize((S, S)), (j * S, y + 22))
sheet.save(out); print('SHEET', out, sheet.size)
