#!/usr/bin/env python3
"""Sheet of review/close renders: rows = spots x mode, columns = labels. Usage: close_sheet.py <out.png> <label,...> [spot,...]"""
import sys
from PIL import Image, ImageDraw
out, labels = sys.argv[1], sys.argv[2].split(',')
spots = sys.argv[3].split(',') if len(sys.argv) > 3 else ['face_front', 'face_q34', 'hand_l', 'hand_r', 'hand_l_up',
                                                           'chest', 'side', 'back', 'elbow']
modes = sys.argv[4].split(',') if len(sys.argv) > 4 else ['tex', 'clay']
S = 300; rows = [(s, m) for s in spots for m in modes]
sheet = Image.new('RGB', (S * len(labels), 20 + S * len(rows)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for j, l in enumerate(labels):
    d.text((j * S + 6, 4), l, fill=(255, 230, 120))
for i, (s, m) in enumerate(rows):
    for j, l in enumerate(labels):
        sheet.paste(Image.open(f'review/close/{l}_{s}_{m}.png').convert('RGB').resize((S, S)), (j * S, 20 + i * S))
    d.text((4, 24 + i * S), f'{s} {m}', fill=(255, 255, 255))
sheet.save(out); print('SHEET', out)
