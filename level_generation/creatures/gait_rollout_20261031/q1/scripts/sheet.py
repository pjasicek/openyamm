#!/usr/bin/env python3
"""Contact sheet of viewer shots: sheet.py <out.png> <columns> <png> [<png> ...] (half size)."""
import sys
from PIL import Image

ims = [Image.open(p).convert('RGB') for p in sys.argv[3:]]
ims = [i.resize((i.width // 2, i.height // 2)) for i in ims]
cols = int(sys.argv[2]); w, h = ims[0].size
sheet = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)))
for k, i in enumerate(ims):
    sheet.paste(i, ((k % cols) * w, (k // cols) * h))
sheet.save(sys.argv[1])
