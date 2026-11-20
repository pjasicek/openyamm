#!/usr/bin/env python3
"""Sheet of axe_views.py tiles: rows = labels, columns = views x (tex, clay). Usage: axe_sheet.py <out.png>"""
import json, os, sys
from PIL import Image, ImageDraw
t = json.load(open('work/_axe_tiles.json')); labels = list(dict.fromkeys(x[0] for x in t)); cols = list(dict.fromkeys((x[1], x[2]) for x in t))
S = 300; sheet = Image.new('RGB', (S * len(cols), 20 + S * len(labels)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for j, (v, m) in enumerate(cols):
    d.text((j * S + 6, 4), f'{v} {m}', fill=(255, 230, 120))
for label, v, m, p in t:
    i = labels.index(label); j = cols.index((v, m))
    sheet.paste(Image.open(p).convert('RGB').resize((S, S)), (j * S, 20 + i * S)); d.text((j * S + 4, 24 + i * S), label, fill=(255, 255, 255)); os.remove(p)
sheet.save(sys.argv[1]); print('SHEET', sys.argv[1])
