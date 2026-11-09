#!/usr/bin/env python3
"""Before/after sheet of the texture pass from review-viewer shots at identical cameras.

Usage: texpass_sheet.py <shots dir> <out png> <tier,tier,...> <shot,shot,...> [crop]
Files are <dir>/before_<tier>_<shot>.png and after_<tier>_<shot>.png, or before_<shot>.png / after_<shot>.png when
the tier list is '-'. One row per tier and shot: before | after. With 'crop', the middle of each shot at 1:1 is added
(before | after), for the texel-level look."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

d, out = Path(sys.argv[1]), sys.argv[2]
tiers, shots = sys.argv[3].split(','), sys.argv[4].split(',')
crop = len(sys.argv) > 5
W, H = 700, 516
C = 516


def load(st, t, s):
    return Image.open(d / (f'{st}_{s}.png' if t == '-' else f'{st}_{t}_{s}.png')).convert('RGB')


rows = [(t, s) for t in tiers for s in shots]
sheet = Image.new('RGB', (W * 2 + (C * 2 if crop else 0), H * len(rows)), (30, 30, 30))
for r, (t, s) in enumerate(rows):
    for c, st in enumerate(('before', 'after')):
        im = load(st, t, s)
        tile = im.resize((W, H), Image.LANCZOS)
        ImageDraw.Draw(tile).text((10, 8), f'{st}  {"" if t == "-" else "tier " + t.upper()}  {s}', fill=(255, 255, 255))
        sheet.paste(tile, (c * W, r * H))
        if crop:
            x, y = im.width // 2 - C // 2, im.height // 2 - C // 2
            sheet.paste(im.crop((x, y, x + C, y + C)), (W * 2 + c * C, r * H))
sheet.save(out)
print('SHEET', out, sheet.size)
