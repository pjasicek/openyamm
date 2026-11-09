"""Compose frames.json (rows of [path, label]) into a sheet with COLS columns per row block. Args: <dir> <out> [cols]"""
import json, sys
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 8
rows = json.load(open(d + '/frames.json'))
W, H = Image.open(rows[0][0][0]).size
blocks = []
for row in rows:
    for i in range(0, len(row), cols): blocks.append(row[i:i + cols])
sheet = Image.new('RGB', (W * cols, H * len(blocks)), (40, 40, 40)); dr = ImageDraw.Draw(sheet)
for r, blk in enumerate(blocks):
    for c, (p, l) in enumerate(blk):
        sheet.paste(Image.open(p).convert('RGB'), (c * W, r * H)); dr.text((c * W + 6, r * H + 6), l, fill=(255, 255, 0))
sheet.save(out); print('SHEET', out, sheet.size)
