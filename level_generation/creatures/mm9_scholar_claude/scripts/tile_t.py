"""Tile a clay_frames.py .list transposed: columns = items (clip:t), rows = views. Args: <list> <out png> [cell]"""
import sys
from PIL import Image, ImageDraw
rows = [l.split('\t') for l in open(sys.argv[1]).read().strip().split('\n')]; cell = int(sys.argv[3]) if len(sys.argv) > 3 else 250
nv = len(rows[0]) - 1; o = Image.new('RGB', (cell * len(rows), cell * nv)); d = ImageDraw.Draw(o)
for c, r in enumerate(rows):
    for v, f in enumerate(r[1:]):
        o.paste(Image.open(f).convert('RGB').resize((cell, cell)), (c * cell, v * cell))
    d.text((c * cell + 4, 4), r[0], fill=(255, 255, 0))
o.save(sys.argv[2])
