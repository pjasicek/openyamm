#!/usr/bin/env python3
"""Before/after comparison sheet from two sheets made by sheet_frames.py (head_closeups.py or glb_frames.py output)
with the same rows: each row of <before> followed by the same row of <after>, labelled. Rows are cut from the
composed sheets themselves (glb_frames.py reuses its tile paths, so a later run overwrites an earlier run's tiles).
Usage: compare_rows.py <before png> <after png> <out png> [title]"""
import sys
from PIL import Image, ImageDraw
b, a, out = sys.argv[1:4]
title = sys.argv[4] if len(sys.argv) > 4 else ''


def rows(p):
    names = [l.split('\t')[0] for l in open(p + '.list').read().splitlines()]
    im = Image.open(p).convert('RGB')
    h = im.height // len(names)
    return names, [im.crop((0, k * h, im.width, (k + 1) * h)) for k in range(len(names))]


nb, rb = rows(b)
na, ra = rows(a)
w, h = max(rb[0].width, ra[0].width), rb[0].height
top = 28 if title else 0
sheet = Image.new('RGB', (w, top + h * 2 * len(rb)), (30, 30, 30))
d = ImageDraw.Draw(sheet)
if title:
    d.text((8, 8), title, fill=(255, 255, 255))
for i in range(len(rb)):
    for k, (im, name, tag, col) in enumerate(((rb[i], nb[i], 'BEFORE', (255, 120, 120)),
                                              (ra[i], na[i], 'AFTER', (120, 255, 120)))):
        oy = top + (2 * i + k) * h
        sheet.paste(im, (0, oy))
        d.rectangle((0, oy, 220, oy + 22), fill=(30, 30, 30))
        d.text((6, oy + 6), f'{tag} {name} (48 fps)', fill=col)
sheet.save(out)
print('COMPARE', out, sheet.size)
