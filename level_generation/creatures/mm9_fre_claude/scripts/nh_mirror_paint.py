#!/usr/bin/env python3
"""Pass 7 paint fix on Meshy's 4K base colour (geometry untouched), before the one downsample: Meshy painted her right brow tail and upper lid
on a neighbouring UV chart in another tone (a square notch in the brow, light blocks on the lid: r74 close-ups, review/newhead/browcmp.png).
The new head is exactly mirror-symmetric (nh_prep.py), so those texels take the colour of the same 3D point on her clean left side: every
face-skin texel of the faulty box (asm x X0..X1 on side SIDE, z Z0..Z1, in front of y Y1) is rasterised with its 3D position, mirrored,
located on the left side's triangles (barycentric), and the 4K paint is sampled there bilinearly; the result is blended in by a weight that
fades over FEATHER m at the box faces. The normal map is not mirrored (the charts are rotated independently in UV, tangent x would not
carry over). Args: <meshy base png> <out png>   (project folder; work/nh/head_uv.npz)"""
import os, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage as ni
Image.MAX_IMAGE_PIXELS = None
E = os.environ.get
X0, X1 = float(E('MP_X0', '0.006')), float(E('MP_X1', '0.074')); Z0, Z1 = float(E('MP_Z0', '0.668')), float(E('MP_Z1', '0.720'))
Y1 = float(E('MP_Y1', '-0.05')); FE = float(E('MP_FEATHER', '0.006')); SIDE = float(E('MP_SIDE', '1'))
D = np.load('work/nh/head_uv.npz'); uv, tri, co, fp = D['uv'], D['tri'], D['co'], D['fpiece']
img = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32); S = img.shape[0]
F = tri[fp == 0]; cen = co[F].mean(1)
inbox = (cen[:, 0] * SIDE > X0 - 0.01) & (cen[:, 0] * SIDE < X1 + 0.01) & (cen[:, 2] > Z0 - 0.01) & (cen[:, 2] < Z1 + 0.01) & (cen[:, 1] < Y1 + 0.01)
good = cen[:, 0] * SIDE < 0; G = F[good]; kd = cKDTree(co[G].mean(1))
def locate(m):
    """UV of 3D points m on the good side's triangles (best barycentric among the 12 nearest triangle centres)."""
    _, cand = kd.query(m, k=12); out = np.full((len(m), 2), np.nan); best = np.full(len(m), np.inf)
    for k in range(12):
        t = G[cand[:, k]]; a, b, c = co[t[:, 0]], co[t[:, 1]], co[t[:, 2]]
        n = np.cross(b - a, c - a); nn = (n * n).sum(1) + 1e-30
        q = m - (((m - a) * n).sum(1) / nn)[:, None] * n
        v0, v1, v2 = b - a, c - a, q - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1); d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01 + 1e-30; l1 = (d11 * d20 - d01 * d21) / den; l2 = (d00 * d21 - d01 * d20) / den; l0 = 1 - l1 - l2
        err = np.maximum(0, -np.minimum(np.minimum(l0, l1), l2)) + np.abs(((m - a) * n).sum(1)) / np.sqrt(nn)
        bet = err < best; best[bet] = err[bet]
        uvq = l0[:, None] * uv[t[:, 0]] + l1[:, None] * uv[t[:, 1]] + l2[:, None] * uv[t[:, 2]]
        out[bet] = uvq[bet]
    return out, best
out = img.copy(); total = 0
for t in F[inbox]:
    p = np.c_[uv[t, 0] * S, (1 - uv[t, 1]) * S]
    x0, y0 = np.floor(p.min(0)).astype(int) - 2; x1, y1 = np.ceil(p.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, S - 1) + 1), np.arange(max(y0, 0), min(y1, S - 1) + 1))
    q = np.c_[xs.ravel() + .5, ys.ravel() + .5]
    T = np.array([[p[1, 0] - p[0, 0], p[2, 0] - p[0, 0]], [p[1, 1] - p[0, 1], p[2, 1] - p[0, 1]]])
    if abs(np.linalg.det(T)) < 1e-9: continue
    b = np.linalg.solve(T, (q - p[0]).T).T; l = np.c_[1 - b.sum(1), b]; ok = (l > -0.08).all(1)      # a little past the edges: the gutter too
    if not ok.any(): continue
    P = l[ok] @ co[t]; X = P[:, 0] * SIDE
    w = np.clip(np.minimum(X - X0, X1 - X) / FE, 0, 1) * np.clip(np.minimum(P[:, 2] - Z0, Z1 - P[:, 2]) / FE, 0, 1) * np.clip((Y1 - P[:, 1]) / FE, 0, 1)
    w = w * w * (3 - 2 * w)
    if not (w > 0).any(): continue
    m = P.copy(); m[:, 0] *= -1; u2, err = locate(m); w = w * (err < 0.0015)
    sx, sy = u2[:, 0] * S - .5, (1 - u2[:, 1]) * S - .5
    col = np.stack([ni.map_coordinates(img[..., c], [np.nan_to_num(sy), np.nan_to_num(sx)], order=1, mode='nearest') for c in range(3)], 1)
    yy, xx = ys.ravel()[ok], xs.ravel()[ok]
    out[yy, xx] = out[yy, xx] * (1 - w[:, None]) + col * w[:, None]; total += int((w > 0.01).sum())
