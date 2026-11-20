#!/usr/bin/env python3
"""Assemble the clip sheet from clip_sheet.py's frame list. Args: <out.png>"""
import json, sys
from PIL import Image, ImageDraw
out = sys.argv[1]; d = json.load(open(out + '.json')); K = d['K']
W = Image.new('RGB', (300 * K * 2, 230 * len(d['rows'])), (255, 255, 255)); dr = ImageDraw.Draw(W)
for r, (clip, row) in enumerate(d['rows']):
    for c, p in enumerate(row):
        W.paste(Image.open(p), (300 * c, 230 * r + 20))
    dr.text((4, 230 * r + 4), clip, fill=(0, 0, 0))
W.save(out)
