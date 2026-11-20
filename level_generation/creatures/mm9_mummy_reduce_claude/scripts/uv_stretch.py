#!/usr/bin/env python3
"""Texture stretch per LOD0 face: anisotropy (sigma max / sigma min of the 3D -> UV map) and the UV/3D area scale against the
primitive's median. A collapse that drags a corner across a painted band leaves a sliver in UV over a wide face in 3D (the
reduced forearm's smeared chevron, 2026-11-04). Usage: uv_stretch.py <glb> [<glb> ...] -> counts per primitive."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbio  # noqa: E402


def aniso(P, UV, T):
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    e1 = b - a; e2 = c - a; n = np.cross(e1, e2); A = np.linalg.norm(n, axis=1)
    x = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-20); y = np.cross(n / np.maximum(A[:, None], 1e-20), x)
    p1 = np.stack([(e1 * x).sum(1), np.zeros(len(T))], 1); p2 = np.stack([(e2 * x).sum(1), (e2 * y).sum(1)], 1)
    u1 = UV[T[:, 1]] - UV[T[:, 0]]; u2 = UV[T[:, 2]] - UV[T[:, 0]]
    Pm = np.stack([p1, p2], 2); Um = np.stack([u1, u2], 2)                     # columns are edges
    M = Um @ np.linalg.inv(Pm + np.eye(2) * 1e-12)
    s = np.linalg.svd(M, compute_uv=False)
    return s[:, 0] / np.maximum(s[:, 1], 1e-12), A


if __name__ == '__main__':
    for g in sys.argv[1:]:
        _, _, _, D = glbio.load(g, 'Mummy')
        for name, d in D.items():
            r, A = aniso(d['P'], d['UV'], d['T'])
            print(g, name, len(r), 'aniso p50/p90/p99/max', np.percentile(r, [50, 90, 99]).round(2), round(float(r.max()), 1),
                  'faces >3', int((r > 3).sum()), '>4', int((r > 4).sum()), '>6', int((r > 6).sum()))
