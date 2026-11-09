#!/usr/bin/env python3
"""Grid of renders: grid.py <out.png> <cols> <img...> (label = file stem)."""
import sys, os
from PIL import Image, ImageDraw
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
S = 300; rows = (len(files) + cols - 1) // cols
sh = Image.new('RGB', (S * cols, S * rows), (20, 20, 20)); d = ImageDraw.Draw(sh)
for i, f in enumerate(files):
    x, y = i % cols * S, i // cols * S
    sh.paste(Image.open(f).convert('RGB').resize((S, S)), (x, y)); d.text((x + 4, y + 4), os.path.basename(f)[:-4], fill=(255, 230, 120))
sh.save(out); print('GRID', out)
