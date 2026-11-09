#!/usr/bin/env python3
"""Full body MM9 vs ours: top row MM9's renders (mirrored to true handedness, as the installed model), bottom row our viewer shots.
Args: <shot dir> <prefix> <out png>"""
import sys
from PIL import Image, ImageOps, ImageDraw
d, pre, out = sys.argv[1:4]; C = 520
mm = [('q34', 'quarter'), ('front', 'front'), ('left', 'right'), ('back', 'back'), ('right', 'left')]
o = Image.new('RGB', (C * 5, C * 2), (40, 40, 40)); dr = ImageDraw.Draw(o)
def sq(im):
    w, h = im.size; s = min(w, h); return im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((C, C))
for k, (a, b) in enumerate(mm):
    o.paste(sq(ImageOps.mirror(Image.open(f'review/mm9/sk_{a}.png').convert('RGB'))), (k * C, 0)); dr.text((k * C + 6, 6), 'MM9 ' + a + ' (mirrored)', fill=(255, 255, 0))
    o.paste(sq(Image.open(f'{d}/{pre}_{b}.png').convert('RGB')), (k * C, C)); dr.text((k * C + 6, C + 6), 'ours ' + b, fill=(255, 255, 0))
o.save(out); print('SHEET', out)
