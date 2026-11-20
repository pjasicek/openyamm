#!/usr/bin/env python3
"""Sheet from clip_frames.py's rows.json: one row per clip, the views side by side. Args: <rows.json> <out.jpg>"""
import json, sys
from PIL import Image, ImageDraw
rows = json.load(open(sys.argv[1]))
W, H = Image.open(rows[0][1][0][0]).size; nf = len(rows[0][1]); nv = len(rows[0][1][0])
sheet = Image.new('RGB', (W * nf * nv + 100, H * len(rows)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
for r, (c, frames) in enumerate(rows):
    d.text((4, r * H + H // 2), c, fill=(0, 0, 0))
    for i, fr in enumerate(frames):
        for v, p in enumerate(fr):
            sheet.paste(Image.open(p).convert('RGB'), (100 + (v * nf + i) * W, r * H))
sheet.save(sys.argv[2], quality=82)
print(sheet.size)
