#!/usr/bin/env python3
"""Faces of a reduced mesh (work/mesh_<tag>.npz) whose UV triangle leaves the source's UV coverage (the source triangles of
the same material rasterised at 1024 px, dilated 1 px): those sample the gutter or another chart. Prints count, area and
where; writes work/uvout_<tag>.npy (per face fraction of 19 samples outside). Usage: uv_outside.py <tag>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
tag = sys.argv[1]; R = 1024
def load(p):
    d = np.load(p); return d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
SV, SF, SW = load('work/mesh_in.npz'); V, F, W = load(f'work/mesh_{tag}.npz')
smat = (SW[:, 0, 0] // 2).astype(int); mat = (W[:, 0, 0] // 2).astype(int)
cov = {}
for m in np.unique(smat):
    im = Image.new('L', (R, R), 0); dr = ImageDraw.Draw(im)
    for t in SW[smat == m]:
        uv = t - [2 * m, 0]
        if np.abs(uv - uv[0]).max() < 1e-9: continue                  # lining texel
        dr.polygon([(u * R, (1 - v) * R) for u, v in uv], fill=255)
    cov[m] = ndimage.binary_dilation(np.asarray(im) > 0, iterations=1)
k = 4; bary = np.array([(i, j, k - i - j) for i in range(k + 1) for j in range(k + 1 - i)], float) / k
frac = np.zeros(len(F))
for f in range(len(F)):
    uv = W[f] - [2 * mat[f], 0]
    if np.abs(uv - uv[0]).max() < 1e-9: continue
    p = bary @ uv; x = np.clip((p[:, 0] * R).astype(int), 0, R - 1); y = np.clip(((1 - p[:, 1]) * R).astype(int), 0, R - 1)
    frac[f] = 1 - cov[mat[f]][y, x].mean()
np.save(f'work/uvout_{tag}.npy', frac)
area = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
bad = frac > 0
print(tag, 'faces leaving the UV coverage', int(bad.sum()), 'area cm2', round(float(area[bad].sum() * 1e4), 1))
for i in np.argsort(-frac * area)[:10]:
    if frac[i] > 0: print(f'  face {i} mat {mat[i]} outside {frac[i]:.2f} area {area[i]*1e4:.1f}cm2 at {np.round(V[F[i]].mean(0), 3)}')
