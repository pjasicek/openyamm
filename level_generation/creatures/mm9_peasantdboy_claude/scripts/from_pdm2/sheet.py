#!/usr/bin/env python3
"""Labelled contact sheet. Usage: sheet.py <out png> <cell height> "<row label>=img1,img2,..." ...  (images scaled to the
cell height; 'mm9:<tier>:<view>' crops a view from references_hd/mm9_views_<tier>.png: q34, front, left, back, right)"""
import sys
from PIL import Image, ImageDraw
out, H = sys.argv[1], int(sys.argv[2])
VIEWS = ['q34', 'front', 'left', 'back', 'right']
def load(s):
    if s.startswith('mm9:'):
        _, t, v = s.split(':')
        im = Image.open(f'references_hd/mm9_views_{t}.png').convert('RGB')
        w = im.width // 5; i = VIEWS.index(v)
        im = im.crop((i * w + w // 6, 0, (i + 1) * w - w // 6, im.height))
        return im
    return Image.open(s).convert('RGB')
rows = []
for arg in sys.argv[3:]:
    label, files = arg.split('=', 1)
    ims = [load(f) for f in files.split(',')]
    ims = [im.resize((max(1, int(im.width * H / im.height)), H)) for im in ims]
    rows.append((label, ims))
W = max(sum(im.width for im in ims) for _, ims in rows)
sheet = Image.new('RGB', (W, H * len(rows)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for r, (label, ims) in enumerate(rows):
    x = 0
    for im in ims:
        sheet.paste(im, (x, r * H)); x += im.width
    d.text((6, r * H + 4), label, fill=(255, 255, 0))
sheet.save(out)
print('SHEET', out, sheet.size)
