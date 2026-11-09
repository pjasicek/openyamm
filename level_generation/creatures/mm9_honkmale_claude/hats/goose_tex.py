#!/usr/bin/env python3
"""Resample the female head set's hat texels onto the hat's own atlas. Writes hats/work/goose_{basecolor,normal,orm}.png (1K)."""
import numpy as np
from PIL import Image
from scipy import ndimage
S = 1024
D = np.load('hats/work/goose.npz')
F = '../mm9_honkfemale_claude/v2/textures/honkf_head_'
maps = {'basecolor': F + 'basecolor.png', 'normal': F + 'normal_1k.png', 'orm': F + 'metal_rough_1k.png'}
OU = np.zeros((S, S, 2), np.float32); cov = np.zeros((S, S), bool)
for uv, old in zip(D['uv'], D['old']):
    p = uv * S; p = np.stack([p[:, 0], S - p[:, 1]], 1)
    lo = np.floor(p.min(0)).astype(int) - 1; hi = np.ceil(p.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if not xs.size: continue
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9: continue
    st = (np.stack([xs + .5, ys + .5], -1) - p[0]) @ np.linalg.inv(T).T
    ins = (st[..., 0] >= -.03) & (st[..., 1] >= -.03) & (st.sum(-1) <= 1.03)
    w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
    OU[ys[ins], xs[ins]] = w[ins] @ old
    cov[ys[ins], xs[ins]] = True
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
for k, f in maps.items():
    im = np.asarray(Image.open(f).convert('RGB'), np.float32); H, W = im.shape[:2]
    out = np.stack([ndimage.map_coordinates(im[..., c], [(1 - OU[..., 1]) * H - .5, OU[..., 0] * W - .5], order=1, mode='nearest') for c in range(3)], -1)
    out = out[idx[0], idx[1]]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f'hats/work/goose_{k}.png')
print('GOOSETEX', int(cov.sum()))
