"""Compose clip_sheet.py frames into one sheet. Args: <frames dir> <out png>"""
import json, sys
from PIL import Image, ImageDraw
d, out = sys.argv[1:3]
rows = json.load(open(d + '/frames.json'))
im0 = Image.open(rows[0][0][0]); W, H = im0.size
sheet = Image.new('RGB', (W * max(len(r) for r in rows), H * len(rows)), (200, 200, 200))
dr = ImageDraw.Draw(sheet)
for r, row in enumerate(rows):
    for c, (p, label) in enumerate(row):
        sheet.paste(Image.open(p).convert('RGB'), (c * W, r * H)); dr.text((c * W + 4, r * H + 4), label, fill=(0, 0, 0))
sheet.save(out)
