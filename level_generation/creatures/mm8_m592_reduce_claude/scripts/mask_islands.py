#!/usr/bin/env python3
"""Mane region-mask islands on the source mesh: faces whose mask (region mask R, 24 samples) exceeds 0.15 on average,
grouped by shared edges; prints each island's face count, area and centre (small islands away from the mane are
spill flecks). Usage: mask_islands.py [mesh npz, default work/mesh_in.npz] -> work/mask_faces.npy"""
import sys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load(sys.argv[1] if len(sys.argv) > 1 else 'work/mesh_in.npz'); f = d['faces']; v = d['verts']
m = np.asarray(Image.open('work/img3.png'), np.float32)[..., 0] / 255; H, W = m.shape
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 24)
su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
fm = m[y, x].mean(1); sel = np.where(fm > .15)[0]
# edge adjacency among selected faces
e = np.sort(np.concatenate([f[sel][:, [0, 1]], f[sel][:, [1, 2]], f[sel][:, [2, 0]]]), 1)
fid = np.tile(np.arange(len(sel)), 3)
key = e[:, 0] * (len(v) + 1) + e[:, 1]; o = np.argsort(key); ks = key[o]; same = ks[1:] == ks[:-1]
a, b = fid[o][1:][same], fid[o][:-1][same]
_, lab = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(len(sel), len(sel))), directed=False)
area = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1) / 2
np.save('work/mask_faces.npy', fm)
for c in np.argsort(-np.bincount(lab)):
    idx = sel[lab == c]
    print(f'island {c}: {len(idx)} faces, {area[idx].sum() * 1e4:.1f} cm2, mask {fm[idx].mean():.2f}, centre {np.round(v[f[idx]].mean((0, 1)), 3)}')
