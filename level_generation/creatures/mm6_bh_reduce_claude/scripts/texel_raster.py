"""Rasterise faces into texel space: for each texel covered by a selected face, the face id and the rest-pose 3D point
(barycentric). Shared by repair_texture.py and ivory_cell.py."""
import numpy as np


def raster(uv, xyz, faces_sel, w, h):
    """uv (F,3,2), xyz (F,3,3); returns rows, cols, face ids, 3D points of every covered texel centre."""
    R, C, I, P = [], [], [], []
    for i in faces_sel:
        t = uv[i] * [w, h]; t[:, 1] = h - t[:, 1]           # texel space, rows down
        x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, w)), np.arange(max(y0, 0), min(y1 + 1, h)))
        px = np.stack([xs.ravel() + .5, ys.ravel() + .5], 1)
        a, b, c = t; v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        d = px - a; l1 = (d[:, 0] * v1[1] - v1[0] * d[:, 1]) / den; l2 = (v0[0] * d[:, 1] - d[:, 0] * v0[1]) / den
        m = (l1 >= -.02) & (l2 >= -.02) & (l1 + l2 <= 1.02)
        if not m.any():
            continue
        l0 = 1 - l1[m] - l2[m]
        R.append(ys.ravel()[m]); C.append(xs.ravel()[m]); I.append(np.full(m.sum(), i))
        P.append(l0[:, None] * xyz[i, 0] + l1[m, None] * xyz[i, 1] + l2[m, None] * xyz[i, 2])
    return np.concatenate(R), np.concatenate(C), np.concatenate(I), np.concatenate(P)
