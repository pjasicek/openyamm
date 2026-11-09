#!/usr/bin/env python3
"""Labelled grid of ear_views.py renders: one row per <label>=<dir>, one column per view.
Usage: ear_sheet.py <out png> <views comma list> <cell px> <label>=<dir> ..."""
import sys
from PIL import Image, ImageDraw, ImageFont
out, views, cell = sys.argv[1], sys.argv[2].split(','), int(sys.argv[3])
rows = [a.split('=', 1) for a in sys.argv[4:]]
LW, TH = 150, 26
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
except OSError:
    font = ImageFont.load_default()
sheet = Image.new('RGB', (LW + cell * len(views), TH + cell * len(rows)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
for i, v in enumerate(views):
    d.text((LW + i * cell + 6, 5), v, fill=(230, 230, 230), font=font)
for j, (label, folder) in enumerate(rows):
    y = TH + j * cell
    for k, part in enumerate(label.split('|')):
        d.text((6, y + 8 + 20 * k), part, fill=(230, 230, 230), font=font)
    for i, v in enumerate(views):
        img = Image.open(f"{folder}/{v}.png").convert("RGB").resize((cell, cell), Image.LANCZOS)
        sheet.paste(img, (LW + i * cell, y))
sheet.save(out)
print('SHEET', out, sheet.size)
