#!/usr/bin/env python3
"""Repair of the projected male tier heads, texture space only, 0 credits (2026-10-30 night pass). head_tier_project.py blended Codex
repaints from several views: on the Elder and the Seer that left doubled irises, a third eye on the nose bridge, a seam down the nose
and doubled nostrils. Outside the central face the projection is good (wrinkles, hair, beard), so only the central face is replaced:
- zone: both eyes and brows, the nose, the mouth, from 3D texel positions in the head set;
- colour: tier A's clean texels times one gain per channel, from the median of the tier's own skin just outside the zone (not an
  image-space blur: the face is several atlas charts, and a blur across them broke it into patches);
- hair in the zone (brows, moustache): `--hair grey` lifts it to the Elder's grey;
- irises: recoloured to `--iris r,g,b` from tier A's green.
Keeps the projected file as v2/textures/<in stem>_proj.png. Run from the project folder.
Args: <tier png> <tier A png> [--hair grey|keep] [--iris r,g,b] [--cx -0.007] [--eye-z 0.755] [--mouth-z 0.69]"""
import argparse, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
ap = argparse.ArgumentParser()
ap.add_argument('tier'); ap.add_argument('a')
ap.add_argument('--hair', default='keep'); ap.add_argument('--iris', default='0.45,0.62,0.85')
ap.add_argument('--cx', type=float, default=-0.007); ap.add_argument('--eye-z', type=float, default=0.755)
ap.add_argument('--grade', default='', help='r,g,b gain on skin texels only, the whole head: towards the MM9 skin')
ap.add_argument('--mouth-z', type=float, default=0.69); ap.add_argument('--eye-dx', type=float, default=0.031)
ar = ap.parse_args()
p = Path(ar.tier)
src = p.with_name(p.stem + '_proj.png')
if not src.exists():
    shutil.copy2(p, src)
T = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
A = np.asarray(Image.open(ar.a).convert('RGB'), np.float32) / 255
S = T.shape[0]
D = np.load('v2/work/uv_head.npz')
xyz = np.full((S, S, 3), np.nan, np.float32)
for uv, x, h, k in zip(D['uv'], D['xyz'], D['head'], D['hand']):
    if not h or k:
        continue
    q = uv * S
    q = np.c_[q[:, 0], S - q[:, 1]]
    lo = np.floor(q.min(0)).astype(int); hi = np.ceil(q.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if not xs.size:
        continue
    M = np.array([q[1] - q[0], q[2] - q[0]]).T
    if abs(np.linalg.det(M)) < 1e-9:
        continue
    st = (np.stack([xs + .5, ys + .5], -1) - q[0]) @ np.linalg.inv(M).T
    ins = (st[..., 0] >= -.03) & (st[..., 1] >= -.03) & (st.sum(-1) <= 1.03)
    w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
    xyz[ys[ins], xs[ins]] = w[ins] @ x
X, Y, Z = xyz[..., 0] - ar.cx, xyz[..., 1], xyz[..., 2]
front = Y < -0.035
Ze, Zm = ar.eye_z, ar.mouth_z


def soft(d):
    """1 inside the unit ellipse, falling to 0 by 1.25"""
    return np.clip((1.25 - d) / 0.25, 0, 1)


eyes = soft(np.hypot(X / 0.078, (Z - Ze - 0.004) / 0.036))
nose = soft(np.maximum(np.abs(X) / 0.034, np.abs(Z - (Ze + Zm) / 2 - 0.016) / 0.062))
mouth = soft(np.hypot(X / 0.062, (Z - Zm) / 0.034))
m = np.nan_to_num(np.maximum(np.maximum(eyes, nose), mouth) * front, nan=0.0)
m = ndimage.gaussian_filter(m, 3)
covered = ~np.isnan(X)
# gain from the tier's skin just outside the zone (not its hair)
skin = np.nan_to_num((np.abs(X) < 0.10) & (Z > Zm - 0.075) & (Z < Ze + 0.07) & front, nan=0).astype(bool)
ring = (covered & skin & (m < 0.02)).astype(np.float32)
blur = lambda a, s: ndimage.gaussian_filter(a, s)
# one gain per channel: the texture's charts are not neighbours on the face, so any image-space blur breaks at chart edges
sk = ring > 0
sk &= (T[..., 0] > T[..., 2] * 1.1) & (A[..., 0] > A[..., 2] * 1.1) & (A @ np.array([.299, .587, .114]) > .35)
gain = np.median(T[sk], 0) / np.median(A[sk], 0)
out = np.clip(A * gain, 0, 1)
L = A @ np.array([.299, .587, .114])
# eye region: neither lashes nor irises are hair
er = np.nan_to_num(np.minimum(np.hypot((np.abs(X) - ar.eye_dx) / 0.024, (Z - Ze) / 0.012), 3.0), nan=3.0)
iris_zone = er < 1.0
if ar.hair == 'grey':
    # only where hair grows: the brows, and the moustache and chin beard around the lips (not nostrils, not the shadows under the eyes)
    brow = np.nan_to_num(soft(np.hypot(X / 0.082, (Z - Ze - 0.024) / 0.016)), nan=0.0)
    lips = np.nan_to_num(soft(np.hypot(X / 0.040, (Z - Zm + 0.008) / 0.006)), nan=0.0)
    musta = np.nan_to_num(soft(np.hypot(X / 0.062, (Z - Zm - 0.008) / 0.026)), nan=0.0) * (1 - lips)
    musta *= np.nan_to_num(np.abs(X) > 0.0, nan=0.0)
    beard = np.nan_to_num(soft(np.hypot(X / 0.05, (Z - Zm + 0.04) / 0.022)), nan=0.0) * (1 - lips)
    nostril = np.nan_to_num(soft(np.hypot(X / 0.03, (Z - Zm - 0.04) / 0.012)), nan=0.0)
    hair = np.clip((0.44 - L) / 0.12, 0, 1) * (er > 1.05) * np.maximum(brow, np.maximum(musta, beard) * (1 - nostril))
    hair = blur(hair, 1.2)
    grey = np.stack([L * 1.0 + .40, L * 1.0 + .38, L * 1.0 + .35], -1)
    out = out * (1 - hair[..., None]) + grey * hair[..., None]
# irises: green in tier A
irgb = np.array([float(x) for x in ar.iris.split(',')], np.float32)
green = iris_zone & (A[..., 1] > A[..., 0] * 1.04) & (A[..., 1] > A[..., 2] * 1.04)
g = blur(green.astype(np.float32), 0.8)[..., None]
out = out * (1 - g) + np.clip(irgb * (L[..., None] * 1.7 + .08), 0, 1) * g
r = T * (1 - m[..., None]) + out * m[..., None]
if ar.grade:
    gr = np.array([float(x) for x in ar.grade.split(',')], np.float32)
    mx, mn = r.max(2), r.min(2)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (r[..., 1] - r[..., 2]), 2 * r[..., 0] - r[..., 1] - r[..., 2])) % 360
    LL = r @ np.array([.299, .587, .114])
    sk = np.clip((sat - .12) / .1, 0, 1) * ((hue < 45) | (hue > 345)) * (LL > .25) * covered
    sk = ndimage.gaussian_filter(np.float32(sk), 1.5)[..., None]
    r = r * (1 - sk) + np.clip(r * gr, 0, 1) * sk
Image.fromarray(np.uint8(np.clip(r, 0, 1) * 255)).save(p)
print('REPAIRED', p.name, 'zone texels', int((m > .5).sum()), 'iris texels', int(green.sum()), 'gain', gain.round(3).tolist(), 'skin texels', int(sk.sum()))
