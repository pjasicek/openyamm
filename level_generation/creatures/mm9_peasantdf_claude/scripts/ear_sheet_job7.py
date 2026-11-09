#!/usr/bin/env python3
"""Job 7 sheet of viewer ear shots (ear_shots.sh): one row per tier and set (before/after), columns earR, earL, lowR,
lowL, front, party; each shot centre-cropped to 760x700 and scaled to CELL px. Args: <out png> <cell px> <label=dir>..."""
import sys
from PIL import Image, ImageDraw
out, cell = sys.argv[1], int(sys.argv[2]); sets = [a.split('=', 1) for a in sys.argv[3:]]
views = ['earR', 'earL', 'lowR', 'lowL', 'front', 'party']
rows = []
for label, d in sets:
    ims = []
    for v in views:
        im = Image.open(f'{d}/{v}.png').convert('RGB'); w, h = im.size
        ims.append(im.crop(((w - 760) // 2, (h - 700) // 2, (w + 760) // 2, (h + 700) // 2)).resize((cell, int(cell * 700 / 760))))
    rows.append((label, ims))
ch = int(cell * 700 / 760)
S = Image.new('RGB', (cell * len(views), (ch + 22) * len(rows)), (30, 30, 30)); dr = ImageDraw.Draw(S)
for r, (label, ims) in enumerate(rows):
    y = r * (ch + 22)
    dr.text((6, y + 5), label, fill=(255, 255, 160))
    for c, im in enumerate(ims):
        S.paste(im, (c * cell, y + 22))
        if r == 0: dr.text((c * cell + cell - 60, y + 5), views[c], fill=(200, 200, 200))
S.save(out); print('SHEET', out, S.size)
