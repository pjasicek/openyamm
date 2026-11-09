#!/usr/bin/env python3
"""Clean the neck of a female head base colour: Meshy painted the reference's collar as a pale line and patches on the neck shell. On the shell
between two heights, texels far from a broad blur take the blur (Gaussian), feathered at the band's ends.
Usage: neck_clean.py <in png> <out png> <z0 z1>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
src, dst, z0, z1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
S = 2048
D = np.load('v2/work/uv_head.npz')
base = np.asarray(Image.open(src).convert('RGB'), np.float32)
sizes = {c: (D['comp'] == c).sum() for c in np.unique(D['comp'][D['head'].astype(bool)])}
shell = max(sizes, key=sizes.get)
sh = np.zeros((S, S), bool); Z = np.zeros((S, S), np.float32)
for uv, x, h, k, c in zip(D['uv'], D['xyz'], D['head'], D['hand'], D['comp']):
    if not h or k or c != shell:
        continue
    p = uv * S; p = np.stack([p[:, 0], S - p[:, 1]], 1)
    lo = np.floor(p.min(0)).astype(int); hi = np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if not xs.size: continue
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9: continue
    st = (np.stack([xs + .5, ys + .5], -1) - p[0]) @ np.linalg.inv(T).T
    ins = (st[..., 0] >= 0) & (st[..., 1] >= 0) & (st.sum(-1) <= 1)
    w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
    Z[ys[ins], xs[ins]] = w[ins] @ x[:, 2]; sh[ys[ins], xs[ins]] = True
band = sh & (Z > z0) & (Z < z1)
w = ndimage.gaussian_filter(band.astype(np.float32), 3)[..., None]
b = np.stack([ndimage.gaussian_filter(base[..., k] * band, 28) for k in range(3)], -1) / np.maximum(ndimage.gaussian_filter(band.astype(np.float32), 28)[..., None], 1e-3)
fine = base - np.stack([ndimage.gaussian_filter(base[..., k], 4) for k in range(3)], -1)
out = base * (1 - w) + np.clip(b + fine * .3, 0, 255) * w
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(dst)
print('NECKCLEAN band texels', int(band.sum()))
