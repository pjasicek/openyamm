#!/usr/bin/env python3
"""Numpy z-buffer of the head faces (work/head_faces.npz, Blender space, front -y), for layer diagnosis and visibility. Import: render(P, cols, view, res) -> rgb, face id."""
import numpy as np


def basis(az, el):
    a, e = np.radians(az), np.radians(el)
    d = np.array([np.sin(a) * np.cos(e), -np.cos(a) * np.cos(e), np.sin(e)])       # from the object to the camera
    r = np.cross([0, 0, 1], d); r /= np.linalg.norm(r); u = np.cross(d, r)
    return r, u, d


def zbuffer(P, az, el, res=700, half=0.17, c=(0, 0.02, 0.8)):
    r, u, d = basis(az, el)
    Q = P - np.array(c)
    px = np.stack([Q @ r, Q @ u, Q @ d], -1)
    sx = (px[..., 0] / half + 1) * res / 2; sy = (1 - px[..., 1] / half) * res / 2; z = px[..., 2]
    Z = np.full((res, res), -1e9); F = np.full((res, res), -1, np.int32)
    for k in range(len(P)):
        ax, bx, cx = sx[k]; ay, by, cy = sy[k]
        x0, x1 = int(max(min(ax, bx, cx), 0)), int(min(max(ax, bx, cx) + 1, res - 1)); y0, y1 = int(max(min(ay, by, cy), 0)), int(min(max(ay, by, cy) + 1, res - 1))
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        l0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den; l1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den; l2 = 1 - l0 - l1
        m = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        zz = l0 * z[k, 0] + l1 * z[k, 1] + l2 * z[k, 2]
        sub = Z[y0:y1 + 1, x0:x1 + 1]; w = m & (zz > sub)
        sub[w] = zz[w]; F[y0:y1 + 1, x0:x1 + 1][w] = k
    return F, Z, (r, u, d)
