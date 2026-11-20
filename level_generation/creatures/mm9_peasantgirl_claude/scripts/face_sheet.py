#!/usr/bin/env python3
"""Face review sheet: per woman (B row 36, A rows 34/41) MM9's head front / three-quarter / side next to ours front / three-quarter /
side / party view (~22 deg above). Args: <shots dir under review/shots> <out png>. Project folder."""
import sys
from PIL import Image, ImageDraw
d, out = sys.argv[1:3]; C = 360
def sq(p, crop=None):
    im = Image.open(p).convert('RGB'); w, h = im.size
    if crop: im = im.crop(crop)
    else:
        c = min(w, h); im = im.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c))
    return im.resize((C, C), Image.LANCZOS)
S = Image.new('RGB', (7 * C, 2 * C + 30), (28, 28, 28)); dr = ImageDraw.Draw(S)
for r, t in enumerate('ba'):
    row = [sq(f'work/refs/head_{t}_front.png'), sq(f'work/refs/head_{t}_q34.png'), sq(f'work/refs/head_{t}_right.png')]
    row += [sq(f'review/shots/{d}/pf5_{t}_{v}.png', (168, 40, 868, 740)) for v in 'fqs'] + [sq(f'review/shots/{d}/pf5_{t}_p.png')]
    for c, im in enumerate(row): S.paste(im, (c * C, 30 + r * C))
for c, lab in enumerate(['MM9 front', 'MM9 3/4', 'MM9 side', 'ours front', 'ours 3/4', 'ours side', 'ours party view (~22 deg)']):
    dr.text((c * C + 6, 8), lab, fill=(255, 255, 0))
S.save(out); print('SHEET', out)
