#!/usr/bin/env python3
"""Meshy left the crown of the hair pale (no view looks straight down): above z0 the head shell takes the hair's colour statistics from the band below.
Usage: crown_fix.py <in png> <out png> <z0>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
src, dst, z0 = sys.argv[1], sys.argv[2], float(sys.argv[3])
S = 2048
D = np.load('v2/work/uv_head.npz')
im = np.asarray(Image.open(src).convert('RGB'), np.float32)
Z = np.zeros((S, S), np.float32)
H = D['head'].astype(bool) & ~D['hand'].astype(bool)
for uv, x in zip(D['uv'][H], D['xyz'][H]):
    p = uv * S; p = np.stack([p[:, 0], S - p[:, 1]], 1)
    lo = np.floor(p.min(0)).astype(int); hi = np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if not xs.size: continue
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9: continue
    st = (np.stack([xs + .5, ys + .5], -1) - p[0]) @ np.linalg.inv(T).T
    ins = (st[..., 0] >= 0) & (st[..., 1] >= 0) & (st.sum(-1) <= 1)
    w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
    Z[ys[ins], xs[ins]] = w[ins] @ x[:, 2]
ref = (Z > z0 - .05) & (Z < z0 - .01)
top = Z > z0
mr, sr = im[ref].mean(0), im[ref].std(0)
big = np.stack([ndimage.gaussian_filter(im[..., k], 22) for k in range(3)], -1)
fine = im - big
w = np.clip((Z - z0) / 0.02, 0, 1)[..., None]
out = im * (1 - w) + np.clip(mr + fine * 1.2, 0, 255) * w
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(dst)
print('CROWN texels', int(top.sum()), 'ref', mr.round(0))
