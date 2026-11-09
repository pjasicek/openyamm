#!/usr/bin/env python3
"""Pass 7 paint fix (texels of the eyeballs only; geometry untouched): the r73 viewer close-ups read as a stare (white sclera above the iris,
Meshy painted no lid shadow). As PeasantF2's head_fix (a soft lid shade over the top of each eyeball): eyeball texels are rasterised with
their 3D height; above the eye centre they blend toward a warm lid shadow, smoothly over LID_Z0..LID_Z1 (asm z), up to LID_K; the sclera
(bright, unsaturated texels) is toned to SCLERA_K of its value. Args: <in png> <out png>   (project folder; work/nh/head_uv.npz)"""
import os, sys
import numpy as np
from PIL import Image
E = os.environ.get
Z0, Z1, K, SK = float(E('LID_Z0', '0.6855')), float(E('LID_Z1', '0.6915')), float(E('LID_K', '0.6')), float(E('SCLERA_K', '0.88'))
im = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32) / 255; S = im.shape[0]
D = np.load('work/nh/head_uv.npz'); uv, tri, co, fp = D['uv'], D['tri'], D['co'], D['fpiece']
zmap = np.full((S, S), np.nan, np.float32)
for t in tri[fp == 2]:
    p = np.c_[uv[t, 0] * S, (1 - uv[t, 1]) * S]; z = co[t, 2]
    x0, y0 = np.floor(p.min(0)).astype(int) - 1; x1, y1 = np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, S - 1) + 1), np.arange(max(y0, 0), min(y1, S - 1) + 1))
    q = np.c_[xs.ravel() + .5, ys.ravel() + .5]
    T = np.array([[p[1, 0] - p[0, 0], p[2, 0] - p[0, 0]], [p[1, 1] - p[0, 1], p[2, 1] - p[0, 1]]])
    if abs(np.linalg.det(T)) < 1e-9: continue
    b = np.linalg.solve(T, (q - p[0]).T).T; l = np.c_[1 - b.sum(1), b]
    ok = (l > -0.02).all(1); zmap[ys.ravel()[ok], xs.ravel()[ok]] = (l[ok] * z).sum(1)
from scipy import ndimage as ni
eye = ~np.isnan(zmap); zi = ni.distance_transform_edt(~eye, return_distances=False, return_indices=True); zz = zmap[zi[0], zi[1]]
eye = ni.binary_dilation(eye, iterations=2)      # chart edges and raster gaps: the shade fades smoothly, no triangle-shaped patches
t = np.clip((zz - Z0) / (Z1 - Z0), 0, 1); w = ni.gaussian_filter(t * t * (3 - 2 * t) * K * eye, 1.0)[..., None]
mx = im.max(2); mn = im.min(2); sclera = eye & (mx > 0.6) & ((mx - mn) < 0.18 * mx)
out = im.copy()      # sclera toning off (SCLERA_K unused): it drew triangle patches on the eyeballs
lid = np.array([0.42, 0.27, 0.22], np.float32)
out = out * (1 - w) + lid * w
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(sys.argv[2])
print('EYES lid shade texels', int((w[..., 0] > 0.05).sum()), 'sclera toned', int(sclera.sum()), 'eyeball texels', int(eye.sum()))
