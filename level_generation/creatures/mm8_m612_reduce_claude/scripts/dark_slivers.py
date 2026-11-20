#!/usr/bin/env python3
"""Dark-sliver test (Cyclops lesson): per decimated face, 24 barycentric samples of the base colour against the source
colour at the same rest-pose points; a face is flagged when the 25th-percentile luminance of its samples is over 35 % darker
than the 25th percentile of the matched source samples (banded feathers: compare like with like). The per-face median drift misses these. Source samples must face the same way (dot > 0.7), so stacked feather sheets do not vote.
Usage: dark_slivers.py <tag, e.g. r60>"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
tag = sys.argv[1]
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255
H, W = img.shape[:2]; lin = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
lum = lin(img) @ np.array([.2126, .7152, .0722], np.float32)
B = np.random.default_rng(2).dirichlet((1, 1, 1), 24)


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
    pos = np.einsum('sk,fkc->fsc', B, v[f]); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    t = v[f]; n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    return pos, lum[y, x], t, n


# stacked feather sheets lie millimetres apart: only source samples on a surface facing the same way count
sp, sl, _, sn = samples('work/mesh_in.npz'); cp, cl, ctri, cn = samples(f'work/mesh_{tag}.npz')
dist, idx = cKDTree(sp.reshape(-1, 3)).query(cp.reshape(-1, 3), 16)
ok = (np.repeat(sn, len(B), 0)[idx] * np.repeat(cn, len(B), 0)[:, None]).sum(-1) > .7
vals = np.where(ok, sl.reshape(-1)[idx], np.nan).reshape(len(cl), -1)  # pooled same-facing source samples per face
import warnings; warnings.simplefilter('ignore')
ref = np.nanpercentile(vals, 25, axis=1); ref = np.where(np.isnan(ref), np.percentile(cl, 25, axis=1), ref)
ratio = np.percentile(cl, 25, axis=1) / np.maximum(ref, 1e-4)  # darkest quarter against the source's darkest quarter
area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
bad = np.where((ratio < .65) & (area > 2e-6))[0]
print(tag, 'dark faces', len(bad), 'area cm2', round(float(area[bad].sum() * 1e4), 2))
for i in bad[np.argsort(-area[bad])][:10]:
    print(f'  face {i} ratio {ratio[i]:.2f} area {area[i]*1e4:.2f}cm2 at {np.round(ctri[i].mean(0), 3)}')
np.save(f'work/dark_{tag}.npy', ratio)
