#!/usr/bin/env python3
"""Keep set for the Fire Elemental's dark texture spots: source faces whose base colour is near-black over at least half
of their interior (six barycentric samples; mouth corners, the throat notch, ear folds, eye sockets, soles, palms), plus
every face sharing a vertex with one, plus the eye faces. A collapse that moves one of their corners spreads the dark
paint over a larger triangle (the throat notch grew to twice its size at 55 %). Needs work/basecolor.png.
Only spots above ZMIN (default 1.6 m: head and neck) are kept; keeping the soles, palms and shoulder spots as well
(1,532 faces) pushed the cut onto the rest and failed at 55 %.
Usage: dark_keep.py <out.npy> [luminance threshold, default 40] [ZMIN, default 1.6]"""
import sys
import numpy as np
from PIL import Image
T = float(sys.argv[2]) if len(sys.argv) > 2 else 40
ZMIN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.6
a = np.asarray(Image.open('work/basecolor.png').convert('RGB')).astype(int); h, w = a.shape[:2]
d = np.load('work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2); f = d['faces']
bc = np.array([[1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6], [.45, .45, .1], [.1, .45, .45]])
p = np.einsum('kj,fjc->fkc', bc, uv)
x = np.clip((p[..., 0] * w).astype(int), 0, w - 1); y = np.clip(((1 - p[..., 1]) * h).astype(int), 0, h - 1)
eye = uv[..., 0].max(1) < 16 / 1040
dark = ((a[y, x].sum(-1) < T).mean(1) >= .5) & ~eye & (d['verts'][f].mean(1)[:, 2] > ZMIN)
vs = np.zeros(f.max() + 1, bool); vs[f[dark].ravel()] = True
keep = vs[f].any(1) | eye
np.save(sys.argv[1], keep)
print('DARK', int(dark.sum()), 'faces; keep with one ring and eyes', int(keep.sum()))
