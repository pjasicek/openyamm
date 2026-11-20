"""Texel raster: uv triangles (Blender v up, 0..1) -> per-texel face and barycentrics at size S. Image row 0 = v 1 (the texture as stored, glTF v down)."""
import numpy as np
def raster(uv, S, pad=0):
    F = -np.ones((S, S), np.int32); B = np.zeros((S, S, 3), np.float32)
    for i, t in enumerate(uv):
        p = np.c_[t[:, 0] * S - .5, (1 - t[:, 1]) * S - .5]
        x0, x1 = int(np.floor(p[:, 0].min())) - pad, int(np.ceil(p[:, 0].max())) + pad; y0, y1 = int(np.floor(p[:, 1].min())) - pad, int(np.ceil(p[:, 1].max())) + pad
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9: continue
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        l2 = 1 - l0 - l1
        m = (l0 >= -.02) & (l1 >= -.02) & (l2 >= -.02)
        F[ys[m], xs[m]] = i; B[ys[m], xs[m]] = np.c_[l0[m], l1[m], l2[m]]
    return F, B
def positions(F, B, corner3d):
    """per-texel 3D point; corner3d (N,3,3)"""
    m = F >= 0; P = np.zeros((*F.shape, 3), np.float32)
    P[m] = (corner3d[F[m]] * B[m][..., None]).sum(1)
    return P, m
