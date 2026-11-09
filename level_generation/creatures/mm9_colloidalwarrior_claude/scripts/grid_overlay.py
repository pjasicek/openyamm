"""Grid overlay for grid_view.py renders. Args: <out prefix> <cx,cy,cz> <ortho>"""
import sys
import numpy as np
a = [None] + sys.argv[1:]
R = 900; S = float(a[3]); cx, cy, cz = [float(x) for x in a[2].split(',')]
class V: pass
C = V(); C.x, C.y, C.z = cx, cy, cz
OUTP = a[1]
from PIL import Image, ImageDraw
for v, (hx, hz) in {'front': (C.x, C.z), 'side': (C.y, C.z)}.items():
    im = Image.open(f'{OUTP}_{v}.png').convert('RGB'); dr = ImageDraw.Draw(im); k = R / S
    for g in np.arange(np.floor((hx - S / 2) * 10) / 10, hx + S / 2, 0.1):
        x = (g - hx) * k + R / 2; dr.line([(x, 0), (x, R)], fill=(255, 0, 0) if abs(g) < 1e-6 else (80, 80, 200)); dr.text((x + 2, 2), f'{g:+.1f}', fill=(255, 255, 0))
    for g in np.arange(np.floor((hz - S / 2) * 10) / 10, hz + S / 2, 0.1):
        y = R / 2 - (g - hz) * k; dr.line([(0, y), (R, y)], fill=(80, 80, 200)); dr.text((2, y + 2), f'{g:+.1f}', fill=(255, 255, 0))
    im.save(f'{OUTP}_{v}.png')
