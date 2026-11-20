"""Labelled before/after grid. Args: <out> <cols> <tile w> <label|img> ...  ('#text' starts a row label; '-' an empty tile)"""
import sys
from PIL import Image, ImageDraw
out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = sys.argv[4:]
rows, cur = [], None
for it in items:
    if it.startswith('#'):
        cur = [it[1:], []]; rows.append(cur)
    else:
        cur[1].append(it)
th = None; tiles = []
for lab, ims in rows:
    r = []
    for p in ims:
        if p == '-': r.append(None); continue
        im = Image.open(p).convert('RGB'); th = th or int(im.height * tw / im.width); r.append(im.resize((tw, th)))
    tiles.append((lab, r))
LW = 150
o = Image.new('RGB', (LW + cols * tw, len(tiles) * th), (40, 40, 40)); d = ImageDraw.Draw(o)
for i, (lab, r) in enumerate(tiles):
    d.text((6, i * th + 6), lab.replace('|', '\n'), fill=(255, 255, 0))
    for j, im in enumerate(r):
        if im: o.paste(im, (LW + j * tw, i * th))
o.save(out); print('SHEET', out, o.size)
