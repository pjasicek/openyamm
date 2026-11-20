#!/usr/bin/env python3
"""Per-texel rest positions of one set (faces.npz, PartUV): <mat> <size> <out npz> -> pos (S,S,3), ok (S,S), face (S,S)."""
import sys
import numpy as np
Z = np.load('work/faces.npz'); UV, MAT, CO = Z['uv'], Z['mat'], Z['co']
k, S, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
pos = np.zeros((S, S, 3), np.float32); ok = np.zeros((S, S), bool); fid = -np.ones((S, S), np.int32)
for f in np.nonzero(MAT == k)[0]:
    t = UV[f] * [S, S]; t[:, 1] = S - t[:, 1]
    x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
    if x1 < x0 or y1 < y0: continue
    X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = t; m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-9: continue
    l = np.linalg.solve(m, np.stack([X.ravel() - a[0], Y.ravel() - a[1]]))
    w = np.stack([1 - l[0] - l[1], l[0], l[1]], 1); inside = (w >= -0.02).all(1)
    p = w[inside] @ CO[f]; xi = X.ravel()[inside].astype(int); yi = Y.ravel()[inside].astype(int)
    pos[yi, xi] = p; ok[yi, xi] = True; fid[yi, xi] = f
np.savez_compressed(out, pos=pos, ok=ok, face=fid); print('TEXPOS', k, S, int(ok.sum()))
