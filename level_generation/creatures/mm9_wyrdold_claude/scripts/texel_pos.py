#!/usr/bin/env python3
"""Rest position of every body-set texel (material 0) of work/uv.npz: work/texel_pos.npy (S x S x 3, float32, NaN outside) and the part id
(work/texel_part.npy, -1 outside) and the uv-npz face index (work/texel_face.npy). Args: [size]"""
import sys
import numpy as np
S = int(sys.argv[1]) if len(sys.argv) > 1 else 2048; MAT = int(sys.argv[2]) if len(sys.argv) > 2 else 0; SUF = '' if MAT == 0 else '_head'
D = np.load('work/uv.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']
P = np.full((S, S, 3), np.nan, np.float32); part = np.full((S, S), -1, np.int16); face = np.full((S, S), -1, np.int32)
for f in np.where(mat == MAT)[0]:
    q = uv[tri[f]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]
    ok = (l3 > -0.01).all(1)
    if not ok.any(): continue
    yy, xx = pts[ok, 1].astype(int), pts[ok, 0].astype(int)
    P[yy, xx] = l3[ok] @ co[tri[f]]; part[yy, xx] = comp[tri[f][0]]; face[yy, xx] = f
np.save(f'work/texel_pos{SUF}.npy', P); np.save(f'work/texel_part{SUF}.npy', part); np.save(f'work/texel_face{SUF}.npy', face); print('TEXELPOS', int((part >= 0).sum()))
