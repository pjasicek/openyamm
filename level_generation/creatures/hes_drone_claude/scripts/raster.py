"""Rasterise per-triangle attributes into UV space (numpy). raster(uv[T,3,2] blender-UV, values[T,3,C] or [T,C], size)
-> (image[H,W,C], tri index map[H,W] (-1 empty)). Image row 0 = top = UV v 1 (PNG convention)."""
import numpy as np


def raster(uv, values, size):
    H = W = size
    out = np.zeros((H, W, values.shape[-1]), np.float32); tid = -np.ones((H, W), np.int32)
    P = np.stack([uv[..., 0] * W - 0.5, (1 - uv[..., 1]) * H - 0.5], -1)
    per_vertex = values.ndim == 3
    for t in range(len(uv)):
        p = P[t]; x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W - 1), min(y1, H - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        l2 = 1 - l0 - l1
        e = -0.02
        inside = (l0 >= e) & (l1 >= e) & (l2 >= e)
        if not inside.any():
            continue
        if per_vertex:
            v = values[t]
            val = l0[..., None] * v[0] + l1[..., None] * v[1] + l2[..., None] * v[2]
        else:
            val = np.broadcast_to(values[t], xs.shape + (values.shape[-1],))
        out[ys[inside], xs[inside]] = val[inside]; tid[ys[inside], xs[inside]] = t
    return out, tid
