#!/usr/bin/env python3
"""Quality-pass sheet from glb_check.py renders (pairs before, after): one row per model, native sprite | before eye |
after eye | before three-quarter | after three-quarter, with triangles, coverage and colour.
Usage: before_after_sheet.py <glb_check prefix> <out.png> [--offset <pair>] <id> [...] (glb_check pair order)"""
import json, os, sys
from PIL import Image, ImageDraw
import common
import glb_bounds
prefix, out, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
OFFSET = 0
if ids[0] == '--offset':
    OFFSET, ids = int(ids[1]), ids[2:]
stats = json.load(open(prefix + '.json'))
P = 270
rows = []
for k, sid in enumerate(ids, OFFSET):
    spec = common.load(sid)
    b, a = stats[2 * k], stats[2 * k + 1]
    sprite = Image.open(spec['sprite_path']).convert('RGBA'); sprite = sprite.crop(sprite.getbbox())
    sprite = sprite.resize((int(sprite.width * (P - 40) / sprite.height), P - 40), Image.LANCZOS)
    cells = [sprite] + [Image.open(f'{prefix}_{2 * k + j}_{v}.png').convert('RGBA').resize((240, P))
                        for v in ('eye', 'three_quarter') for j in (0, 1)]
    tb, ta = glb_bounds.info(b['path'])['lod_triangles'], glb_bounds.info(a['path'])['lod_triangles']
    cov = a['eye']['opaque_px'] / b['eye']['opaque_px'] - 1
    label = (f"{sid}: LOD0 {tb[0]} -> {ta[0]} (LOD1 {tb[1]} -> {ta[1]}, LOD2 {tb[2]} -> {ta[2]})  eye coverage "
             f"{cov:+.1%}  mean {b['eye']['mean_srgb']} -> {a['eye']['mean_srgb']}")
    rows.append((cells, label))
W = max(sum(c.width for c in cs) for cs, _ in rows) + 10 * 5
sheet = Image.new('RGBA', (W, len(rows) * (P + 18)), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
for r, (cells, label) in enumerate(rows):
    y = r * (P + 18); d.text((4, y + 2), label + '   [sprite | before eye | after eye | before 3/4 | after 3/4]',
                             fill=(0, 0, 0, 255))
    x = 0
    for c in cells:
        sheet.alpha_composite(c, (x, y + 18 + P - c.height)); x += c.width + 10
sheet.convert('RGB').save(out); print('SHEET', out)
