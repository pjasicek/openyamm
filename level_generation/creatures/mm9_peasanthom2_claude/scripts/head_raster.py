"""Texel rest positions of the head set: raster(N) -> N x N x 3 (NaN outside), from work/head_faces.npz (head_dump.py)."""
import numpy as np
def raster(N, path='work/head_faces.npz', keep=None):
    D = np.load(path)
    P = np.full((N, N, 3), np.nan)
    for uv, p in zip(D['UV'], D['P']):
        if keep is not None and not keep(p):
            continue
        q = uv * N; q[:, 1] = N - q[:, 1]
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0:
            continue
        c = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, d = q
        m = np.array([[b[0] - a[0], d[0] - a[0]], [b[1] - a[1], d[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-12:
            continue
        l = np.linalg.solve(m, (c - a).T).T
        w = np.column_stack([1 - l.sum(1), l])
        ok = (w >= -1e-3).all(1)
        P[c[ok, 1].astype(int), c[ok, 0].astype(int)] = w[ok] @ p
    return P
