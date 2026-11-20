#!/usr/bin/env python3
"""Draw the 10 cm grid onto grid_views.py renders (ortho scale 3.4 m over 1500 px). Args: prefix"""
import sys
from PIL import Image, ImageDraw
pre = sys.argv[1]; W, H, S = 1500, 900, 3.4; k = W / S
# view -> (horizontal axis label, vertical axis label, centre (h, v), h sign, v sign)
V = {'side': ('y', 'z', (0, 0.6), 1, 1), 'front': ('x', 'z', (0, 0.6), 1, 1), 'top': ('x', 'y', (0, 0), 1, 1),
     'below': ('x', 'y', (0, 0), -1, 1)}
for name, (ha, va, (ch, cv), sh, sv) in V.items():
    im = Image.open(f'{pre}_{name}.png').convert('RGB'); d = ImageDraw.Draw(im)
    for i in range(-30, 31):
        m = i / 10
        x = W / 2 + sh * (m - ch) * k
        y = H / 2 - sv * (m - cv) * k
        col = (200, 0, 0) if i % 5 == 0 else (150, 150, 255)
        if 0 <= x < W:
            d.line([(x, 0), (x, H)], fill=col, width=1); d.text((x + 2, 2), f'{ha}{m:+.1f}', fill=(0, 0, 0))
        if 0 <= y < H:
            d.line([(0, y), (W, y)], fill=col, width=1); d.text((2, y + 2), f'{va}{m:+.1f}', fill=(0, 0, 0))
    im.save(f'{pre}_{name}_grid.png')
