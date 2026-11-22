#!/usr/bin/env python3
"""pairs.py <out prefix> <per sheet> : before | after side by side, per shot name."""
import sys, os, glob
from PIL import Image, ImageDraw
pre, per = sys.argv[1], int(sys.argv[2])
names = sorted(os.path.basename(f) for f in glob.glob('shots_after/*.png'))
W, H = 560, 315
for k in range(0, len(names), per):
    chunk = names[k:k + per]
    S = Image.new('RGB', (2 * W, len(chunk) * (H + 16)), (20, 20, 20))
    d = ImageDraw.Draw(S)
    for i, n in enumerate(chunk):
        for j, side in enumerate(('before', 'after')):
            f = f'shots_{side}/{n}'
            if os.path.exists(f):
                S.paste(Image.open(f).convert('RGB').resize((W, H)), (j * W, i * (H + 16) + 16))
            d.text((j * W + 4, i * (H + 16) + 2), f'{side} {n}', fill=(255, 255, 0))
    S.save(f'{pre}_{k // per + 1}.jpg', quality=85)