# brow tails: both tails cross a chart seam where Meshy's brow stops in a square step (eyesw_crop.png); past BT0 the brow fades smoothly into
# the skin 7 mm above the same point (sampled on the surface), fully skin at BT1, both sides, brow band only (z BZ0..BZ1)
BT0, BT1, BZ0, BZ1 = float(E('BT0', '0.034')), float(E('BT1', '0.045')), float(E('BZ0', '0.683')), float(E('BZ1', '0.712'))
img2 = out.copy(); G_all = F; kd2 = cKDTree(co[F].mean(1)); nb = 0
def locate_all(m):
    _, cand = kd2.query(m, k=12); res = np.full((len(m), 2), np.nan); best = np.full(len(m), np.inf)
    for k in range(12):
        t = F[cand[:, k]]; a, b, c = co[t[:, 0]], co[t[:, 1]], co[t[:, 2]]
        n = np.cross(b - a, c - a); nn = (n * n).sum(1) + 1e-30; q = m - (((m - a) * n).sum(1) / nn)[:, None] * n
        v0, v1, v2 = b - a, c - a, q - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1); d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01 + 1e-30; l1 = (d11 * d20 - d01 * d21) / den; l2 = (d00 * d21 - d01 * d20) / den; l0 = 1 - l1 - l2
        err = np.maximum(0, -np.minimum(np.minimum(l0, l1), l2)) + np.abs(((m - a) * n).sum(1)) / np.sqrt(nn)
        bet = err < best; best[bet] = err[bet]; res[bet] = (l0[:, None] * uv[t[:, 0]] + l1[:, None] * uv[t[:, 1]] + l2[:, None] * uv[t[:, 2]])[bet]
    return res
band = (np.abs(cen[:, 0]) > BT0 - 0.012) & (cen[:, 2] > BZ0 - 0.008) & (cen[:, 2] < BZ1 + 0.008) & (cen[:, 1] < -0.06) & (np.abs(cen[:, 0]) < 0.07)
for t in F[band]:
    p = np.c_[uv[t, 0] * S, (1 - uv[t, 1]) * S]
    x0, y0 = np.floor(p.min(0)).astype(int) - 2; x1, y1 = np.ceil(p.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, S - 1) + 1), np.arange(max(y0, 0), min(y1, S - 1) + 1))
    q = np.c_[xs.ravel() + .5, ys.ravel() + .5]
    T = np.array([[p[1, 0] - p[0, 0], p[2, 0] - p[0, 0]], [p[1, 1] - p[0, 1], p[2, 1] - p[0, 1]]])
    if abs(np.linalg.det(T)) < 1e-9: continue
    b = np.linalg.solve(T, (q - p[0]).T).T; l = np.c_[1 - b.sum(1), b]; ok = (l > -0.08).all(1)
    if not ok.any(): continue
    P = l[ok] @ co[t]
    w = np.clip((np.abs(P[:, 0]) - BT0) / (BT1 - BT0), 0, 1) * np.clip(np.minimum(P[:, 2] - BZ0, BZ1 - P[:, 2]) / 0.004, 0, 1)
    w = w * w * (3 - 2 * w)
    if not (w > 0).any(): continue
    m = P + np.array([0, 0, 0.007]); u2 = locate_all(m)
    col = np.stack([ni.map_coordinates(img2[..., c], [(1 - u2[:, 1]) * S - .5, u2[:, 0] * S - .5], order=1, mode='nearest') for c in range(3)], 1)
    yy, xx = ys.ravel()[ok], xs.ravel()[ok]; out[yy, xx] = out[yy, xx] * (1 - w[:, None]) + col * w[:, None]; nb += int((w > 0.01).sum())
print('BROW TAILS faded texels', nb)
Image.fromarray(np.clip(out + .5, 0, 255).astype('u1')).save(sys.argv[2])
print('MIRROR PAINT 4K texels', total, 'triangles', int(inbox.sum()))
