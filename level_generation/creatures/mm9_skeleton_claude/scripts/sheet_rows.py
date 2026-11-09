#!/usr/bin/env python3
"""Stack images vertically. Args: <out> <images...>"""
import sys
from PIL import Image
ims = [Image.open(p).convert('RGB') for p in sys.argv[2:]]
W = max(i.width for i in ims); H = sum(i.height for i in ims)
s = Image.new('RGB', (W, H), (30, 30, 30)); y = 0
for i in ims:
    s.paste(i, (0, y)); y += i.height
s.save(sys.argv[1]); print(s.size)
