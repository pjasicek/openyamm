#!/usr/bin/env python3
"""Horizontal slices through the robe wall and the boots at given clip times: the ground truth of what is inside what.
Args: <glb> <out png> <clip:time,...> [heights, comma separated]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out, poses = sys.argv[1:4]
H = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else [0.12, 0.2, 0.3, 0.4]
m = Model(Glb(glb))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
idx = next(i for i, p in enumerate(m.primitives) if p['skinned'] and (p['positions'][:, 1].min() < 0.05))
pr = m.primitives[idx]
P, T = pr['positions'], pr['triangles']
_, inv = np.unique(np.round(P, 4), axis=0, return_inverse=True)
inv = inv.ravel()
e = np.r_[inv[T[:, [0, 1]]], inv[T[:, [1, 2]]], inv[T[:, [0, 2]]]]
n, cl = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(inv.max() + 1, inv.max() + 1)), directed=False)
part = cl[inv]
legs = []
for s in 'LR':
    ids = [names.index(f'Bip01 {s} {b}') for b in ('Foot', 'Toe0')]
    legs.append(int(np.bincount(part, np.where(np.isin(pr['joints'], ids), pr['weights'], 0).sum(1)).argmax()))
fp = part[T[:, 0]]
isleg = np.isin(fp, legs)
poses = [p.split(':') for p in poses.split(',')]


def slice_tris(x, tris, h):
    a, b, c = x[tris[:, 0]], x[tris[:, 1]], x[tris[:, 2]]
    segs = []
    for u, v, w in ((a, b, c), (b, c, a), (c, a, b)):
        pass
    d = np.stack([a[:, 1], b[:, 1], c[:, 1]], 1) - h
    for f in np.where((d.min(1) < 0) & (d.max(1) > 0))[0]:
        pts = []
        tri = (a[f], b[f], c[f])
        for i in range(3):
            j = (i + 1) % 3
            if d[f, i] * d[f, j] < 0:
                s = d[f, i] / (d[f, i] - d[f, j])
                pts.append(tri[i] + s * (tri[j] - tri[i]))
        if len(pts) == 2:
            segs.append(pts)
    return segs


C = 240
S = Image.new('RGB', (C * len(poses), C * len(H)), 'white')
d = ImageDraw.Draw(S)
scale = 300
for c, (clip, t) in enumerate(poses):
    x = m.skinned_positions(m.world(m.sample(clip, float(t))))[idx][0]
    root = np.median(x[np.isin(part, legs)], 0)
    for r, h in enumerate(H):
        ox, oy = C * c + C / 2, C * r + C / 2
        for tris, col in ((T[~isleg], 'black'), (T[isleg], 'red')):
            for g in slice_tris(x, tris, h):
                d.line([(ox + (g[0][0] - root[0]) * scale, oy + (g[0][2] - root[2]) * scale), (ox + (g[1][0] - root[0]) * scale, oy + (g[1][2] - root[2]) * scale)], fill=col, width=2 if col == 'red' else 1)
        d.rectangle([C * c, C * r, C * c + C - 1, C * r + C - 1], outline=(200, 200, 200))
        d.text((C * c + 4, C * r + 4), f'{clip} {t} y={h}', fill=(0, 0, 200))
S.save(out)
