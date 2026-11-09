#!/usr/bin/env python3
"""Shaded wireframe of the head set (painter's algorithm, ortho), coloured by part, for shape work.
Usage: wire_view.py <mesh npz> <out png> <view front|side|q34> [cx cz half]  (mesh space; front looks along +y)"""
import sys, numpy as np
from PIL import Image, ImageDraw
D = np.load(sys.argv[1]); co, tri, mat, comp = D['co'], D['tri'], D['mat'], D['comp']; mn = [str(x) for x in D['matnames']]
t = tri[mat == mn.index('EboraHead')]
view = sys.argv[3]; cx, cz, hw = (float(x) for x in sys.argv[4:7]) if len(sys.argv) > 6 else (0.0, 0.86, 0.09)
d = {'front': np.array([0, 1.0, 0]), 'side': np.array([-1.0, 0, 0]), 'q34': np.array([-0.7, 0.7, 0])}[view]; d /= np.linalg.norm(d)
up = np.array([0, 0, 1.0]); r = np.cross(d, up); r /= np.linalg.norm(r)
S = 1100; P = co[t]; sx = ((P @ r) - (cx if view == 'front' else (np.array([cx, 0, 0]) @ r + 0.0))) ; sx = (P @ r - P.reshape(-1, 3).mean(0) @ r * (view != 'front') - cx * (view == 'front')) / (2 * hw) + 0.5
sy = 0.5 - (P[..., 2] - cz) / (2 * hw); dep = (P @ d).mean(1)
n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pc = comp[t[:, 0]]
COL = {0: (200, 150, 120), 1: (60, 60, 80), 3: (150, 150, 150), 4: (90, 70, 110), 6: (240, 240, 240), 7: (220, 120, 60), 9: (200, 60, 90)}
im = Image.new('RGB', (S, S), (30, 30, 30)); dr = ImageDraw.Draw(im)
for i in np.argsort(-dep):
    if n[i] @ d > 0.05: continue
    sh = 0.35 + 0.65 * abs(n[i] @ d); c = tuple(int(v * sh) for v in COL.get(int(pc[i]), (255, 0, 255)))
    pts = [(float(sx[i, k] * S), float(sy[i, k] * S)) for k in range(3)]
    dr.polygon(pts, fill=c, outline=(0, 0, 0))
im.save(sys.argv[2])
