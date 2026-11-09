"""
An estimate of the compiler's outline count (editor/import/IndoorDerivedGeometry.cpp: at most 7 000): the edges of the
drawn, static, non-portal faces that border a floor (normal z >= 0.45), split at collinear vertices, without the
coplanar joins. `count(faces)` takes [(points (n, 3) native ints)] of those faces.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np


def _normal(p: np.ndarray) -> np.ndarray:
    n = np.zeros(3)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        n += np.cross(a, b)
    length = np.linalg.norm(n)
    return n / length if length > 0 else n


def count(faces: list, split_faces: list | None = None) -> int:
    """faces: the drawn static faces; split_faces: every non-moving face (invisible, portal, detail too), whose
    vertices split the outline edges as the compiler's outlineVertices do (default: faces)."""
    rings = [np.asarray(f, float) for f in faces]
    normals = [_normal(r) for r in rings]
    planes = [(n, float(n @ r[0])) for n, r in zip(normals, rings)]
    floor = [n[2] >= 0.45 for n in normals]
    ceiling = [n[2] <= -0.45 for n in normals]
    split = rings if split_faces is None else [np.asarray(f, float) for f in split_faces]
    vertices = np.unique(np.concatenate(split), axis=0)
    order = np.argsort(vertices[:, 0])
    xs = vertices[order, 0]
    vid = {tuple(v): i for i, v in enumerate(vertices)}
    edges = defaultdict(list)
    for fid, r in enumerate(rings):
        if ceiling[fid]:
            continue                          # facet types 5 and 6 add no edges
        for k in range(len(r)):
            a, b = r[k], r[(k + 1) % len(r)]
            if a[0] == b[0] and a[1] == b[1]:
                continue                      # vertical edges are never outlines
            lo, hi = np.searchsorted(xs, min(a[0], b[0]) - 0.01), np.searchsorted(xs, max(a[0], b[0]) + 0.01, "right")
            cand = vertices[order[lo:hi]]
            d = b - a
            ll = d @ d
            t = (cand - a) @ d / ll
            on = (t >= 0) & (t <= 1) & (np.abs(a + t[:, None] * d - cand).max(1) < 0.01)
            pts = sorted(zip(t[on], (vid[tuple(c)] for c in cand[on])))
            for (_, i), (_, j) in zip(pts, pts[1:]):
                edges[(min(i, j), max(i, j))].append(fid)
    total = 0
    for edge, fids in edges.items():
        if not any(floor[f] for f in fids):
            continue
        first = fids[0]
        n, d0 = planes[first]
        second = first
        for f in fids:
            r = rings[f]
            dist = r @ n - d0
            if np.abs(dist).max() > 0.01:              # classifyFace: 0.01 off the plane
                second = f
                break
        if len(fids) > 1 and first == second:
            continue
        total += 1
    return total
