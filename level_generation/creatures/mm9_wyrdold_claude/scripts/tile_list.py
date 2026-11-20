"""Tile a clay_frames.py .list (rows clip:t, columns views) into one sheet with labels. Args: <list> <out png> [cell]"""
import sys
from PIL import Image, ImageDraw
rows = [l.split('\t') for l in open(sys.argv[1]).read().strip().split('\n')]; cell = int(sys.argv[3]) if len(sys.argv) > 3 else 300
nc = len(rows[0]) - 1
W = Image.new('RGB', (cell * len(rows), cell * nc), (40, 40, 40)); dr = ImageDraw.Draw(W)
for r, row in enumerate(rows):
    for c, f in enumerate(row[1:]):
        W.paste(Image.open(f).convert('RGB').resize((cell, cell)), (r * cell, c * cell))
    dr.text((r * cell + 4, 4), row[0], fill=(255, 255, 0))
W.save(sys.argv[2]); print('SHEET', sys.argv[2], W.size)
