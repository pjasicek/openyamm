#!/usr/bin/env python3
"""Death thorax height before/after the fix (work/death_fix.npz from fix_clips.py) plus the lowest body and prop
vertex after it, per viewer frame: review/death/thorax_height.png (PIL; no matplotlib here)."""
import numpy as np
from PIL import Image, ImageDraw
d = np.load('work/death_fix.npz'); n = len(d['before'])
W, H, L, T, B = 1100, 480, 60, 30, 50
img = Image.new('RGB', (W, H), 'white'); g = ImageDraw.Draw(img)
X = lambda f: L + f / (n - 1) * (W - L - 20); Y = lambda cm: H - B - (cm + 5) / 75 * (H - T - B)
g.rectangle([X(26), T, X(34), H - B], fill=(255, 236, 200))
for cm in range(0, 71, 10):
    g.line([L, Y(cm), W - 20, Y(cm)], fill=(225, 225, 225)); g.text((8, Y(cm) - 6), f'{cm} cm', fill='black')
for f in range(0, n, 2):
    g.text((X(f) - 6, H - B + 6), str(f), fill='black')
g.line([L, Y(0), W - 20, Y(0)], fill='black')
for key, col, w in (('before', (150, 150, 150), 3), ('after', (31, 111, 209), 3), ('low_body', (42, 157, 85), 1), ('low_prop', (192, 57, 43), 1)):
    pts = [(X(f), Y(v * 100)) for f, v in enumerate(d[key])]
    g.line(pts, fill=col, width=w)
    if w > 1:
        for p in pts:
            g.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=col)
g.text((L, 8), 'MM8 Wasp Warrior Death, thorax height per viewer frame (48 fps). grey: installed/before, blue: fixed, '
       'green: fixed lowest body vertex, red: fixed lowest sword/shield vertex; shaded: rewritten Root frames', fill='black')
img.save('review/death/thorax_height.png'); print('PLOT review/death/thorax_height.png')
