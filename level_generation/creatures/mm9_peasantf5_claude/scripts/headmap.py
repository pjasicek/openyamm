#!/usr/bin/env python3
"""Per-texel 3D position, normal and face of the head set (1K): work/headmap.npz (pos, nrm, face, cov). Bind pose of the frozen mesh. Project folder."""
import numpy as np
from PIL import Image, ImageDraw
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
S = 1024
fi = np.where(mat == 1)[0]
im = Image.new('I', (S, S), -1); dr = ImageDraw.Draw(im)
for k, f in enumerate(fi):
    dr.polygon([(float(uv[i, 0] * S), float((1 - uv[i, 1]) * S)) for i in tri[f]], fill=int(k))
F = np.asarray(im).astype(np.int64); cov = F >= 0
yy, xx = np.nonzero(cov); kk = F[yy, xx]; f = fi[kk]
P = np.stack([(xx + 0.5) / S, 1 - (yy + 0.5) / S], 1)
A, B, C = uv[tri[f, 0]], uv[tri[f, 1]], uv[tri[f, 2]]
v0, v1, v2 = B - A, C - A, P - A
d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
den = d00 * d11 - d01 * d01; den[np.abs(den) < 1e-14] = 1e-14
b1 = (d11 * d20 - d01 * d21) / den; b2 = (d00 * d21 - d01 * d20) / den; b0 = 1 - b1 - b2
X = co[tri[f, 0]] * b0[:, None] + co[tri[f, 1]] * b1[:, None] + co[tri[f, 2]] * b2[:, None]
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
pos = np.zeros((S, S, 3), np.float32); nrm = np.zeros((S, S, 3), np.float32); face = np.full((S, S), -1, np.int64)
pos[yy, xx] = X; nrm[yy, xx] = fn[f]; face[yy, xx] = f
np.savez_compressed('work/headmap.npz', pos=pos, nrm=nrm, face=face, cov=cov)
print('HEADMAP', int(cov.sum()), 'texels')
