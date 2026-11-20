#!/usr/bin/env python3
"""Labelled image grid. Usage: grid_sheet.py <out png> <cell px> <title> <col labels a,b,...> <row spec> [row spec ...]
row spec = <row label>=<png>,<png>,...  (a '-' leaves a cell empty)."""
import sys
from PIL import Image, ImageDraw, ImageFont
out, cell, title = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cols = sys.argv[4].split(',')
rows = [a.split('=', 1) for a in sys.argv[5:]]
LW, TH = 190, 48
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except OSError:
    font = ImageFont.load_default()
sheet = Image.new('RGB', (LW + cell * len(cols), TH + cell * len(rows)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
d.text((6, 4), title, fill=(255, 220, 120), font=font)
for i, c in enumerate(cols):
    d.text((LW + i * cell + 6, 26), c, fill=(230, 230, 230), font=font)
for j, (label, files) in enumerate(rows):
    y = TH + j * cell
    for k, part in enumerate(label.split('|')):
        d.text((6, y + 8 + 18 * k), part, fill=(230, 230, 230), font=font)
    for i, f in enumerate(files.split(',')):
        if f != '-':
            sheet.paste(Image.open(f).convert('RGB').resize((cell, cell), Image.LANCZOS), (LW + i * cell, y))
    d.line([(LW, y), (sheet.size[0], y)], fill=(0, 0, 0), width=2)
sheet.save(out)
print('SHEET', out, sheet.size)
