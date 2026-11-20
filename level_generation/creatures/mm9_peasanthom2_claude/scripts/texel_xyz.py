#!/usr/bin/env python3
"""Rest-pose position per texel from a uv_xyz.py dump (v2/scripts/uv_xyz.py). Library: texel_xyz(npz, size, faces mask)
-> (xyz HxWx3, covered HxW bool, face index HxW). UV v up (row 0 = v 1)."""
import numpy as np


def texel_xyz(npz, size, keep=None):
    d = np.load(npz)
    uv, xyz = d['uv'], d['xyz']
    out = np.zeros((size, size, 3)); cov = np.zeros((size, size), bool); fid = -np.ones((size, size), np.int32)
    for f in range(len(uv)):
        if keep is not None and not keep[f]:
            continue
        p = uv[f] * size; p[:, 1] = size - p[:, 1]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        l3 = 1 - l1 - l2
        m = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        if not m.any():
            continue
        P = l1[..., None] * xyz[f, 0] + l2[..., None] * xyz[f, 1] + l3[..., None] * xyz[f, 2]
        yy, xx = np.nonzero(m)
        out[y0 + yy, x0 + xx] = P[m]; cov[y0 + yy, x0 + xx] = True; fid[y0 + yy, x0 + xx] = f
    return out, cov, fid
