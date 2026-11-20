#!/usr/bin/env python3
"""Face sheet: per tier and view (front close-up, 3/4, true profile, low 3/4, party) the installed render, the reduced
render and their per-pixel difference x8 (review/glbclose/<label>_<tier>_<spot>_tex.png).
Usage: face_sheet.py <before label> <after label> <out.png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
A, B, out = sys.argv[1:4]
spots = ['face_front', 'face_q34', 'face_profile', 'face_low34', 'party']
rows = []
for t in 'abc':
    for sp in spots:
        a = np.asarray(Image.open(f'review/glbclose/{A}_{t}_{sp}_tex.png').convert('RGB')).astype(int)
        b = np.asarray(Image.open(f'review/glbclose/{B}_{t}_{sp}_tex.png').convert('RGB')).astype(int)
        d = np.clip(np.abs(a - b).max(2) * 8, 0, 255)
        row = Image.fromarray(np.concatenate([a, b, np.stack([d] * 3, -1)], 1).astype(np.uint8)).resize((630, 210))
        ImageDraw.Draw(row).text((4, 3), f'tier {t} {sp}: installed | reduced | diff x8', fill=(255, 220, 120))
        rows.append(row)
sheet = Image.new('RGB', (1260, 210 * ((len(rows) + 1) // 2)))
for i, r in enumerate(rows):
    sheet.paste(r, ((i % 2) * 630, (i // 2) * 210))
sheet.save(out); print('FACESHEET', out)
