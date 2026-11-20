#!/usr/bin/env python3
"""Before/after sheets of the texture quality pass from review/texpass/{before,after}_<tier>_<shot>.png
(texpass_views.py). Usage: texpass_sheet.py <close shot,...> <tier shot,...>
Writes review/texpass_closeups_sheet.png (tier A, every close shot: before | after) and
review/texpass_tiers_sheet.png (every tier: before | after of each tier shot)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
D = HERE / 'review' / 'texpass'
close, tiers_shots = sys.argv[1].split(','), sys.argv[2].split(',')
W, H = 700, 490


def tile(name, label):
    im = Image.open(D / f'{name}.png').convert('RGB').resize((W, H), Image.LANCZOS)
    ImageDraw.Draw(im).text((10, 8), label, fill=(255, 255, 255))
    return im


def sheet(rows, out):
    s = Image.new('RGB', (W * len(rows[0]), H * len(rows)), (30, 30, 30))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            s.paste(im, (c * W, r * H))
    s.save(out)
    print('SHEET', out, s.size)


sheet([[tile(f'before_a_{s}', f'before  tier A  {s}'), tile(f'after_a_{s}', f'after  tier A  {s}')] for s in close],
      HERE / 'review' / 'texpass_closeups_sheet.png')
sheet([[tile(f'{st}_{t}_{s}', f'{st}  tier {t.upper()}  {s}') for s in tiers_shots for st in ('before', 'after')]
       for t in 'abc'], HERE / 'review' / 'texpass_tiers_sheet.png')
