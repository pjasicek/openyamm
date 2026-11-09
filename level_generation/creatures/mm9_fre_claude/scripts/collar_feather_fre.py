#!/usr/bin/env python3
"""Fre body paint fix (2026-11-04, viewer r4 back views): the bodice's collar at the back of the neck (hidden by the hair bun in the HD
masters) was painted a flat pale yellow. MM9's Fre has the feather shawl up to the neck there. Bodice texels on the back above Z0 that are
flat pale yellow (no feather structure: low local contrast) take feathers: a patch of the shawl's own paint (the largest all-feather
square: light, low-saturation texels of the bodice) mapped by the texel's back position (x across, z up) at the bodice's texel density,
tiled with mirroring; the region is grown 2 texels and feathered. Args: <in png> <out png> [Z0]   (project folder; work/uv_tex2.npz)"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ni
sys.path.insert(0, __file__.rsplit('/', 1)[0])
SRC, DST = sys.argv[1:3]; Z0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.47
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
def raster(faces):
    POS = np.full((S, S, 3), np.nan)
    for f in faces:
        q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
        if abs(np.linalg.det(T_)) < 1e-12: continue
        l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]]))
        b = np.vstack([l, 1 - l.sum(0)]); ok = (b >= -1e-4).all(0)
        if not ok.any(): continue
        POS[gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)] = (b[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1)
    return POS
fd = np.where((mat == 0) & (comp[tri[:, 0]] == names.index('dress')))[0]
P = raster(fd); on = ~np.isnan(P[..., 0])
a3 = 0.5 * np.linalg.norm(np.cross(co[tri[fd, 1]] - co[tri[fd, 0]], co[tri[fd, 2]] - co[tri[fd, 0]]), axis=1)
u2 = uv[tri[fd]] * S; a2 = 0.5 * np.abs((u2[:, 1, 0] - u2[:, 0, 0]) * (u2[:, 2, 1] - u2[:, 0, 1]) - (u2[:, 2, 0] - u2[:, 0, 0]) * (u2[:, 1, 1] - u2[:, 0, 1]))
dens = float(np.sqrt(a2.sum() / a3.sum()))
r, g, b = im[..., 0], im[..., 1], im[..., 2]; lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
mx, mn = im.max(-1), im.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
loc = np.sqrt(np.maximum(ni.uniform_filter(lum ** 2, 7) - ni.uniform_filter(lum, 7) ** 2, 0))
yellow = on & (np.nan_to_num(P[..., 2], nan=-9) > Z0) & (np.nan_to_num(P[..., 1], nan=-9) > -0.01) & (r > 0.70) & (g > 0.55) & (b < 0.62) & (sat > 0.25) & (loc < 0.05)
yellow = ni.binary_opening(yellow, iterations=1); yellow = ni.binary_dilation(yellow, iterations=2) & on
feather = on & (lum > 0.50) & (sat < 0.38)
feather = ni.binary_opening(ni.binary_closing(feather, iterations=3), iterations=1)
dt = ni.distance_transform_edt(feather); yc, xc = np.unravel_index(np.argmax(dt), dt.shape); h = max(int(dt.max() / 1.42) - 1, 8)
def mirror(i, n): i = np.mod(i, 2 * n); return np.where(i >= n, 2 * n - 1 - i, i)
ys, xs = np.where(yellow); Q = P[ys, xs]
px = (xc - h + mirror((Q[:, 0] * dens).astype(int) + 4096, 2 * h)).clip(0, S - 1); py = (yc - h + mirror((-Q[:, 2] * dens).astype(int) + 4096, 2 * h)).clip(0, S - 1)
w = ni.gaussian_filter(yellow.astype(np.float32), 1.0)[ys, xs][:, None]
out = im.copy(); out[ys, xs] = im[ys, xs] * (1 - w) + im[py, px] * w
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
print('COLLAR feathers', json.dumps(dict(texels=int(yellow.sum()), patch=[int(xc - h), int(yc - h), int(2 * h)], density=round(dens, 1))))
