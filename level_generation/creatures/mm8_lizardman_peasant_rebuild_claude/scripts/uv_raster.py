#!/usr/bin/env python3
"""Rasterise a GLB's LOD0 primitive in UV space: per texel the rest position (glTF metres, Y up), the triangle index
and coverage, at SIZE x SIZE. Writes <out>.npz (pos HxWx3, tri HxW, cov HxW). Usage: uv_raster.py <glb> <out> [size]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp
g = gp.Glb(sys.argv[1]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
p = g.json['meshes'][0]['primitives'][0]
P = g.accessor(p['attributes']['POSITION']).astype(float); UV = g.accessor(p['attributes']['TEXCOORD_0']).astype(float)
T = g.accessor(p['indices']).astype(int).reshape(-1, 3)
pos = np.zeros((N, N, 3)); tri = -np.ones((N, N), int)
for k, t in enumerate(T):
    uv = UV[t] * N - 0.5
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
    if x1 < x0 or y1 < y0: continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
    q = np.stack([xs.ravel(), ys.ravel()], 1).astype(float)
    a, b, c = uv; v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-12: continue
    d = q - a; l1 = (d[:, 0] * v1[1] - v1[0] * d[:, 1]) / den; l2 = (v0[0] * d[:, 1] - d[:, 0] * v0[1]) / den; l0 = 1 - l1 - l2
    m = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
    if not m.any(): continue
    X, Y = xs.ravel()[m], ys.ravel()[m]
    pos[Y, X] = l0[m, None] * P[t[0]] + l1[m, None] * P[t[1]] + l2[m, None] * P[t[2]]; tri[Y, X] = k
np.savez_compressed(sys.argv[2], pos=pos.astype(np.float32), tri=tri, cov=tri >= 0)
print('RASTER', sys.argv[2], 'coverage', round(float((tri >= 0).mean()), 3))
