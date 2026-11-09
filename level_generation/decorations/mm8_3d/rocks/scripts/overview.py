#!/usr/bin/env python3
"""Stack the top rows (native | front | three-quarter | side) of several review/<rock>/compare.png sheets, scaled
to half size: overview.py out.png rock..."""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, *rocks = sys.argv[1:]
rows = [Image.open(os.path.join(HERE, 'review', r, 'compare.png')).crop((0, 0, 1200, 320)).resize((600, 160)) for r in rocks]
s = Image.new('RGB', (600, 160 * len(rows)), (255, 255, 255))
for i, r in enumerate(rows):
    s.paste(r, (0, 160 * i))
s.save(out); print(out)
