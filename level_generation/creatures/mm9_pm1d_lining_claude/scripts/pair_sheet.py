#!/usr/bin/env python3
"""Installed | lined | |difference| x4 (black = unchanged) per viewer shot, one row each, split into sheets of `rows` rows.
Usage: pair_sheet.py <set> <installed id> <lined id> <out stem> [rows 6] [names comma list]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[1] / 'review'
st, a, b, stem = sys.argv[1:5]; rows = int(sys.argv[5]) if len(sys.argv) > 5 else 6
names = sys.argv[6].split(',') if len(sys.argv) > 6 else sorted(x.stem for x in (P / 'shots' / st / a).glob('*.png'))
W = 520
for k in range(0, len(names), rows):
    part = names[k:k + rows]; ims = []
    for n in part:
        x = Image.open(P / 'shots' / st / a / f'{n}.png').convert('RGB'); y = Image.open(P / 'shots' / st / b / f'{n}.png').convert('RGB')
        d = np.clip(np.abs(np.asarray(x, int) - np.asarray(y, int)) * 4, 0, 255).astype(np.uint8)
        ims.append([x, y, Image.fromarray(d)])
    h = int(W * ims[0][0].height / ims[0][0].width)
    sh = Image.new('RGB', (W * 3, (h + 20) * len(part)), (20, 20, 20)); dr = ImageDraw.Draw(sh)
    for r, (n, trio) in enumerate(zip(part, ims)):
        for c, im in enumerate(trio):
            sh.paste(im.resize((W, h)), (c * W, r * (h + 20) + 20))
        dr.text((4, r * (h + 20) + 4), f'{n}: {a} | {b} | |diff| x4', fill=(255, 220, 120))
    out = P / f'{stem}_{k // rows + 1}.png'; sh.save(out); print(out)
