#!/usr/bin/env python3
"""Fre head normal map fix (2026-11-04, viewer r19: the thin dark line across her left cheek and down the neck is stronger lit than in the
base colour alone: Meshy's normal map carries the same projection seam). In the face and neck skin zone of the head shell (as
skin_line_fre.py: eyes, brows, lips, nostrils and hairline left out), normal texels deviating more than DEG from their 9-px median take the
median. Args: <in png> <out png> [DEG]   (project folder; positions from work/uv_tex2.npz)"""
import sys, runpy
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; DEG = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
POS = np.full((S, S, 3), np.nan)
for f in np.where((mat == 1) & (comp[tri[:, 0]] == names.index('head')))[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); b = np.vstack([l, 1 - l.sum(0)]); ok = (b >= -1e-4).all(0)
    if ok.any(): POS[gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)] = (b[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1)
x, z, y = POS[..., 0], np.nan_to_num(POS[..., 2], nan=-9), np.nan_to_num(POS[..., 1], nan=9); on = ~np.isnan(x); ax = np.abs(np.nan_to_num(x, nan=9))
feat = ((z > 0.655) & (z < 0.74) & (ax < 0.065) & (y < -0.06)) | ((z > 0.585) & (z < 0.632) & (ax < 0.032) & (y < -0.08)) | \
       ((z > 0.625) & (z < 0.66) & (ax < 0.022) & (y < -0.09)) | (z > 0.74)
zone = on & ~feat
n = im * 2 - 1; med = np.stack([ni.median_filter(n[..., c], size=9) for c in range(3)], -1)
med /= np.maximum(np.linalg.norm(med, axis=-1, keepdims=True), 1e-6); nn = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
dev = np.degrees(np.arccos(np.clip((nn * med).sum(-1), -1, 1)))
fix = zone & (dev > DEG); fix = ni.binary_dilation(fix, iterations=1) & zone
out = n.copy(); out[fix] = med[fix]
Image.fromarray((np.clip((out + 1) / 2, 0, 1) * 255 + .5).astype('u1')).save(DST); print('NORMALLINE texels', int(fix.sum()))
