"""Torso/legs faces whose Ebora paint is a printed motif (silver/ivory/gold: skull cups, corset plates, belt, emblem,
studded leg panels, back ornament): fraction of 16 samples per face with min(R,G,B) > MINC (sRGB) above FRAC ->
work/pattern.npy. The texture-aware collapse warps these motifs first (skull cups at 85 %, the knee medallion at 80 %).
GROW dilates by edge-neighbour rings. Usage: pattern_faces.py"""
import os
import numpy as np
from PIL import Image
MINC, FRAC, GROW = int(os.environ.get('MINC', '90')), float(os.environ.get('FRAC', '0.25')), int(os.environ.get('GROW', '1'))
d = np.load('work/mesh_in.npz'); f, wuv, mat = d['faces'], d['wuv'].reshape(-1, 3, 2), d['mat']
imgs = {m: np.asarray(Image.open(f'work/base_{m}.png').convert('RGB')) for m in (0, 2)}
B = np.random.default_rng(3).dirichlet((1, 1, 1), 16)
pat = np.zeros(len(f), bool)
for m, img in imgs.items():
    sel = np.flatnonzero(mat == m); H, W = img.shape[:2]
    uv = np.einsum('sk,fkc->fsc', B, wuv[sel]); u = uv[..., 0] - 2 * m
    x = np.clip((u % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - uv[..., 1] % 1) * H, 0, H - 1).astype(int)
    c = img[y, x]; frac = (c.min(-1) > MINC).mean(1)
    pat[sel] = frac > FRAC
# grow by edge rings within torso/legs
from collections import defaultdict
ef = defaultdict(list)
for i, t in enumerate(f):
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        ef[(min(a, b), max(a, b))].append(i)
for _ in range(GROW):
    add = pat.copy()
    for fs in ef.values():
        if pat[fs].any():
            add[fs] = True
    pat = add & np.isin(mat, (0, 2))
np.save('work/pattern.npy', pat)
keep = np.load('work/keep_a.npy')
print('PATTERN faces', int(pat.sum()), 'torso', int((pat & (mat == 0)).sum()), 'legs', int((pat & (mat == 2)).sum()),
      '; outside keep_a', int((pat & ~keep).sum()), '; plain free', int((~pat & ~keep).sum()))
