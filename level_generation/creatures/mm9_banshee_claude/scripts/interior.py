"""Faces of a closed-ish shell that look into it: from the face centre along its own normal a ray hits the shell again within `reach`. Those are the mouth's inner walls (gums, palate). numpy Moller-Trumbore."""
import numpy as np


def interior_faces(P, reach=0.3, eps=1e-5):
    """P: (n, 3, 3) triangles. Returns a boolean mask."""
    a, b, c = P[:, 0], P[:, 1], P[:, 2]
    e1, e2 = b - a, c - a
    N = np.cross(e1, e2); L = np.linalg.norm(N, axis=1, keepdims=True)
    good = L[:, 0] > 1e-12
    N = N / np.maximum(L, 1e-12)
    O = P.mean(1) + N * eps
    out = np.zeros(len(P), bool)
    for i in np.where(good)[0]:
        d = N[i]
        p = np.cross(d, e2)
        det = (e1 * p).sum(1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        s = O[i] - a
        u = (s * p).sum(1) * inv
        q = np.cross(s, e1)
        v = (q @ d) * inv
        t = (e2 * q).sum(1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < reach)
        hit[i] = False
        out[i] = hit.any()
    return out
