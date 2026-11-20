#!/usr/bin/env python3
"""Plot of work/fingertips.json (fingertip_speed.py): per viewer frame fingertip speed, Fidget and Hit, before (grey)
and after (blue) the arm-boundary easing, left (solid) and right (thin) hands -> review/fingertip_speed.png"""
import json
from PIL import Image, ImageDraw
d = json.load(open('work/fingertips.json'))
W, H, M = 1100, 300, 50
img = Image.new('RGB', (W, 2 * H + 30), (250, 250, 250)); dr = ImageDraw.Draw(img)
dr.text((M, 6), 'fingertip speed, mm per viewer frame (48 fps): grey = before, blue = after; thick = left, thin = right',
        fill=(0, 0, 0))
for row, clip in enumerate(('Fidget', 'Hit')):
    y0 = 30 + row * H; top = 60
    n = len(d['before'][clip]['LeftHandMiddle3'])
    X = lambda i: M + (W - 2 * M) * i / (n - 1); Y = lambda v: y0 + H - 30 - (H - 60) * min(v, top) / top
    for v in range(0, top + 1, 10):
        dr.line([(M, Y(v)), (W - M, Y(v))], fill=(225, 225, 225)); dr.text((8, Y(v) - 6), str(v), fill=(90, 90, 90))
    for i in range(0, n, 8 if n > 60 else 4):
        dr.text((X(i) - 6, y0 + H - 24), str(i + 1), fill=(90, 90, 90))
    dr.text((M + 4, y0 + 4), clip, fill=(0, 0, 0))
    for label, col in (('before', (150, 150, 150)), ('after', (30, 100, 220))):
        for bone, width in (('LeftHandMiddle3', 3), ('RightHandMiddle3', 1)):
            v = d[label][clip][bone]
            dr.line([(X(i), Y(x)) for i, x in enumerate(v)], fill=col, width=width)
img.save('review/fingertip_speed.png'); print('PLOT review/fingertip_speed.png')
