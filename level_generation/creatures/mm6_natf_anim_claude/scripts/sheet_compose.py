"""Compose clip_sheet.py tiles into one labelled PNG. Usage: sheet_compose.py <out.png> [fps]"""
import json, os, sys
from PIL import Image, ImageDraw
out = sys.argv[1]; fps = float(sys.argv[2]) if len(sys.argv) > 2 else 24
rows = json.load(open(out + '.json')); T = 400; L = 24
s = Image.new('RGB', (T * len(rows[0][1]), (T + L) * len(rows)), (40, 40, 40)); dr = ImageDraw.Draw(s)
for j, (an, row, dur) in enumerate(rows):
    dr.text((6, j * (T + L) + 5), f'{an}  ({dur:.0f} frames)', fill=(255, 255, 255))
    for i, p in enumerate(row):
        s.paste(Image.open(p).convert('RGB'), (i * T, j * (T + L) + L)); os.remove(p)
s.save(out); os.remove(out + '.json'); os.rmdir(out + '_tiles')
