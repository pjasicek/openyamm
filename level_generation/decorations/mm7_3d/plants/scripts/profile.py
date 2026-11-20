#!/usr/bin/env python3
"""Print a sprite's opaque runs per height band (fractions of the art height from the ground, x in art-height units
from the art's horizontal centre), for laying out models. Usage: profile.py <id> [bands]"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SPECS, SPRITES
sid = sys.argv[1]; bands = int(sys.argv[2]) if len(sys.argv) > 2 else 20
a = np.asarray(Image.open(os.path.join(SPRITES, SPECS[sid][0])).convert('RGBA'))[..., 3] > 128
ys, xs = np.nonzero(a)
top, bottom = ys.min(), ys.max(); H = bottom - top + 1
cx = (xs.min() + xs.max()) / 2
print(sid, 'art px', H, 'width/height', round((xs.max() - xs.min() + 1) / H, 3))
for b in range(bands, 0, -1):
    y = int(bottom - (b - 0.5) / bands * H)
    row = a[y]; runs = []; x = 0
    while x < len(row):
        if row[x]:
            s = x
            while x < len(row) and row[x]:
                x += 1
            if x - s > 1:
                runs.append((round(float((s - cx) / H), 3), round(float((x - cx) / H), 3)))
        x += 1
    print(f'{(b - 0.5) / bands:.3f}', runs)
