#!/usr/bin/env python3
import numpy as np
from PIL import Image, ImageDraw
D = np.load('work/uv_v1.npz'); uv, tri, mat, comp, inner = D['uv'], D['tri'], D['mat'], D['comp'], D['inner']
for m, S in ((0, 1400), (1, 700)):
    im = Image.new('RGB', (S, S), (20, 20, 20)); dr = ImageDraw.Draw(im)
    for f in np.where(mat == m)[0]:
        t = tri[f]; c = (200, 60, 60) if inner[f] else tuple(int(x) for x in (np.array([80, 160, 220]) + int(comp[t[0]]) * np.array([20, -15, -20])) % 255)
        dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in t], fill=c, outline=(0, 0, 0))
    im.save(f'review/uv_{m}.png')
