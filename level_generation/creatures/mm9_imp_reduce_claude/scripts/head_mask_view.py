#!/usr/bin/env python3
"""Head faces coloured by tier-A region mask (RGB) and by tier-B / tier-C base colour at the centroid, with a y/z grid, to
place the face/hairline cut. -> review/head_mask_view.png"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_imp.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Imp' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])
X = np.concatenate([p['POSITION'].astype(float) for p in pr]); off = np.cumsum([0] + [len(p['POSITION']) for p in pr])
T = np.concatenate([p['T'] + o for p, o in zip(pr, off)])
UV = np.concatenate([p['TEXCOORD_0'].astype(float) for p in pr])
nb = len(pr[0]['T'])
def samp(name):
    out = []
    for k, base in enumerate(('Imp', 'ImpHead')):
        m = np.asarray(Image.open(HERE / 'work' / f'tex_{base}_{name}.png').convert('RGB'), float); H_, W_ = m.shape[:2]
        TT = T[:nb] if k == 0 else T[nb:]
        uv = UV[TT].mean(1); x = np.clip((uv[:, 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[:, 1] % 1) * H_, 0, H_ - 1).astype(int)
        out.append(m[y, x])
    return np.concatenate(out)
def view(C, yaw, pitch, center, half, size=520, grid=True):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    R1 = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); R2 = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Y = (X - center) @ R1.T @ R2.T
    tri = Y[T]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nn = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
    vis = nn[:, 2] > 0; order = np.argsort(tri[:, :, 2].mean(1))
    im = Image.new('RGB', (size, size), (40, 40, 46)); d = ImageDraw.Draw(im); sc = size / (2 * half)
    for f in order:
        if vis[f]:
            sh = 0.55 + 0.45 * nn[f, 2]
            d.polygon([(p[0] * sc + size / 2, size / 2 - p[1] * sc) for p in tri[f]], fill=tuple(int(c) for c in C[f] * sh))
    if grid:
        for yy in np.arange(0.85, 1.25, 0.025):
            py = size / 2 - (yy - center[1]) * sc; d.line([(0, py), (12, py)], fill=(255, 255, 0)); d.text((14, py - 6), f'{yy:.2f}', fill=(255, 255, 0))
    return im
c = np.array([0, 1.03, 0.2]); h = 0.2
rows = []
for C in (samp('A'), samp('B'), samp('C')):
    ims = [view(C, a, p, c, h) for a, p in ((0, 0), (0.8, 0), (np.pi / 2, 0), (np.pi, 0), (0, -0.6))]
    r = Image.new('RGB', (520 * 5, 520)); [r.paste(im, (520 * i, 0)) for i, im in enumerate(ims)]; rows.append(r)
out = Image.new('RGB', (2600, 520 * 3)); [out.paste(r, (0, 520 * i)) for i, r in enumerate(rows)]
out.save(HERE / 'review' / 'head_mask_view.png'); print('ok')
