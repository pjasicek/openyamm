#!/usr/bin/env python3
"""Region-mask drift: reduced faces whose iris channel (G of the region mask, coloured by the tier's iris ramp) is
present while the source surface at the same rest-pose points has none; the base colour drift check misses these
(MM8 Nightmare: an iris-coloured fleck on the left stalk junction). Usage: mask_drift.py <tag> [radius m]
-> work/mask_drift_<tag>.npy (bool per reduced face)"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
tag = sys.argv[1]
m = np.asarray(Image.open('../mm8_m600_claude/textures/body_region_mask.png').convert('RGBA'), np.float32) / 255
H, W = m.shape[:2]; rng = np.random.default_rng(1); B = rng.dirichlet((1, 1, 1), 24)


def samp(p):
    d = np.load(p); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2); tri = v[f]
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    return pos, m[y, x, 1], tri


sp, sg, _ = samp('work/mesh_in.npz'); cp, cg, ctri = samp(f'work/mesh_{tag}.npz')
_, i = cKDTree(sp.reshape(-1, 3)).query(cp.reshape(-1, 3), 6)
src_iris = sg.reshape(-1)[i].max(1).reshape(cg.shape)  # any iris nearby in the source
spurious = ((cg > .25) & (src_iris < .1)).mean(1)
bad = spurious > 0
area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
np.save(f'work/mask_drift_{tag}.npy', bad)
print(tag, 'faces with spurious iris mask', int(bad.sum()), 'area cm2', round(float(area[bad].sum() * 1e4), 3))
for k in np.where(bad)[0][np.argsort(-spurious[bad])][:10]:
    print('  face', k, 'iris samples', round(float(spurious[k]), 2), 'area', round(float(area[k] * 1e4), 3), 'cm2 at', np.round(ctri[k].mean(0), 3))
