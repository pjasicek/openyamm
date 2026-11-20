#!/usr/bin/env python3
"""review/sheet_escapes_<t>.png: per spot of work/escape_spots.json (where s82's LOD0 faces left the charts) installed
(top) vs fix-pass candidate (bottom), textured rest-pose close-ups from escape_close.py. Usage: escape_sheet.py <label>"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parents[1]; lab = sys.argv[1]; n = len(json.load(open(H / 'work' / 'escape_spots.json')))
for t in 'abc':
    W = 300; s = Image.new('RGB', (W * n, 2 * W + 40), (20, 20, 20)); d = ImageDraw.Draw(s)
    d.text((6, 4), f'tier {t.upper()}: where s82 escaped; installed (top) vs {lab} (bottom), rest pose, 18 cm wide', fill=(240, 240, 240))
    for k in range(n):
        for j, l in enumerate(('installed', lab)):
            s.paste(Image.open(H / 'review' / 'escape_close' / f'{t}_{l}_{k:02d}.png').convert('RGB').resize((W, W)), (k * W, 20 + j * (W + 20)))
        d.text((k * W + 4, 20 + W + 4), f'spot {k}', fill=(240, 220, 120))
    s.save(H / 'review' / f'sheet_escapes_{t}.png'); print('sheet', t)
