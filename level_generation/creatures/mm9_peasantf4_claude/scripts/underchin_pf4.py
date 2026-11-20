#!/usr/bin/env python3
"""Under the chin (2026-11-02, viewer shot from below): Meshy painted the jaw's underside as a dark brown shadow (a goatee in the low views;
the front repaint never reaches it). Head-shell texels whose surface faces down (normal z < -0.15 after the chin sculpt) between the chin
and the throat (1.45-1.545 m over the soles, |x| < 6.5 cm, behind the chin's front) take the throat's skin tone (median of the forward-
facing neck texels at 1.43-1.49 m) x 0.93 (a soft shade, the angle kept) plus their own fine detail, eased in over 6 mm.
Args: <in png> <out png> (project folder; positions and normals from work/uv_tex2.npz)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
kh = names.index('head'); Z0 = -0.9297
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
POS = np.full((S, S, 3), np.nan); NOR = np.zeros((S, S, 3))
for f in np.where((mat == 1) & (comp[tri[:, 0]] == kh))[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l, 1 - l.sum(1)]; ins = (L3 >= -0.01).all(1)
    yy, xx = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)
    POS[yy, xx] = L3[ins] @ co[tri[f]]; NOR[yy, xx] = fn[f]
cov = ~np.isnan(POS[..., 0]); x, y, z = (np.nan_to_num(POS[..., i]) for i in range(3)); zs = z - Z0
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
throat = cov & (zs > 1.43) & (zs < 1.49) & (np.abs(x) < 0.03) & (NOR[..., 1] < -0.6)
tone = np.median(im[throat], 0) * 0.93
w = cov * ramp(-NOR[..., 2], 0.10, 0.25) * ramp(zs, 1.445, 1.455) * (1 - ramp(zs, 1.535, 1.548)) * (1 - ramp(np.abs(x), 0.058, 0.066)) * (1 - ramp(-y, 0.100, 0.112))
lum = im @ np.array([0.2126, 0.7152, 0.0722]); det = lum - ni.gaussian_filter(lum, 1.5)
new = np.clip(tone[None, None] + det[..., None] * 0.6, 0, 1)
out = im * (1 - w[..., None]) + new * w[..., None]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
print('UNDERCHIN texels', int((w > 0.5).sum()), 'tone', np.round(tone * 255).tolist(), 'throat texels', int(throat.sum()))
