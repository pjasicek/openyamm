#!/usr/bin/env python3
"""Rest-pose painter's-algorithm sheet (PIL) of the per-face classes and the keep set (make_sets.py), to check the labels:
row 1 whole body, row 2 head; front / 3-4 / side / back, each as class colours and keep (red) beside it.
Usage: class_sheet.py <tag> <out.png>"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag, out = sys.argv[1:3]
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_zombie.glb', 'Zombie')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CLS = json.load(open(HERE / 'work' / 'classes.json'))['names']
FV = np.concatenate([D[k]['P'][D[k]['T']] for k in ('Zombie_A', 'ZombieHead_A', 'ZombieTorso')])
PAL = np.array([[31, 119, 180], [174, 199, 232], [255, 127, 14], [255, 187, 120], [44, 160, 44], [152, 223, 138], [214, 39, 40],
                [255, 152, 150], [148, 103, 189], [197, 176, 213], [140, 86, 75], [196, 156, 148], [227, 119, 194], [127, 127, 127],
                [188, 189, 34], [23, 190, 207]], float)
S = 420
tiles = []
for sel, yaws in ((None, (0, 45, 90, 180)), (1.5, (0, 45, 90, 180))):
    for yaw in yaws:
        a = np.radians(yaw); R = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
        X = FV @ R.T
        m = ~s['lining']
        if sel is not None:
            m &= FV[:, :, 1].mean(1) > sel
        nv = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]); nz = nv[:, 2] / np.maximum(np.linalg.norm(nv, axis=1), 1e-12)
        m &= nz > 0
        idx = np.flatnonzero(m); idx = idx[np.argsort(X[idx][:, :, 2].mean(1))]
        lo = X[m][:, :, :2].reshape(-1, 2).min(0); hi = X[m][:, :, :2].reshape(-1, 2).max(0); sc = (S - 20) / (hi - lo).max()
        for mode in ('cls', 'keep'):
            im = Image.new('RGB', (S, S), (255, 255, 255)); dr = ImageDraw.Draw(im)
            for f in idx:
                c = PAL[s['cls'][f] % 16] if mode == 'cls' else (np.array([220, 30, 30.]) if s['keep'][f] else np.array([150, 150, 150.]))
                c = tuple(int(v) for v in c * (0.35 + 0.65 * nz[f]))
                pts = [(10 + (p[0] - lo[0]) * sc, S - 10 - (p[1] - lo[1]) * sc) for p in X[f, :, :2]]
                dr.polygon(pts, fill=c)
            tiles.append(im)
W = Image.new('RGB', (S * 8, S * 2 + 40), (255, 255, 255)); dr = ImageDraw.Draw(W)
for i, t in enumerate(tiles):
    W.paste(t, ((i % 8) * S, (i // 8) * S))
for i, c in enumerate(CLS):
    dr.rectangle([10 + i * 200, S * 2 + 10, 30 + i * 200, S * 2 + 30], fill=tuple(int(v) for v in PAL[i % 16])); dr.text((35 + i * 200, S * 2 + 14), c, fill=(0, 0, 0))
W.save(out); print('SHEET', out)
