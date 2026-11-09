#!/usr/bin/env python3
"""Review sheet (review/sheet.png): one row per bush on a neutral grey, columns LOD0 front / three-quarter / top, then
LOD1 and LOD2 front and top, all at the same camera distance (true relative size). Each row is labelled with its
height, footprint and triangles per level; under each LOD0 front the mean colour and coverage (alpha > 0.5).
Also review/<id>.png per bush. Usage: sheet.py [id ...]"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
from bushes import BUSHES   # noqa: E402

REV = os.path.join(HERE, 'work', 'review')
COLUMNS = [('LOD0', 'front'), ('LOD0', 'three_quarter'), ('LOD0', 'top'), ('LOD1', 'front'), ('LOD1', 'top'),
           ('LOD2', 'front'), ('LOD2', 'top')]
BG = (150, 156, 164, 255)
ids = sys.argv[1:] or list(BUSHES)
tile = Image.open(os.path.join(REV, f'{ids[0]}_LOD0_front.png')).size[0]
label_h = 40
rows = []
for bid in ids:
    info = json.load(open(os.path.join(HERE, 'work', f'{bid}_build.json')))
    lods = info['lods']
    lo, hi = lods['0']['min'], lods['0']['max']
    final = os.path.join(HERE, 'work', f'{bid}_final.json')
    tris = json.load(open(final))['triangles'] if os.path.exists(final) else [lods[k]['tris'] for k in '012']
    row = Image.new('RGBA', (tile * len(COLUMNS), tile + 2 * label_h), BG)
    d = ImageDraw.Draw(row)
    d.text((6, 4), f"{bid}: {BUSHES[bid]['note']}  height {hi[2]:.2f} m, footprint {hi[0] - lo[0]:.2f} x "
                   f"{hi[1] - lo[1]:.2f} m  triangles LOD0/1/2 {tris[0]}/{tris[1]}/{tris[2]}", fill=(20, 20, 20, 255))
    for k, (level, view) in enumerate(COLUMNS):
        im = Image.open(os.path.join(REV, f'{bid}_{level}_{view}.png')).convert('RGBA')
        row.alpha_composite(im, (k * tile, label_h))
        a = np.asarray(im)
        inside = a[..., 3] > 127
        mean = a[..., :3][inside].mean(0).round().astype(int).tolist() if inside.any() else [0, 0, 0]
        d.text((k * tile + 6, label_h + tile + 4), f'{level} {view}  mean {mean} cover {inside.mean():.3f}',
               fill=(20, 20, 20, 255))
    row.convert('RGB').save(os.path.join(HERE, 'review', f'{bid}.png'))
    rows.append(row)
sheet = Image.new('RGB', (rows[0].size[0], sum(r.size[1] for r in rows)), BG[:3])
y = 0
for r in rows:
    sheet.paste(r.convert('RGB'), (0, y)); y += r.size[1]
if len(ids) == len(BUSHES):
    sheet.save(os.path.join(HERE, 'review', 'sheet.png'))
print('SHEET', [os.path.join(HERE, 'review', f'{b}.png') for b in ids])
