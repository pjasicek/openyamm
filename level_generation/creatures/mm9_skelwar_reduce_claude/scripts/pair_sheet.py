#!/usr/bin/env python3
"""Side-by-side sheet of review/glbclose renders: per spot one row of <A> tex | <B> tex | |diff| x4 | <A> clay | <B> clay.
Usage: pair_sheet.py <labelA> <labelB> <spot,...> <out.png> [cell px]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]; R = HERE / 'review' / 'glbclose'
a, b, spots, out = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]
C = int(sys.argv[5]) if len(sys.argv) > 5 else 300
sheet = Image.new('RGB', (C * 5, C * len(spots) + 20 * len(spots)), 'white'); d = ImageDraw.Draw(sheet)
for r, sp in enumerate(spots):
    y = r * (C + 20)
    ta, tb = (Image.open(R / f'{x}_{sp}_tex.png').convert('RGB') for x in (a, b))
    diff = Image.fromarray(np.clip(np.abs(np.asarray(ta, int) - np.asarray(tb, int)) * 4, 0, 255).astype(np.uint8))
    ims = [ta, tb, diff] + [Image.open(R / f'{x}_{sp}_clay.png').convert('RGB') for x in (a, b)]
    for k, im in enumerate(ims):
        sheet.paste(im.resize((C, C)), (k * C, y + 20))
    d.text((4, y + 4), f'{sp}: {a} tex | {b} tex | diff x4 | {a} clay | {b} clay', fill='black')
sheet.save(out); print('SHEET', out)
