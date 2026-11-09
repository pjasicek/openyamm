#!/usr/bin/env python3
"""Fre pass 2: small dark or red specks in the face skin (cheek beside the nose, under the lower lip, the chin point; r22-r24 zoomed
front/jaw views). Head-shell skin texels (3D zones as heal_lines_fre.py: eyes, brows, upper lip/lip line and nostrils left out; the lower
lip's own red is kept by excluding lip-coloured blobs larger than MAXN) whose colour differs from their 15-px median by more than DIFF and
that form blobs of at most MAXN texels are replaced by the median of the clean texels round them. Args: <in png> <out png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; DIFF, MAXN = 0.085, 40
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
on = ~np.isnan(POS[..., 0]); x, z, y = np.nan_to_num(POS[..., 0], nan=9), np.nan_to_num(POS[..., 2], nan=-9), np.nan_to_num(POS[..., 1], nan=9); ax = np.abs(x)
feat = ((z > 0.663) & (z < 0.74) & (ax < 0.065) & (y < -0.06)) | ((z > 0.603) & (z < 0.632) & (ax < 0.030) & (y < -0.085)) | \
       ((z > 0.632) & (z < 0.66) & (ax < 0.014) & (y < -0.10)) | (z > 0.74)
med = np.stack([ni.median_filter(im[..., c], size=15) for c in range(3)], -1)
skin = on & ~feat & (med[..., 0] > 0.45) & (med[..., 0] > med[..., 1]) & (med[..., 1] > med[..., 2])
odd = skin & (np.linalg.norm(im - med, axis=-1) > DIFF)
lab, n = ni.label(odd); sz = ni.sum(odd, lab, range(1, n + 1)); keep = np.isin(lab, 1 + np.where(sz <= MAXN)[0])
keep = ni.binary_dilation(keep, iterations=1) & skin
out = im.copy(); out[keep] = med[keep]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST); print('SPECKS', int(n), 'healed texels', int(keep.sum()))
