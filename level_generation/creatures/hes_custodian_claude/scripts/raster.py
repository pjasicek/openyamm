"""Texel rasterisation of a triangle dump (dump_tris.py): per texel the triangle index (-1 empty), the 3D position
and the face normal, at res x res over the whole 0..1 UV square (v up, image row 0 at v = 1)."""
import numpy as np


def rasterise(uv, co, n, res):
    tri = np.full((res, res), -1, np.int32)
    pos = np.zeros((res, res, 3), np.float32)
    for t in range(len(uv)):
        p = uv[t] * res
        p = np.stack([p[:, 0], res - p[:, 1]], 1)              # image x, y
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, res - 1), min(y1, res - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not inside.any():
            continue
        yy, xx = (ys[inside] - 0.5).astype(int), (xs[inside] - 0.5).astype(int)
        tri[yy, xx] = t
        pos[yy, xx] = (w0[inside, None] * co[t, 0] + w1[inside, None] * co[t, 1] + w2[inside, None] * co[t, 2])
    return tri, pos


def dilate(img, mask, steps):
    """Grow img's values from mask into the unmasked neighbourhood `steps` texels (nearest-neighbour fill)."""
    img = img.copy(); mask = mask.copy()
    for _ in range(steps):
        grown = mask.copy(); acc = np.zeros_like(img, dtype=np.float64); cnt = np.zeros(mask.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m = np.roll(mask, (dy, dx), (0, 1)); v = np.roll(img, (dy, dx), (0, 1))
            add = m & ~mask
            acc[add] += v[add]; cnt[add] += 1; grown |= add
        new = grown & ~mask
        img[new] = (acc[new] / cnt[new][..., None] if img.ndim == 3 else acc[new] / cnt[new]).astype(img.dtype)
        mask = grown
    return img
