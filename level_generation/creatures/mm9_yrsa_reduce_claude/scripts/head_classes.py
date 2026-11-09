#!/usr/bin/env python3
"""Yrsa head-set faces classified by their painted colour (head basecolor, 7 samples per UV triangle): skin, hair (white),
hood (dark knit), other. Writes work/head_classes.npz and review/head_classes.png (front/side/back/top scatter)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import colorsys
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_yrsa.glb', 'Yrsa')
im = np.asarray(Image.open(HERE / 'work' / 'head_basecolor.png').convert('RGB')).astype(float) / 255
H, Wd = im.shape[:2]
d = D['YrsaHead']; P, T, UV = d['P'], d['T'], d['UV']
bary = np.array([[1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6], [.45, .45, .1], [.1, .45, .45], [.45, .1, .45]])
uvs = np.einsum('sk,fkd->fsd', bary, UV[T])
px = np.clip((uvs[..., 0] * Wd).astype(int), 0, Wd - 1); py = np.clip((uvs[..., 1] * H).astype(int), 0, H - 1)
col = im[py, px]  # f, s, 3
med = np.median(col, 1)
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in med])
h, s, v = hsv.T
cls = np.full(len(T), 3)
hair = (s < 0.16) & (v > 0.5)
hood = (v < 0.36)
skin = ~hair & ~hood & ((h < 0.11) | (h > 0.93)) & (s >= 0.16)
cls[skin] = 0; cls[hair] = 1; cls[hood] = 2
raw = np.load(HERE / 'work' / 'glb_raw_labels.npz')
f0 = raw['foff'][1]; hand = raw['hand'][f0:].astype(bool); comp = raw['comp'][f0:]
cls[hand] = 9
print({k: int((cls == k).sum()) for k in (0, 1, 2, 3, 9)})
np.savez(HERE / 'work' / 'head_classes.npz', cls=cls, med=med, comp=comp)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
C = P[T].mean(1); colors = {0: (0.9, 0.5, 0.4), 1: (0.6, 0.6, 1.0), 2: (0.3, 0.2, 0.1), 3: (0, 0.8, 0), 9: (0.8, 0.8, 0.8)}
fig, ax = plt.subplots(1, 4, figsize=(28, 9))
sel = ~hand
for a, (xi, yi, nm, flip) in zip(ax, [(0, 1, 'front (+z)', 1), (2, 1, 'side', 1), (0, 1, 'back', -1), (0, 2, 'top', 1)]):
    order = np.argsort(C[sel, 2] * flip) if nm in ('front (+z)', 'back') else np.argsort(C[sel, 0]) if nm == 'side' else np.argsort(C[sel, 1])
    cc = C[sel][order]; kk = cls[sel][order]
    a.scatter(cc[:, xi] * (flip if nm == 'back' else 1), cc[:, yi], c=[colors[k] for k in kk], s=14)
    a.set_title(nm); a.set_aspect('equal')
plt.tight_layout(); plt.savefig(HERE / 'review' / 'head_classes.png', dpi=60)
