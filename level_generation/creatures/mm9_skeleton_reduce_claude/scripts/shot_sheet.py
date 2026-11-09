#!/usr/bin/env python3
"""Viewer shots side by side: per shot one row installed | reduced | |diff| x4 (review/shots/<tier>_<model>_<shot>.png).
Usage: shot_sheet.py <tier prefix, e.g. skel_a> <A suffix> <B suffix> <shot,...> <out.png> [cell px]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]; S = HERE / 'review' / 'shots'
t, a, b, shots, out = sys.argv[1:6]; C = int(sys.argv[6]) if len(sys.argv) > 6 else 360
shots = shots.split(','); sheet = Image.new('RGB', (C * 3, (C + 18) * len(shots)), 'white'); d = ImageDraw.Draw(sheet)
for r, s in enumerate(shots):
    A = Image.open(S / f'{t}_{a}_{s}.png').convert('RGB'); B = Image.open(S / f'{t}_{b}_{s}.png').convert('RGB')
    w, h = A.size; side = min(w, h); box = ((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2)
    A, B = A.crop(box), B.crop(box)
    D = Image.fromarray(np.clip(np.abs(np.asarray(A, int) - np.asarray(B, int)) * 4, 0, 255).astype(np.uint8))
    for k, im in enumerate((A, B, D)):
        sheet.paste(im.resize((C, C)), (k * C, r * (C + 18) + 18))
    d.text((4, r * (C + 18) + 3), f'{t} {s}: {a} | {b} | diff x4', fill='black')
sheet.save(out); print('SHEET', out)
