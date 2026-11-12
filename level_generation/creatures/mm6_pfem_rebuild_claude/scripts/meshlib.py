"""Small numpy mesh helpers shared by this project's scripts."""
import numpy as np


def sample(co, tri, n=400000, seed=0, faces=None):
    """area-weighted random surface points; returns points, triangle index"""
    t = tri if faces is None else tri[faces]
    a = np.linalg.norm(np.cross(co[t[:, 1]] - co[t[:, 0]], co[t[:, 2]] - co[t[:, 0]]), axis=1)
    rng = np.random.default_rng(seed); k = rng.choice(len(t), n, p=a / a.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    b = np.c_[1 - s, s * (1 - r2), s * r2]
    p = (co[t[k]] * b[:, :, None]).sum(1)
    return p, (k if faces is None else np.asarray(faces).nonzero()[0][k] if np.asarray(faces).dtype == bool else np.asarray(faces)[k])


def profile(p, z0, z1, step=0.004, xw=0.006):
    """front-most y (min) per z bin in the mid slab"""
    m = np.abs(p[:, 0]) < xw; zs = np.arange(z0, z1, step); out = []
    for z in zs:
        s = p[m & (np.abs(p[:, 2] - z) < step / 2)]
        out.append(s[:, 1].min() if len(s) else np.nan)
    return zs, np.array(out)


def normals(co, tri):
    n = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)


def vnormals(co, tri):
    n = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
    vn = np.zeros_like(co)
    for k in range(3): np.add.at(vn, tri[:, k], n)
    return vn / np.maximum(np.linalg.norm(vn, axis=1)[:, None], 1e-12)


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def posmap(co, tri, uv, faces, size):
    """per-texel 3D position (nan where no face) and face index (-1) for the given faces of a per-vertex UV layout"""
    P = np.full((size, size, 3), np.nan); F = -np.ones((size, size), int)
    for f in faces:
        t = uv[tri[f]] * [size, size]; t[:, 1] = size - t[:, 1]
        x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = t; v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12: continue
        px, py = xs - a[0], ys - a[1]
        l1 = (px * v1[1] - v1[0] * py) / den; l2 = (v0[0] * py - px * v0[1]) / den; l0 = 1 - l1 - l2
        ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
        if not ins.any(): continue
        p = co[tri[f]]; q = l0[ins, None] * p[0] + l1[ins, None] * p[1] + l2[ins, None] * p[2]
        yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
        P[yy, xx] = q; F[yy, xx] = f
    return P, F
