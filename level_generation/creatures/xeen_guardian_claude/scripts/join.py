#!/usr/bin/env python3
"""Join review images into a grid. Usage: join.py <out> <cols> <tile> <img...> (paths relative to the project)."""
import sys
from pathlib import Path
from PIL import Image
R = Path(__file__).resolve().parents[1]
out, cols, tile, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
rows = (len(files) + cols - 1) // cols
S = Image.new('RGB', (cols * tile, rows * tile), 'white')
for i, f in enumerate(files):
    im = Image.open(R / f).convert('RGB'); im.thumbnail((tile, tile))
    S.paste(im, ((i % cols) * tile, (i // cols) * tile))
S.save(R / out)
