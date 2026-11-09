"""Plot slices2.npz with PIL. Colours: shell (part 0) black, eyes (1, 18) magenta, tongue part 9 blue, frill 4 green,
teeth orange. Shell segments whose face normal points down (nz < -0.3) drawn dark red. Args: <npz> <png>"""
import sys, numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); keys = list(d.keys())
C = 420; n = len(keys); cols = 6; rows = (n + cols - 1) // cols
sheet = Image.new('RGB', (C * cols, C * rows), 'white')
for k_i, k in enumerate(keys):
    im = Image.new('RGB', (C, C), 'white'); dr = ImageDraw.Draw(im)
    if k.startswith('y'): i, j, x0, x1, y0, y1 = 0, 2, -0.9, 0.9, 14.65, 16.45
    else: i, j, x0, x1, y0, y1 = 1, 2, -5.4, -2.8, 14.6, 17.2
    sc = C / max(x1 - x0, y1 - y0)
    f = lambda x, y: ((x - x0) * sc, C - (y - y0) * sc)
    for g in np.arange(np.ceil(y0 * 10) / 10, y1, 0.1):
        dr.line([f(x0, g), f(x1, g)], fill=(235, 235, 235) if round(g * 10) % 5 else (200, 200, 200))
    for g in np.arange(np.ceil(x0 * 10) / 10, x1, 0.1):
        dr.line([f(g, y0), f(g, y1)], fill=(235, 235, 235) if round(g * 10) % 5 else (200, 200, 200))
    for s in d[k]:
        p = int(s[6])
        c = {0: (0, 0, 0), 1: (220, 0, 220), 18: (220, 0, 220), 9: (0, 60, 255), 4: (0, 160, 0)}.get(p, (255, 140, 0))
        if p == 0 and s[10] < -0.3: c = (170, 0, 0)
        dr.line([f(s[i], s[j]), f(s[3 + i], s[3 + j])], fill=c, width=2)
    dr.text((4, 4), f'{k} grid .1 (.5 dark) z {y0}', fill='black')
    sheet.paste(im, ((k_i % cols) * C, (k_i // cols) * C))
sheet.save(sys.argv[2])
