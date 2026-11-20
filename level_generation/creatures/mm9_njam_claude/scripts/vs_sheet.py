#!/usr/bin/env python3
"""MM9 vs ours: top row MM9 (Blender render of the true-handed source, mm9_compare.py), bottom row our viewer shots, same clip times.
Args: <out png> <mm9 prefix> <ours prefix> <n> [labels comma]"""
import sys
from PIL import Image, ImageDraw
out, mp, op, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]); lab = sys.argv[5].split(',') if len(sys.argv) > 5 else []
S = 420
o = Image.new('RGB', (S * n, S * 2), (40, 40, 40)); d = ImageDraw.Draw(o)
for k in range(n):
    a = Image.open(f'{mp}_{k}.png').convert('RGB').resize((S, S))
    b = Image.open(f'{op}_{k}.png').convert('RGB'); w, h = b.size; b = b.crop(((w - h) // 2 + 40, 20, (w + h) // 2 - 40, h - 60)).resize((S, S))
    o.paste(a, (k * S, 0)); o.paste(b, (k * S, S))
    if k < len(lab): d.text((k * S + 6, 6), 'MM9 ' + lab[k], fill=(255, 255, 0)); d.text((k * S + 6, S + 6), 'ours ' + lab[k], fill=(255, 255, 0))
o.save(out); print('VS', out, o.size)
