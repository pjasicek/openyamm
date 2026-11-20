#!/usr/bin/env python3
"""Review sheets from viewer shots. Args: <tier list> <mm9 glb frames prefix>. Writes review/sheet_compare.png, sheet_tiers.png, sheet_close.png."""
import sys
from PIL import Image, ImageDraw
tiers = sys.argv[1].split(',')
T = 360
def crop(p, zoom=1.0):
    """Square crop round the figure (the pixels unlike the viewer's background), so bodies fill the tile."""
    import numpy as np
    im = Image.open(p).convert('RGB'); a = np.asarray(im, np.int32)[30:-60]
    bg = a[5, 5]
    m = np.abs(a - bg).sum(2) > 40
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min() + 30, ys.max() + 30
    s = int(max(x1 - x0, y1 - y0) * 1.08); cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    return im.crop((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2)).resize((T, T), Image.LANCZOS)
ordr = ['r0', 'r1', 'w', 'u', 'a', 'g', 'c', 'h', 'd', 'e']
A = tiers[0]
mm9 = sys.argv[2]
S = Image.new('RGB', (T * len(ordr), T * 2), (40, 40, 40)); d = ImageDraw.Draw(S)
for i, n in enumerate(ordr):
    S.paste(Image.open(f'{mm9}_{n}.png').convert('RGB').resize((T, T)), (T * i, 0))
    S.paste(crop(f'review/shots/{A}_{n}.png', 1.25), (T * i, T))
    d.text((T * i + 6, 6), 'MM9 ' + n, fill=(255, 255, 120)); d.text((T * i + 6, T + 6), 'ours ' + n, fill=(255, 255, 120))
S.save('review/sheet_compare.png')
S = Image.new('RGB', (T * 5, T * len(tiers)), (40, 40, 40)); d = ImageDraw.Draw(S)
for j, t in enumerate(tiers):
    for i, n in enumerate(['r0', 'r1', 'cl', 'ar', 'e']):
        S.paste(crop(f'review/shots/{t}_{n}.png', 1.25 if n != 'cl' else 1.5), (T * i, T * j))
    d.text((6, T * j + 6), t, fill=(255, 255, 120))
S.save('review/sheet_tiers.png')
print('SHEETS')
