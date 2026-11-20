#!/usr/bin/env python3
"""4x4 sheet of the grip close-ups (rows: Standing 0, mid, loop seam, AttackMelee impact; columns: front, below, outside, palm side), crops
the centre of each viewer shot. Args: <shot dir> <prefix> <title> <out png>"""
import sys
from PIL import Image, ImageDraw
d, pre, title, out = sys.argv[1:5]; C = 400
rows = ['Standing 0.0 s', 'Standing 1.33 s (mid)', 'Standing 2.67 s (loop seam)', 'AttackMelee 0.479 s (impact)']
cols = ['front', 'below', 'outside', 'palm']
s = Image.new('RGB', (4 * C, 4 * C + 24), (30, 30, 30)); dr = ImageDraw.Draw(s); dr.text((6, 5), title, fill=(255, 255, 255))
for r in range(4):
    for c, v in enumerate(cols):
        im = Image.open(f'{d}/{pre}{r}{v}.png').convert('RGB'); w, h = im.size; m = int(min(w, h) * 0.8)
        im = im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((C, C), Image.LANCZOS)
        ImageDraw.Draw(im).text((5, 5), f'{rows[r]} | {v}', fill=(255, 255, 0)); s.paste(im, (c * C, 24 + r * C))
s.save(out)
