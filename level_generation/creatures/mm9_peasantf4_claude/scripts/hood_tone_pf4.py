#!/usr/bin/env python3
"""PF4 hood paint (2026-11-02): Meshy painted the new hood from four head views, and the side view came out lighter than the front and back,
so the hood showed a pale band with a zigzag edge along its UV charts (raw paint, profile). The hood is plain wool: every hood4 texel takes
(a) the hood's median colour (TARGET, or tier factors) plus its low-pass luminance deviation measured in 3D (Gaussian SIGMA over the
hood surface, so UV seams play no part) clamped to +-CLAMP of the median, and (b) its own fine weave (UV high-pass, 2 px).
F1's old hood under it (the hidden skull, seen only up the cape) takes the median x 0.90 (the hood's shaded inside).
Args: <in png> <out png> [r,g,b multipliers for the tier]   (project folder; rest positions from work/uv.npz)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
from scipy.spatial import cKDTree
SRC, DST = sys.argv[1:3]; MUL = np.array([float(v) for v in sys.argv[3].split(',')]) if len(sys.argv) > 3 else np.ones(3)
SIGMA, CLAMP = 0.025, 0.10
D = np.load('work/uv.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
PART = np.full((S, S), -1, int); POS = np.zeros((S, S, 3))
for fi in np.where(mat == 1)[0]:
    q = uv[tri[fi]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]; ok = (l3 > -0.01).all(1)
    yy, xx = pts[ok, 1].astype(int), pts[ok, 0].astype(int); PART[yy, xx] = comp[tri[fi][0]]; POS[yy, xx] = l3[ok] @ co[tri[fi]]
hood = PART == names.index('hood4'); old = PART == names.index('scarf')
LUMA = np.array([0.2126, 0.7152, 0.0722]); lum = im @ LUMA
med = np.median(im[hood], 0); mlum = float(med @ LUMA)
# low-pass luminance in 3D over the hood
hy, hx = np.where(hood); P = POS[hy, hx]; L = lum[hy, hx]
sub = np.arange(len(P))[::4]; kd = cKDTree(P[sub])
d, ii = kd.query(P, k=64, distance_upper_bound=3 * SIGMA); ok = np.isfinite(d); ii = np.where(ok, ii, 0)
g = np.exp(-0.5 * (np.where(ok, d, 1e9) / SIGMA) ** 2) * ok
lo = (L[sub][ii] * g).sum(1) / np.maximum(g.sum(1), 1e-9)
dev = np.clip(lo / mlum - 1, -CLAMP, CLAMP)
fine = np.clip((lum - ni.gaussian_filter(lum, 2.0))[hy, hx], -0.08, 0.035)      # Meshy's dotted pale 'stitch' rows across the hood sides clipped
out = im.copy()
base = med * MUL
out[hy, hx] = np.clip(base[None] * (1 + dev)[:, None] + fine[:, None] * 0.9, 0, 1)
oy, ox = np.where(old); fo = (lum - ni.gaussian_filter(lum, 2.0))[oy, ox]
out[oy, ox] = np.clip(base[None] * 0.90 + fo[:, None] * 0.5, 0, 1)      # shaded hood colour: where it shows through, it reads as the hood
# black specks Meshy left on hidden head texels (seen where a face of the head comes close to the hood): neighbour colour
blk = (PART == names.index('head')) & (out.sum(-1) < 0.25)
okc = (PART >= 0) & ~ni.binary_dilation(blk, iterations=1)
wsum = ni.gaussian_filter(okc.astype(np.float32), 3.0)
for c_ in range(3):
    fillc = ni.gaussian_filter(out[..., c_] * okc, 3.0) / np.maximum(wsum, 1e-4)
    out[..., c_] = np.where(blk, fillc, out[..., c_])
print('black head texels filled', int(blk.sum()))
# isolated specks on the hood (Meshy's dotted rows survived as single texels): texels far from their 5x5 median take it
med5 = np.stack([ni.median_filter(out[..., c_], 5) for c_ in range(3)], -1)
spk = hood & (np.abs((out - med5) @ LUMA) > 0.045)
out[spk] = med5[spk]; print('hood specks', int(spk.sum()))
cov = PART >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
print('HOODTONE median', np.round(med * 255).tolist(), 'x', MUL.tolist(), 'hood texels', int(hood.sum()), 'old hood', int(old.sum()),
      'dev range', round(float(dev.min()), 3), round(float(dev.max()), 3))
