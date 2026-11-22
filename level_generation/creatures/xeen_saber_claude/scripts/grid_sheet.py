#!/usr/bin/env python3
"""Join images into a grid sheet. Usage: grid_sheet.py <out.png> <cols> <img>... (or @list.json)"""
import sys, json
from PIL import Image
out, cols = sys.argv[1], int(sys.argv[2])
files = [f[1] if isinstance(f, list) else f for f in json.load(open(sys.argv[3][1:]))] if sys.argv[3].startswith('@') else sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
w, h = ims[0].size
S = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)), (255, 255, 255))
for k, im in enumerate(ims):
    S.paste(im.resize((w, h)), ((k % cols) * w, (k // cols) * h))
S.save(out)
