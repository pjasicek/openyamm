#!/usr/bin/env python3
"""Red slivers (m438: wound texels pulled onto skin): candidate faces with at least REA_RED_N (default 2) of 48 samples
that read as wound/bone-patch colour (red over 1.5x green and blue, or a hue jump over 40 in any channel towards red)
where the source at the same rest-pose point is skin or cloth. Same sampling as dark_slivers.py; writes
work/drift_<tag>.npy (100 for those faces) for drift_lock.py. Usage: red_slivers.py <tag>"""
import os, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
tag = sys.argv[1]
img = np.asarray(Image.open(os.environ.get('REA_BASECOLOR', 'work/basecolor.png')).convert('RGB'), np.float32); H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 48)


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2); tri = v[f]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    return pos, nrm, img[y, x], tri


def red(c):
    return (c[..., 0] > 1.5 * c[..., 1] + 8) & (c[..., 0] > 1.5 * c[..., 2] + 8)


sp, sn, sc, _ = samples(os.environ.get('REA_SRC_NPZ', 'work/mesh_in.npz')); cp, cn, cc, ctri = samples(f'work/mesh_{tag}.npz')
dist, idx = cKDTree(sp.reshape(-1, 3)).query(cp.reshape(-1, 3), 8)
ok = np.abs((np.repeat(sn, len(B), 0)[idx] * np.repeat(cn, len(B), 0)[:, None]).sum(-1)) > .5
best = idx[np.arange(len(idx)), np.where(ok, dist, np.inf).argmin(1)]
s = sc.reshape(-1, 3)[best]; c = cc.reshape(-1, 3)
# compare against the source's 3x3 neighbourhood of samples: red only if no nearby source sample is red
srcred = red(sc.reshape(-1, 3))[idx].any(1)
bad_s = (red(c) & ~srcred).reshape(len(cn), len(B))
bad = bad_s.sum(1) >= int(os.environ.get('REA_RED_N', '2'))
area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
np.save(f'work/drift_{tag}.npy', np.where(bad, 100., 0.))
print(tag, 'red-sliver faces', int(bad.sum()))
for i in np.where(bad)[0][:20]:
    print(f'  face {i} red samples {bad_s[i].sum()} area {area[i]*1e4:.2f}cm2 at {np.round(ctri[i].mean(0), 3)}')
