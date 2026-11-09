#!/usr/bin/env python3
"""Fre body paint fix (2026-11-04, viewer r1): Meshy painted the feather shawl over PeasantF1's whole puffed upper sleeve (white feathers to
the elbow); MM9's Fre and the HD masters have the feather shawl on the shoulders only and plain red patterned sleeves below. Upper-sleeve
texels of the bodice ('dress') beyond T0 of the shoulder->elbow axis (eased in to T1) take the red dress cloth: a patch of the skirt's own
red paint (the largest all-red square of the skirt, tiled with mirroring) mapped round the arm (arc length x along-arm length at the skirt's texel
density, the wrap seam on the arm's underside), so the swirl pattern and fine detail are Meshy's. Gutters re-padded afterwards by the
caller. Args: <in png> <out png> [T0 T1]   (project folder; positions from work/uv_tex2.npz, joints from work/rig.json)"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]
T0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.16
T1 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.30
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
J = {k: np.array(v) for k, v in json.load(open('work/rig.json'))['mm9'].items()}
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
        P = (b[:, ok].T[:, :, None] * co[tri[f]][None]).sum(1)
        POS[gy.ravel()[ok].astype(int), gx.ravel()[ok].astype(int)] = P
    return POS
kd, ks = names.index('dress'), names.index('skirt')
body = np.where(mat == 0)[0]
P_dress = raster(body[comp[tri[body, 0]] == kd])
# skirt texel density (px per m) from the skirt faces
sk = body[comp[tri[body, 0]] == ks]
a3 = 0.5 * np.linalg.norm(np.cross(co[tri[sk, 1]] - co[tri[sk, 0]], co[tri[sk, 2]] - co[tri[sk, 0]]), axis=1)
u2 = uv[tri[sk]] * S; a2 = 0.5 * np.abs((u2[:, 1, 0] - u2[:, 0, 0]) * (u2[:, 2, 1] - u2[:, 0, 1]) - (u2[:, 2, 0] - u2[:, 0, 0]) * (u2[:, 1, 1] - u2[:, 0, 1]))
dens = float(np.sqrt(a2.sum() / a3.sum()))
# the red source patch: the largest all-red rectangle among the skirt's back texels
P_sk = raster(sk)
red = (im[..., 0] > 0.40) & (im[..., 1] < 0.22) & (im[..., 2] < 0.20) & ~np.isnan(P_sk[..., 0]) 
red = ni.binary_erosion(red, iterations=3)
rep = {'density_px_per_m': round(dens, 1)}
out = im.copy(); total = 0
for s in ('R', 'L'):
    Sh, El = J[f'FHP {s} UpperArm'], J[f'FHP {s} Forearm']; ax = El - Sh; L = np.linalg.norm(ax); ax /= L
    m = ~np.isnan(P_dress[..., 0]); ys, xs = np.where(m); P = P_dress[ys, xs]
    t = (P - Sh) @ ax / L; rad = P - Sh - np.outer((P - Sh) @ ax, ax); r = np.linalg.norm(rad, axis=1)
    sel = (t > T0 - 0.02) & (t < 1.25) & (r < 0.10) & (np.sign(P[:, 0]) == np.sign(Sh[0]))
    ys, xs, P, t, rad = ys[sel], xs[sel], P[sel], t[sel], rad[sel]
    down = np.array([0, 0, -1.0]) - (np.array([0, 0, -1.0]) @ ax) * ax; down /= np.linalg.norm(down); side = np.cross(ax, down)
    th = np.arctan2(rad @ side, rad @ down)          # 0 = the arm's underside (the wrap seam)
    arc = (th + np.pi) * 0.055; along = t * L
    # the largest all-red square of the skirt (distance transform), tiled with mirroring round and along the arm
    dt = ni.distance_transform_edt(red); y0c, x0c = np.unravel_index(np.argmax(dt), dt.shape); h = max(int(dt.max() / 1.42) - 1, 8)
    y0, x0, ww, hh = y0c - h, x0c - h, 2 * h, 2 * h
    def mirror(i, n): i = np.mod(i, 2 * n); return np.where(i >= n, 2 * n - 1 - i, i)
    px = (x0 + mirror((arc * dens).astype(int), ww)).clip(0, S - 1); py = (y0 + mirror((along * dens).astype(int), hh)).clip(0, S - 1)
    w = np.clip((t - T0) / (T1 - T0), 0, 1); w = (w * w * (3 - 2 * w))[:, None]
    out[ys, xs] = im[ys, xs] * (1 - w) + im[py, px] * w
    total += int((w > 0.01).sum()); rep[s] = dict(patch=[int(x0), int(y0), int(ww), int(hh)], texels=int((w > 0.01).sum()))
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST); print('SLEEVERED', json.dumps(rep))
