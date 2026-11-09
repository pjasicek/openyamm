#!/usr/bin/env python3
"""Carry the Meshy head maps (meshy/head_retexture_v1, 2K, painted on the old HeadUV) into the head_uv_texpass.py
layout (texture quality pass 2026-10-30), so compose_head.py reads them as if Meshy had painted the new layout.

Every texel of the new 2K canvas belongs to a head triangle (gutters to the nearest triangle, with barycentric
coordinates extrapolated, so the gutter holds the continuation of the old paint and its own padding); its old HeadUV
is sampled bicubically. Normal map: Meshy stores +y down; the tangent-space xy is rotated by the orthogonal part of
each triangle's old -> new UV map, so the surface relief is unchanged under the new chart orientation.
Writes work/head_relayout/texture_urls_0_{base_color,normal,roughness,metallic}.png.
Usage: resample_head.py [size=2048]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
M = HERE / 'meshy' / 'head_retexture_v1'
OUT = HERE / 'work' / 'head_relayout'
N = int(sys.argv[1]) if len(sys.argv) > 1 else 2048
d = np.load(HERE / 'work' / 'head_uv_texpass.npz')
old, new = d['old'].astype(np.float64), d['new'].astype(np.float64)

tid = np.full((N, N), -1, np.int32)
for t, p in enumerate(new * N):
    x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), N - 1)
    y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), N - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = p
    w0 = (b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])
    w1 = (c[0] - b[0]) * (gy - b[1]) - (c[1] - b[1]) * (gx - b[0])
    w2 = (a[0] - c[0]) * (gy - c[1]) - (a[1] - c[1]) * (gx - c[0])
    inside = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
    yy, xx = np.nonzero(inside)
    tid[N - 1 - (yy + y0), xx + x0] = t
covered = tid >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
tid = tid[iy, ix]

rows, cols = np.mgrid[0:N, 0:N]
u = (cols + 0.5) / N
v = 1.0 - (rows + 0.5) / N
A = new[tid]                                    # (N, N, 3, 2) new corners
e1, e2 = A[..., 1, :] - A[..., 0, :], A[..., 2, :] - A[..., 0, :]
den = e1[..., 0] * e2[..., 1] - e1[..., 1] * e2[..., 0]
den = np.where(np.abs(den) < 1e-14, 1e-14, den)
qx, qy = u - A[..., 0, 0], v - A[..., 0, 1]
l1 = (qx * e2[..., 1] - qy * e2[..., 0]) / den
l2 = (e1[..., 0] * qy - e1[..., 1] * qx) / den
O = old[tid]
ouv = O[..., 0, :] + l1[..., None] * (O[..., 1, :] - O[..., 0, :]) + l2[..., None] * (O[..., 2, :] - O[..., 0, :])
S0 = 2048
coords = [(1.0 - ouv[..., 1]) * S0 - 0.5, ouv[..., 0] * S0 - 0.5]
OUT.mkdir(parents=True, exist_ok=True)


def sample(img, order=3):
    a = np.asarray(img, np.float32)
    if a.ndim == 2:
        a = a[..., None]
    out = np.stack([ndimage.map_coordinates(a[..., k], coords, order=order, mode='nearest') for k in range(a.shape[2])], -1)
    return out


for name in ('base_color', 'roughness', 'metallic'):
    src = Image.open(M / f'texture_urls_0_{name}.png')
    src = src.convert('RGB') if name == 'base_color' else src.convert('L')
    assert src.size == (S0, S0), src.size
    out = sample(src)
    out = np.clip(out, 0, 255).round().astype(np.uint8)
    Image.fromarray(out if out.shape[2] == 3 else out[..., 0]).save(OUT / f'texture_urls_0_{name}.png')

# normal: per-triangle rotation of tangent-space xy (true frame: +y up = stored y negated)
Jn = np.stack([new[:, 1] - new[:, 0], new[:, 2] - new[:, 0]], -1)       # (T, 2, 2) columns = edges
Jo = np.stack([old[:, 1] - old[:, 0], old[:, 2] - old[:, 0]], -1)
R = np.tile(np.eye(2), (len(new), 1, 1))
ok = np.abs(np.linalg.det(Jo)) > 1e-14
Amap = Jn[ok] @ np.linalg.inv(Jo[ok])
U, _, Vt = np.linalg.svd(Amap)
R[ok] = U @ Vt
nrm = sample(Image.open(M / 'texture_urls_0_normal.png').convert('RGB')) / 255 * 2 - 1
xy = np.stack([nrm[..., 0], -nrm[..., 1]], -1)
Rt = R[tid]
xy2 = np.einsum('hwij,hwj->hwi', Rt, xy)
n2 = np.stack([xy2[..., 0], -xy2[..., 1], nrm[..., 2]], -1)
n2 /= np.maximum(np.linalg.norm(n2, axis=-1, keepdims=True), 1e-6)
Image.fromarray(np.clip((n2 + 1) / 2 * 255, 0, 255).round().astype(np.uint8)).save(OUT / 'texture_urls_0_normal.png')
det = np.linalg.det(R[ok])
print('RESAMPLED', N, 'covered %.1f %%' % (100 * covered.mean()), 'triangles', len(new),
      'reflected', int((det < 0).sum()), 'rotation p50 deg', round(float(np.degrees(np.median(np.abs(
          np.arctan2(R[ok][:, 1, 0], R[ok][:, 0, 0]))))), 1))
