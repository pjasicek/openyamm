#!/usr/bin/env python3
"""Family review sheet (review/family_<first>.png): one row per season, native x2 sprite (scaled to the model's
rendered height) | LOD0 eye level | three-quarter | side (Eevee, review.py) | LOD1 | LOD2 | LOD3 (lod_check.py common
size). Every model of a family shares its LOD0 bounds height, so the renders share one framing.
Usage: family_sheet.py <id> [<id> ...]"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
import common
P = 300


def fit(im, h):
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)


rows = []
for sid in sys.argv[1:]:
    spec = common.load(sid); W = spec['work']
    eye = Image.open(os.path.join(W, 'rv_Tree_eye.png')).convert('RGBA')
    box = eye.getbbox(); tree_px = (box[3] - box[1]) * P / eye.height
    panels = []
    sprite = Image.open(spec['sprite_path']).convert('RGBA'); sprite = sprite.crop(sprite.getbbox())
    s = fit(sprite, int(tree_px))
    cell = Image.new('RGBA', (max(s.width, 200), P)); cell.alpha_composite(s, ((cell.width - s.width) // 2, P - s.height - int((eye.height - box[3]) * P / eye.height)))
    panels.append(cell)
    for v in ('eye', 'three_quarter', 'side'):
        panels.append(fit(Image.open(os.path.join(W, f'rv_Tree_{v}.png')).convert('RGBA'), P))
    for n in ('Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3'):
        panels.append(fit(Image.open(os.path.join(W, f'lc_common_{n}_eye.png')).convert('RGBA'), P))
    model = json.load(open(os.path.join(W, 'model.json')))
    label = (f"{sid} -> {spec['output']}  LOD tris {model['lod_triangles']}  "
             f"{model['file_bytes'] / 1e6:.1f} MB  LOD0 height (m) {model['bounds_max'][1] - model['bounds_min'][1]:.3f}")
    rows.append((panels, label))
width = max(sum(p.width for p in ps) for ps, _ in rows)
sheet = Image.new('RGBA', (width, len(rows) * (P + 20)), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
heads = ['native x2', 'LOD0 eye', 'LOD0 three-quarter', 'LOD0 side', 'LOD1', 'LOD2', 'LOD3 impostor']
for r, (panels, label) in enumerate(rows):
    x = 0; y = r * (P + 20)
    d.text((4, y + 4), label, fill=(0, 0, 0, 255))
    for k, p in enumerate(panels):
        sheet.alpha_composite(p, (x, y + 20)); d.text((x + 4, y + 22), heads[k], fill=(30, 30, 30, 255)); x += p.width
out = os.path.join(common.TREES, 'review', f'family_{sys.argv[1]}.png')
sheet.convert('RGB').save(out)
print('SHEET', out)
