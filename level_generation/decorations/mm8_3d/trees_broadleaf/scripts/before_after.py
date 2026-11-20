#!/usr/bin/env python3
"""review/<id>/before_after.png: the v1 sheet row (sprite | LOD0 front | three-quarter | side, then the LODs at a
common size; saved as review/<id>/v1_*.png before the 2026-10-16 reduction) above the same row of the current build,
each labelled with its LOD triangle counts. Usage: before_after.py <id> "<v1 triangles>" """
import json, os, sys
from PIL import Image, ImageDraw
import common
spec = common.load(); R = spec['review']; W = spec['work']
before_tris = common.extra_args()[0] if common.extra_args() else ''
after_tris = open(os.path.join(W, 'validation.txt')).read().split('VALID LOD triangles')[1].split('bounds')[0].strip()


def row(compare, lods, label):
    a = Image.open(os.path.join(R, compare)).convert('RGB')
    l = Image.open(os.path.join(R, lods)).convert('RGB')
    l = l.crop((0, 0, l.width, 440)); l = l.resize((int(l.width * a.height / l.height), a.height))
    r = Image.new('RGB', (a.width + l.width, a.height + 28), (150, 160, 175))
    r.paste(a, (0, 28)); r.paste(l, (a.width, 28))
    ImageDraw.Draw(r).text((6, 6), label, fill=(0, 0, 0))
    return r


rows = [row('v1_compare.png', 'v1_lod_consistency.png', f'BEFORE (v1)  LOD triangles {before_tris}'),
        row('compare.png', 'lod_consistency.png', f'AFTER (reduced + colour lift)  LOD triangles {after_tris}')]
w = max(r.width for r in rows)
out = Image.new('RGB', (w, sum(r.height for r in rows)), (150, 160, 175)); y = 0
for r in rows:
    out.paste(r, (0, y)); y += r.height
out.save(os.path.join(R, 'before_after.png'))
print('BEFORE_AFTER', os.path.join(R, 'before_after.png'), before_tris, '->', after_tris)
