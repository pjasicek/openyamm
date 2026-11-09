#!/usr/bin/env python3
"""PeasantDM2 head prim survey for the keep set: per head-prim face of the installed LOD0, the welded component, and on the
head shell (the largest component: face skin, bald scalp, neck, beard sheet in one piece) a texture class from both tiers'
head images sampled at the face's UV centroid and corners: hair (white/grey, low saturation, both tiers) vs skin. Writes
work/head_parts.npz (comp, hairtex, cen) and review/head_parts.png (front/right/back/left: red face window, orange hair-coloured
shell faces, tan skin, blue hair component, green hands, purple small parts). Read-only on the GLB.
Usage: head_parts.py   (env FACE_X, FACE_Y0, FACE_Y1, FACE_Z: the face window, as DM4's make_sets_dm4.py)"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
from set_view import views  # noqa: E402
E = lambda k, d: float(os.environ.get(k, d))  # noqa: E731
FACE_X, FACE_Y0, FACE_Y1, FACE_Z = E('FACE_X', 0.075), E('FACE_Y0', 0.985), E('FACE_Y1', 1.10), E('FACE_Z', 0.03)
doc, b = bglbio.read(HERE / 'before' / 'mm9_phom1.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PHOM1' and 'mesh' in n)
prims = bglbio.prims(doc, b, node['mesh'])
pr = next(p for p in prims if p['material'] == 'PHOM1Head_A')
P = pr['POSITION'].astype(float); T = pr['T']; U = pr['TEXCOORD_0'].astype(float)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
comp = lab[FT[:, 0]]; cnt = np.bincount(comp)
shell = comp == cnt.argmax()
cen = P[T].mean(1)


def sample(img, uv):
    a = np.asarray(img, np.float64) / 255; h, wd = a.shape[:2]
    x = np.clip((uv[:, 0] % 1) * wd, 0, wd - 1).astype(int); y = np.clip((uv[:, 1] % 1) * h, 0, h - 1).astype(int)
    return a[y, x]


hairy = np.zeros(len(T), bool)
votes = np.zeros(len(T))
for t in 'AB':
    img = Image.open(HERE / 'work' / f'tex_PHOM1Head_A_{t}.png').convert('RGB')
    pts = [U[T].mean(1)] + [U[T[:, k]] for k in range(3)] + [(U[T].mean(1) + U[T[:, k]]) / 2 for k in range(3)]
    for uv in pts:
        c = sample(img, uv); mx = c.max(1); mn = c.min(1)
        sat = (mx - mn) / np.maximum(mx, 1e-6)
        votes += (sat < 0.22) & (mx > 0.45)
hairtex = votes >= 0.5 * 14
win = shell & (np.abs(cen[:, 0]) < FACE_X) & (cen[:, 1] > FACE_Y0) & (cen[:, 1] < FACE_Y1) & (cen[:, 2] > FACE_Z)
print('head prim faces', len(T), 'components', {int(k): int(v) for k, v in enumerate(cnt)})
print('shell', int(shell.sum()), 'face window', int(win.sum()), 'hair-coloured outside window', int((shell & hairtex & ~win).sum()),
      'skin outside window', int((shell & ~hairtex & ~win).sum()))
for nm, m in (('hair-col', shell & hairtex & ~win), ('skin', shell & ~hairtex & ~win)):
    c = cen[m]
    print(' ', nm, 'y', np.percentile(c[:, 1], [0, 10, 50, 90, 100]).round(3), 'z', np.percentile(c[:, 2], [0, 10, 50, 90, 100]).round(3))
np.savez(HERE / 'work' / 'head_parts.npz', comp=comp, hairtex=hairtex, cen=cen, shell=shell, win=win)
rgb = np.full((len(T), 3), 120)
big = cnt[comp] > 1000
rgb[shell & ~hairtex] = (205, 160, 120); rgb[shell & hairtex] = (240, 140, 30); rgb[win] = (220, 40, 40)
rgb[~shell & big & (np.abs(cen[:, 0]) < 0.3)] = (60, 90, 230)
rgb[np.abs(cen[:, 0]) > 0.3] = (40, 200, 40)
rgb[~big & (np.abs(cen[:, 0]) < 0.3)] = (170, 80, 200)
m = np.abs(cen[:, 0]) < 0.3
views(P, T[m], rgb[m], (-0.15, 0.15, 0.86, 1.24), HERE / 'review' / 'head_parts.png', size=420)
