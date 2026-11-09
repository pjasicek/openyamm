#!/usr/bin/env python3
"""Colour slivers (dark_slivers.py by colour): candidate faces with at least REA_COL_N (default 3) of 48 samples over
REA_COL (default 60) RGB distance from the source at the same rest-pose point, in any direction. A collapsed face
spanning a UV-island edge samples a neighbouring chart (Smuggler: orange streaks on the left hand, a bandolier-brown
wedge on the tunic below the left collar); the median drift check passes it. Writes work/drift_<tag>.npy as 100 for
those faces, 0 otherwise, for drift_lock.py. Usage: colour_slivers.py <tag>"""
import os, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
tag = sys.argv[1]
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 48)


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2); tri = v[f]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    return pos, nrm, img[y, x], tri


sp, sn, sl, _ = samples('work/mesh_in.npz'); cp, cn, cl, ctri = samples(f'work/mesh_{tag}.npz')
dist, idx = cKDTree(sp.reshape(-1, 3)).query(cp.reshape(-1, 3), 8)
ok = np.abs((np.repeat(sn, len(B), 0)[idx] * np.repeat(cn, len(B), 0)[:, None]).sum(-1)) > .5
best = idx[np.arange(len(idx)), np.where(ok, dist, np.inf).argmin(1)]
darker = (np.linalg.norm(sl.reshape(-1, 3)[best] - cl.reshape(-1, 3), axis=1).reshape(len(cn), len(B))
          > float(os.environ.get('REA_COL', '60')))
bad = darker.sum(1) >= int(os.environ.get('REA_COL_N', '3'))
area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
np.save(f'work/drift_{tag}.npy', np.where(bad & (area > 0), 100., 0.))
print(tag, 'colour-sliver faces', int(bad.sum()))
for i in np.where(bad)[0][:20]:
    print(f'  face {i} off samples {darker[i].sum()} area {area[i]*1e4:.2f}cm2 at {np.round(ctri[i].mean(0), 3)}')
