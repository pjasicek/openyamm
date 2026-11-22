#!/usr/bin/env python3
"""Contact sheet of 16:9 images (squares letterboxed): sheet.py <out.jpg> <columns> <tile px> <img> [<img> ...]"""
import sys

from PIL import Image, ImageDraw

out, cols, tile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
paths = sys.argv[4:]
rows = (len(paths) + cols - 1) // cols
th = tile * 9 // 16
sheet = Image.new('RGB', (cols * tile, rows * th), 'black')
draw = ImageDraw.Draw(sheet)
for i, p in enumerate(paths):
    im = Image.open(p).convert('RGB')
    im.thumbnail((tile, th))
    x, y = (i % cols) * tile, (i // cols) * th
    sheet.paste(im, (x, y))
    draw.text((x + 4, y + 4), p.rsplit('/', 1)[-1], fill='red')
sheet.save(out, quality=88)
