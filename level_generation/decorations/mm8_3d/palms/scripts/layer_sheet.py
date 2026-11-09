#!/usr/bin/env python3
"""Heat-map sheets of the frond-card layers measured by layers.py: review/<id>/layers.png (LOD0-2 x front,
three-quarter, side; 0 layers transparent, 1 dark blue ... 8+ white-yellow, labels with mean and 95th percentile per
covered pixel) and review/layers_overview.png (every palm's row). Usage: layer_sheet.py [<tag>] (tag: suffix of the
overview, e.g. 'before')"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc
tag = sys.argv[1] if len(sys.argv) > 1 else ''
STOPS = [(0, (40, 40, 120)), (1, (30, 60, 200)), (2, (0, 170, 170)), (3, (60, 200, 60)), (4, (230, 220, 40)),
         (6, (240, 120, 20)), (8, (230, 30, 30)), (12, (255, 255, 255))]


def heat(n):
    ts = np.array([s[0] for s in STOPS], float); cs = np.array([s[1] for s in STOPS], float)
    rgb = np.stack([np.interp(n, ts, cs[:, k]) for k in range(3)], -1)
    img = np.dstack([rgb, np.where(n >= 0.5, 255, 0)]).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


rows = []
for sid in pc.ORDER:
    W = pc.work(sid)
    st = json.load(open(os.path.join(W, 'layers.json')))
    tiles = []
    for lod in ('Plant', 'Plant_LOD1', 'Plant_LOD2'):
        for view in ('front', 'three_quarter', 'side'):
            n = np.load(os.path.join(W, f'layers_{lod}_{view}.npy'))
            t = Image.new('RGBA', (n.shape[1], n.shape[0] + 30), (150, 150, 150, 255))
            t.alpha_composite(heat(n), (0, 30))
            s = st[f'{lod}/{view}']
            ImageDraw.Draw(t).text((4, 2), f"{sid} {lod.replace('Plant_', '').replace('Plant', 'LOD0')} {view}\n"
                                   f"mean {s['mean']:.2f} p95 {s['p95']:.1f}", fill=(0, 0, 0, 255))
            tiles.append(t.resize((t.width // 2, t.height // 2), Image.LANCZOS))
    row = Image.new('RGBA', (sum(t.width for t in tiles), tiles[0].height), (150, 150, 150, 255)); x = 0
    for t in tiles:
        row.paste(t, (x, 0)); x += t.width
    row.convert('RGB').save(os.path.join(pc.review(sid), f'layers{"_" + tag if tag else ""}.png'))
    rows.append(row)
sheet = Image.new('RGB', (rows[0].width, sum(r.height for r in rows) + 24), (150, 150, 150)); y = 24
ImageDraw.Draw(sheet).text((4, 4), 'frond-card layers per pixel (alpha-tested, no depth test): blue 1, cyan 2, green 3, '
                           'yellow 4, orange 6, red 8, white 12+', fill=(0, 0, 0))
for r in rows:
    sheet.paste(r.convert('RGB'), (0, y)); y += r.height
sheet.save(os.path.join(pc.PALMS, 'review', f'layers_overview{"_" + tag if tag else ""}.png'))
print('SHEET', os.path.join(pc.PALMS, 'review', f'layers_overview{"_" + tag if tag else ""}.png'))
