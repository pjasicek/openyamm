"""Texel-space helpers for the texture pass: rasterise a UV layout (triangle id and barycentrics per texel centre),
bilinear sampling, gutter padding. UVs are glTF (v down: row = v * size)."""
import numpy as np
from scipy import ndimage


def raster(uv, size, grow=0.0):
    """uv (T, 3, 2) -> tri_id (S, S) int32 (-1 outside), bary (S, S, 3) float32. grow > 0 also claims texels up to
    that many texels outside a triangle (barycentrics extrapolated) where no triangle covers them."""
    S = size
    tri_id = np.full((S, S), -1, np.int32)
    bary = np.zeros((S, S, 3), np.float32)
    dist = np.full((S, S), np.inf, np.float32)
    for t, tu in enumerate(uv):
        p = tu * S
        lo = np.floor(p.min(0) - grow).astype(int)
        hi = np.ceil(p.max(0) + grow).astype(int) + 1
        x0, y0 = max(lo[0], 0), max(lo[1], 0)
        x1, y1 = min(hi[0], S), min(hi[1], S)
        if x1 <= x0 or y1 <= y0:
            continue
        M = np.array([p[1] - p[0], p[2] - p[0]]).T
        det = np.linalg.det(M)
        if abs(det) < 1e-12:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        st = (np.stack([xs.ravel(), ys.ravel()], 1) - p[0]) @ np.linalg.inv(M).T
        w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
        if grow > 0:
            # distance outside in texels: barycentric deficit times the triangle's height scale
            scale = np.sqrt(abs(det))
            d = np.maximum(-w.min(1), 0) * scale
            ok = d <= grow
        else:
            d = np.zeros(len(w))
            ok = (w >= -1e-6).all(1)
        if not ok.any():
            continue
        yy = (ys.ravel()[ok] - 0.5).astype(int)
        xx = (xs.ravel()[ok] - 0.5).astype(int)
        better = d[ok] < dist[yy, xx]
        yy, xx = yy[better], xx[better]
        tri_id[yy, xx] = t
        bary[yy, xx] = w[ok][better]
        dist[yy, xx] = d[ok][better]
    return tri_id, bary


def bilinear(img, uv):
    """img (H, W, C) float, uv (N, 2) glTF -> (N, C)."""
    h, w = img.shape[:2]
    x, y = uv[:, 0] * w - 0.5, uv[:, 1] * h - 0.5
    x0 = np.clip(np.floor(x).astype(int), 0, w - 2)
    y0 = np.clip(np.floor(y).astype(int), 0, h - 2)
    fx = np.clip(x - x0, 0, 1)[:, None]
    fy = np.clip(y - y0, 0, 1)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def nearest(img, uv):
    h, w = img.shape[:2]
    x = np.clip((uv[:, 0] * w).astype(int), 0, w - 1)
    y = np.clip((uv[:, 1] * h).astype(int), 0, h - 1)
    return img[y, x]


def corresponding_uv(tri_id, bary, uv_other):
    """For every covered texel of one layout: the same surface point's UV in another layout of the same triangles."""
    cov = tri_id >= 0
    t = tri_id[cov]
    return cov, (uv_other[t] * bary[cov][:, :, None]).sum(1)


def pad(img, covered):
    """Fills uncovered texels with the nearest covered texel's value."""
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]
