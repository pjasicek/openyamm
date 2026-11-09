#!/usr/bin/env python3
"""Viewer-shot sheet per tier: installed (left) and reduced (right) side by side, one row per shot.
Usage: shot_sheet.py <tier a|b|c> <reduced tag> <names,...> <out.png> [size]"""
import sys
from PIL import Image, ImageDraw
t, tag, names, out = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]; S = int(sys.argv[5]) if len(sys.argv) > 5 else 520
labs = [f'{t}_before', f'{t}_{tag}']
sheet = Image.new('RGB', (S * 2, (S + 18) * len(names)), (30, 30, 30)); d = ImageDraw.Draw(sheet)
for j, n in enumerate(names):
    for i, l in enumerate(labs):
        im = Image.open(f'review/shots/{l}/{n}.png').convert('RGB'); w, h = im.size; c = min(w, h)
        im = im.crop(((w - c) // 2, (h - c) // 2, (w + c) // 2, (h + c) // 2)).resize((S, S))
        sheet.paste(im, (i * S, j * (S + 18) + 18)); d.text((i * S + 4, j * (S + 18) + 3), f'{l} {n}', fill=(255, 220, 120))
sheet.save(out); print('SHEET', out)
