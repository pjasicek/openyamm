#!/usr/bin/env python3
"""Sheet of review/glbclose renders: rows = spots, columns = labels x (tex, clay).
Usage: glb_sheet.py <out.png> <label,...> [spot,...] [modes, default tex,clay]"""
import sys
from PIL import Image, ImageDraw
out, labels = sys.argv[1], sys.argv[2].split(',')
spots = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else [
    'head_front', 'head_q34', 'head_side', 'head_back', 'helmet_top', 'torso', 'back', 'quiver', 'hand_r', 'hand_l',
    'grip_draw', 'pinch_draw', 'attack', 'boots', 'boots_back', 'death']
modes = sys.argv[4].split(',') if len(sys.argv) > 4 else ['tex', 'clay']
S = 300; cols = [(l, m) for m in modes for l in labels]
sheet = Image.new('RGB', (S * len(cols), 20 + S * len(spots)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for j, (l, m) in enumerate(cols):
    d.text((j * S + 6, 4), f'{l} {m}', fill=(255, 230, 120))
for i, s in enumerate(spots):
    for j, (l, m) in enumerate(cols):
        sheet.paste(Image.open(f'review/glbclose/{l}_{s}_{m}.png').convert('RGB').resize((S, S)), (j * S, 20 + i * S))
    d.text((4, 24 + i * S), s, fill=(255, 255, 255))
sheet.save(out); print('SHEET', out)
