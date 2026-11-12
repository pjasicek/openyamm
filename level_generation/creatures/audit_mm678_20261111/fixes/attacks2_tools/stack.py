#!/usr/bin/env python3
"""Stack images vertically at one width (native strip above clip sheets): stack.py <out.png> <img> [<img> ...]."""
import sys

from PIL import Image

ims = [Image.open(p).convert('RGB') for p in sys.argv[2:]]
w = max(i.width for i in ims)
ims = [i.resize((w, round(i.height * w / i.width))) for i in ims]
out = Image.new('RGB', (w, sum(i.height for i in ims)), (255, 255, 255))
y = 0
for i in ims:
    out.paste(i, (0, y))
    y += i.height
out.save(sys.argv[1])
print(sys.argv[1], out.size)
