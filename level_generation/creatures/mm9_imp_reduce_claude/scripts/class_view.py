#!/usr/bin/env python3
"""Rest-pose orthographic raster of the installed LOD0 coloured by the per-GLB-face set labels of work/glb_sets_<tag>.npz
(keep = grey, group 0 = tan, group 1 = blue, group 2 = green, group 3 = magenta, group 4 = orange), shaded by the face normal.
Views: front (+Z), 3/4, side (+X), back, top; whole body row and head row. Usage: class_view.py <tag> -> review/classes_<tag>.png"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
tag = sys.argv[1]
doc, b = gb.read(HERE / 'before' / 'mm9_imp.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Imp' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])
S = np.load(HERE / 'work' / f'glb_sets_{tag}.npz')
X = np.concatenate([p['POSITION'].astype(float) for p in pr]); off = np.cumsum([0] + [len(p['POSITION']) for p in pr])
T = np.concatenate([p['T'] + o for p, o in zip(pr, off)])
col = np.array([[205, 170, 120], [80, 130, 230], [80, 200, 90], [210, 80, 210], [240, 150, 40], [40, 220, 220]], float)
C = np.where(S['keep'][:, None], np.array([[150, 150, 150]], float), col[np.clip(S['group'], 0, 5)])
import os
for lab in os.environ.get('CV_LABELS', '').split(','):
    if lab:
        C[S[lab]] = [255, 40, 40]


def view(yaw, pitch, center, half, size=520):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    R1 = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); R2 = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Y = (X - center) @ R1.T @ R2.T                      # camera looks along -z (towards the model from +z)
    tri = Y[T]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nn = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
    vis = nn[:, 2] > 0; order = np.argsort(tri[:, :, 2].mean(1))
    im = Image.new('RGB', (size, size), (40, 40, 46)); d = ImageDraw.Draw(im)
    sc = size / (2 * half)
    for f in order:
        if not vis[f]:
            continue
        sh = 0.35 + 0.65 * nn[f, 2]
        pts = [((p[0]) * sc + size / 2, size / 2 - p[1] * sc) for p in tri[f]]
        d.polygon(pts, fill=tuple(int(c) for c in C[f] * sh))
    return im


rows = []
for center, half in ((np.array([0, 0.55, 0.0]), 0.62), (np.array([0, 1.03, 0.2]), 0.2)):
    ims = [view(a, p, center, half) for a, p in ((0, 0), (0.8, 0), (np.pi / 2, 0), (np.pi, 0), (0, -np.pi / 2 + 0.01))]
    row = Image.new('RGB', (520 * len(ims), 520))
    for i, im in enumerate(ims):
        row.paste(im, (520 * i, 0))
    rows.append(row)
out = Image.new('RGB', (rows[0].width, 520 * len(rows)))
for i, r in enumerate(rows):
    out.paste(r, (0, 520 * i))
out.save(HERE / 'review' / f'classes_{tag}.png'); print('WROTE', HERE / 'review' / f'classes_{tag}.png')
