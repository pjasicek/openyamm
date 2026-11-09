#!/usr/bin/env python3
"""Compose work/film/rows.json (filmstrip.py) into one sheet: rows = clip x model, columns = viewer frames."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[1]; d = json.load(open(P / 'work/film/rows.json'))
S = 200; cols = max(len(r[1]) for r in d['rows'])
sheet = Image.new('RGB', (120 + S * cols, S * len(d['rows'])), (20, 20, 20)); dr = ImageDraw.Draw(sheet)
for i, (label, files) in enumerate(d['rows']):
    dr.text((6, i * S + S // 2), label, fill=(255, 230, 120))
    for j, (k, f) in enumerate(files):
        sheet.paste(Image.open(f).convert('RGB').resize((S, S)), (120 + j * S, i * S)); dr.text((124 + j * S, i * S + 4), f'frame {k}', fill=(255, 255, 255))
out = P / d['out']; out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out); print('SHEET', out)
