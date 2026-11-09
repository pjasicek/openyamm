#!/usr/bin/env python3
"""Sheets of the scan survey (work/survey): one row per scan key, eight yaws. Usage: survey_sheet.py out.png key..."""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, *keys = sys.argv[1:]
T = 150
s = Image.new('RGB', (T * 8 + 70, T * len(keys)), (90, 100, 90)); d = ImageDraw.Draw(s)
for r, k in enumerate(keys):
    d.text((2, r * T + 4), k, fill=(255, 255, 255))
    for i, y in enumerate(range(0, 360, 45)):
        im = Image.open(os.path.join(HERE, 'work', 'survey', f'{k}_y{y:03d}.png')).convert('RGBA')
        bb = im.getbbox(); im = im.crop(bb) if bb else im; im.thumbnail((T - 6, T - 6))
        s.paste(im, (70 + i * T + (T - im.width) // 2, r * T + T - 3 - im.height), im)
        if r == 0:
            d.text((70 + i * T + 2, 2), str(y), fill=(255, 255, 0))
s.save(out); print(out)
