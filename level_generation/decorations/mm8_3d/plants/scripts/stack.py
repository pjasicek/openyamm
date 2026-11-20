#!/usr/bin/env python3
"""Stack the top rows (sprite + LOD0 views) of several review sheets: review/stack.png. Usage: stack.py ids..."""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for sid in sys.argv[1:]:
    im = Image.open(os.path.join(HERE, 'review', sid, 'compare.png'))
    rows.append(im.crop((0, 0, 340 * 5, 362)))
out = Image.new('RGB', (340 * 5, 362 * len(rows)), 'white')
for i, r in enumerate(rows):
    out.paste(r, (0, i * 362))
out = out.resize((out.width * 3 // 4, out.height * 3 // 4), Image.LANCZOS)
out.save(os.path.join(HERE, 'review', 'stack.png'))
