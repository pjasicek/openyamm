#!/usr/bin/env python3
"""Fre pass 4: the head set's AO (ORM red, from the bake on the upload with the old bob on) is 0.1-0.5 on the jaw sides, below the ears
and the nape, where the bob covered the skin; with PeasantF2's drawn-back hair that skin shows and the AO read as brown smudges from
below. Every face-shell texel the new hair does not cover, lower than the cheekbone (z < 0.66) and behind the cheek (y > -0.075), and
every old-hood texel (the teeth left between hair rim and face outline; their AO was the dark hidden skull) and (at 85 %) the face shell
below 0.60 m (under the chin, the throat) takes AO max(AO, FLOOR),
eased in over 1 cm of height and depth. Args: <orm png in> <orm png out>   (project folder; after finish_pf.py)"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
SRC, DST = sys.argv[1:3]; FLOOR = 0.9
U = np.load('work/uv.npz'); A = np.load('work/asm_frozen.npz'); names = [str(x) for x in U['names']]
co = A['co'][U['orig']]; tri, uv, mat, comp = U['tri'], U['uv'], U['mat'], U['comp']
KH, KS, K2 = names.index('head'), names.index('scarf'), names.index('hair2')
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
POS = np.full((S, S, 3), np.nan); PART = np.full((S, S), -1)
for f in np.where((mat == 1) & np.isin(comp[tri[:, 0]], [KH, KS]))[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, np.stack([gx.ravel() - q[2, 0], gy.ravel() - q[2, 1]])); bb = np.vstack([l, 1 - l.sum(0)]); ok = (bb >= -1e-4).all(0)
    if ok.any():
        yy, xx = gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)
        POS[yy, xx] = (bb[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1); PART[yy, xx] = comp[tri[f, 0]]
ys, xs = np.where(PART >= 0); P = POS[ys, xs]; pt = PART[ys, xs]
C = np.array([0.0, 0.0, 0.665]); tube = A['hair2_tube'][U['orig']]
capT = tri[(comp[tri] == K2).all(1) & ~tube[tri].any(1)]
d = P - C; r = np.linalg.norm(d, axis=1); u = d / r[:, None]
t = raycast(C + u * 0.6, -u, co, capT); cov = np.isfinite(t) & (0.6 - t > r - 0.001)
def ss(x, a, b):
    k = np.clip((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k)
w = np.where(pt == KS, 1.0, (1 - ss(P[:, 2], 0.65, 0.66 + 0.0)) * ss(P[:, 1], -0.085, -0.075)) * ~cov
w[pt == KS] = 1.0
# and under the chin / the throat (r53 'jaw' view: the chin's baked occlusion read as a brown smudge from below), floor 0.85 there
w = np.maximum(w, (1 - ss(P[:, 2], 0.595, 0.615)) * (pt == KH) * ~cov * 0.85)
ao = im[ys, xs, 0]; new = np.maximum(ao, FLOOR); im[ys, xs, 0] = ao * (1 - w) + new * w
# pass 5 (orchestrator r62: lit panels at the temples and forehead): the AO bake also carries the old bob's broad occlusion along its
# whole edge (the forehead under the circlet ~0.84). On every bare face-shell texel the AO is divided by its own broad mean (the 64
# nearest texels in 3D, ~1.5 cm): crevices (eyes, nostrils, lips) keep their relative darkness, broad shadow from the bob goes
fs = np.where((pt == KH) & ~cov & (P[:, 2] > 0.55))[0]
if len(fs):
    a = im[ys[fs], xs[fs], 0]; _, jj = cKDTree(P[fs]).query(P[fs], k=64); lp = a[jj].mean(1)
    im[ys[fs], xs[fs], 0] = np.clip(a / np.maximum(lp, 0.35), 0, 1)
Image.fromarray((np.clip(im, 0, 1) * 255 + 0.5).astype('u1')).save(DST)
print('AOLIFT texels', int((w > 0.01).sum()), 'mean AO there before', round(float(ao[w > 0.5].mean()), 3), 'after', round(float(im[ys, xs, 0][w > 0.5].mean()), 3))
