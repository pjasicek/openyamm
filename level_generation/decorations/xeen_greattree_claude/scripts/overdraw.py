#!/usr/bin/env python3
"""Overdraw gate: leaf-card layers per covered pixel for every LOD of work/<id>/tree_export.blend, from the front
(eye), three-quarter and side review cameras (overdraw_render.py). Per LOD and view: mean and 95th percentile of the
alpha-tested card layers over covered pixels (tree pixels, opaque bark/shell included, which pass no card layer in
front of them as 0). Writes work/<id>/overdraw_<tag>.json and the heat map sheet review/<id>/overdraw_<tag>.png
(rows LOD0..LOD3, columns front / three-quarter / side; 0 layers dark grey, 1 blue ... 6+ red).
Targets (coordinator, 2026-10-16): mean ~2.5-3 at LOD0 and LOD1, ~2 at LOD2.
Usage: overdraw.py <id> [tag] [blend]"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
import common
spec = common.load(); W = spec['work']; R = spec['review']
extra = common.extra_args()
tag = extra[0] if extra else 'now'
blend = extra[1] if len(extra) > 1 else os.path.join(W, 'tree_export.blend')
out = os.path.join(W, f'overdraw_{tag}')
frame = json.load(open(os.path.join(W, 'impostor.json')))['size_m']
subprocess.run([common.BLENDER, '--background', '--python', os.path.join(common.TREES, 'scripts', 'overdraw_render.py'),
                '--', spec['id'], blend, out, str(frame)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
NAMES = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']
VIEWS = ['eye', 'three_quarter', 'side']
CONTEXT = ['foot', 'green4k']     # the great tree's own gate views (LOD0/LOD1 matter there)
stats = {}


def colour(layers):
    stops = np.array([[60, 60, 66], [40, 80, 220], [40, 200, 220], [60, 210, 60], [240, 220, 40], [240, 120, 30],
                      [220, 30, 30]], float)
    t = np.clip(layers, 0, 6)
    i = np.minimum(t.astype(int), 5); f = (t - i)[..., None]
    return stops[i] * (1 - f) + stops[i + 1] * f


tiles = []
for n in NAMES:
    row = []
    per = {}
    for v in VIEWS + CONTEXT:
        a = np.load(os.path.join(out, f'{n}_{v}.npy')); layers, cov = a[..., 0], a[..., 1] > 0.5
        vals = layers[cov]
        per[v] = {'mean': round(float(vals.mean()), 2), 'p95': round(float(np.percentile(vals, 95)), 2),
                  'covered_px': int(cov.sum())}
        img = np.full(layers.shape + (3,), 150.0); img[cov] = colour(layers)[cov]
        row.append(Image.fromarray(img.astype(np.uint8)))
    stats[n] = {'views': per, 'mean': round(float(np.mean([per[v]['mean'] for v in VIEWS])), 2),
                'foot': per['foot'], 'green4k': per['green4k'],
                'p95': round(float(np.mean([per[v]['p95'] for v in VIEWS])), 2)}
    tiles.append(row)
json.dump(stats, open(os.path.join(W, f'overdraw_{tag}.json'), 'w'), indent=1)
tw, th = tiles[0][0].size
widths = [im.width for im in tiles[0]]
sheet = Image.new('RGB', (sum(widths) + 160, th * 4 + 30), (150, 160, 175)); d = ImageDraw.Draw(sheet)
d.text((6, 6), f"{spec['id']} leaf-card layers per covered pixel ({tag}); columns front / three-quarter / side; "
       "(+ foot, green4k) 0 grey, 1 blue, 2 cyan, 3 green, 4 yellow, 5 orange, 6+ red", fill=(0, 0, 0))
for r, n in enumerate(NAMES):
    for c, im in enumerate(tiles[r]):
        sheet.paste(im, (160 + sum(widths[:c]), 30 + r * th))
    d.text((6, 30 + r * th + 10), f"{n}\nmean {stats[n]['mean']}\np95 {stats[n]['p95']}\nfoot {stats[n]['foot']['mean']}"
           f" / {stats[n]['foot']['p95']}\ngreen4k {stats[n]['green4k']['mean']}", fill=(0, 0, 0))
sheet.save(os.path.join(R, f'overdraw_{tag}.png'))
print('OVERDRAW', spec['id'], tag, {n[-4:] if n != 'Tree' else 'LOD0': (stats[n]['mean'], stats[n]['p95'], 'foot',
      stats[n]['foot']['mean'], stats[n]['foot']['p95'], 'green4k', stats[n]['green4k']['mean']) for n in NAMES})
