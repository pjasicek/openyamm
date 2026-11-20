#!/usr/bin/env python3
"""The eyeballs are painted from their own 3D position, not projected (Honk's lesson). Args: <final png>. In place."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
F = sys.argv[1]
Z = np.load('work/head_pos.npz'); pos, cov, prt = Z['pos'], Z['cov'], Z['prt']
im = np.asarray(Image.open(F).convert('RGB'), np.float32) / 255
S = im.shape[0]
if prt.shape[0] != S:
    k = prt.shape[0] / S
    idx = (np.arange(S) * k).astype(int); pos = pos[idx][:, idx]; cov = cov[idx][:, idx]; prt = prt[idx][:, idx]
m = prt == 13; P = pos[m]; out = np.zeros_like(P)
for sg in (1, -1):
    e = P[:, 0] * sg > 0
    c = 0.5 * (P[e].min(0) + P[e].max(0))
    fwd = np.array([sg * 0.05, -1.0, 0.0]); fwd /= np.linalg.norm(fwd)
    d = P[e] - c; d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
    a = np.degrees(np.arccos(np.clip(d @ fwd, -1, 1)))
    ir0 = np.array([0.80, 0.46, 0.08]); ir1 = np.array([0.42, 0.16, 0.03]); sclera = np.array([0.30, 0.22, 0.14]); pupil = np.array([0.012, 0.01, 0.008])
    t = np.clip(a / 34, 0, 1)[:, None]
    col = ir0 * (1 - t) + ir1 * t
    col = np.where((a > 34)[:, None], sclera, col)
    pu = np.clip((16 - a) / 2, 0, 1)[:, None]
    out[e] = col * (1 - pu) + pupil * pu
res = im.copy(); res[m] = out
idx = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
near = ndimage.binary_dilation(m, iterations=3) & ~cov
res[near] = res[idx[0][near], idx[1][near]]
Image.fromarray((np.clip(res, 0, 1) * 255 + .5).astype('u1')).save(F); print('EYES', int(m.sum()))
