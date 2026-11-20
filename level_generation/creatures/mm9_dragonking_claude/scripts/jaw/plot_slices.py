"""Plot slices.npz with PIL: lip faces red, upper-side blue, lower-side green. Args: <npz> <png>"""
import sys, numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); keys = list(d.keys())
C = 500; sheet = Image.new('RGB', (C * 3, C * 3), 'white')
for n, k in enumerate(keys):
    im = Image.new('RGB', (C, C), 'white'); dr = ImageDraw.Draw(im)
    if k.startswith('y'): i, j, x0, x1, y0, y1 = 0, 2, -1.2, 1.2, 14.4, 16.8
    else: i, j, x0, x1, y0, y1 = 1, 2, -5.4, -1.4, 14.2, 18.2
    sc = C / max(x1 - x0, y1 - y0)
    f = lambda x, y: ((x - x0) * sc, C - (y - y0) * sc)
    for g in np.arange(np.ceil(y0 * 5) / 5, y1, 0.2):
        dr.line([f(x0, g), f(x1, g)], fill=(225, 225, 225))
    for g in np.arange(np.ceil(x0 * 5) / 5, x1, 0.2):
        dr.line([f(g, y0), f(g, y1)], fill=(225, 225, 225))
    for s in d[k]:
        c = (220, 0, 0) if s[6] else ((0, 0, 220) if s[7] > 0 else (0, 150, 0))
        dr.line([f(s[i], s[j]), f(s[3 + i], s[3 + j])], fill=c, width=2)
    dr.text((5, 5), f'{k}  x[{x0},{x1}] z[{y0},{y1}] grid 0.2', fill='black')
    sheet.paste(im, ((n % 3) * C, (n // 3) * C))
sheet.save(sys.argv[2])
