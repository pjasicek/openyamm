#!/usr/bin/env python3
"""White tunic trim faces (V-neck band, hem and shoulder-flap stripes): body-atlas faces on the tunic whose sampled
base colour is bright and unsaturated, plus their one-ring neighbours. Thin painted lines bend under any collapse, so
they are kept exactly. Usage: trim_faces.py <base keep .npy> <out .npy>  (also prints a per-region count)"""
import sys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
mask = np.asarray(Image.open('work/regionmask.png').convert('RGB'), np.float32)
uv = d['wuv'].reshape(-1, 3, 2); B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
p = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((p[..., 0] % 1 * W).astype(int), 0, W - 1); y = np.clip(((1 - p[..., 1] % 1) * H).astype(int), 0, H - 1)
col = img[y, x]; mk = mask[y, x][..., 0]
white = (col.min(-1) > 170) & (col.max(-1) - col.min(-1) < 40)
tunic_near = (mk > 127).any(1)
info = np.load('work/faces_info.npz'); body = info['u'] < .5
trim = body & white.any(1) & (tunic_near | (white.mean(1) > .5)) & (c[:, 2] > .85)
# one ring of neighbours by shared vertices
n = len(v); rows = np.repeat(np.arange(len(f)), 3); A = coo_matrix((np.ones(len(rows)), (rows, f.ravel())), shape=(len(f), n)).tocsr()
ring = (A @ (A.T @ trim.astype(float))) > 0
keep = np.load(sys.argv[1]) | (ring & body & (c[:, 2] > .85))
np.save(sys.argv[2], keep); print('TRIM white', int(trim.sum()), 'with ring', int((ring & body & (c[:, 2] > .85)).sum()), 'keep total', int(keep.sum()))
