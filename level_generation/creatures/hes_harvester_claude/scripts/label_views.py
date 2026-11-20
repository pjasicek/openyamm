#!/usr/bin/env python3
"""Write component indices onto the component renders. Usage: label_views.py <prefix> <view> [...]"""
import json, sys
from PIL import Image, ImageDraw
prefix = sys.argv[1]
for view in sys.argv[2:]:
    im = Image.open(f'{prefix}_{view}.png').convert('RGB'); d = ImageDraw.Draw(im)
    for c, x, y in json.load(open(f'{prefix}_{view}_marks.json')):
        X, Y = x * im.width, y * im.height
        d.text((X - 6, Y - 6), str(c), fill=(255, 255, 0)); d.text((X - 5, Y - 5), str(c), fill=(0, 0, 0))
    im.save(f'{prefix}_{view}_lab.png')
