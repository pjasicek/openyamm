#!/usr/bin/env python3
"""Readable parts of a strip sheet: clips 1-7 and 8-14, both views, 6 frames. Args: <strip png> <out prefix>"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size; n = H // 600
for k, (a, b) in enumerate(((0, n // 2), (n // 2, n))):
    im.crop((0, a * 600, W, b * 600)).resize((W * 2 // 3, (b - a) * 400), Image.LANCZOS).save(f'{sys.argv[2]}_{k}.png')
