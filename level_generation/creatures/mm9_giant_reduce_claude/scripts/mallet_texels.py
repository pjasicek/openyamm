#!/usr/bin/env python3
"""Rasterise the rebuilt mallet's UV layout (work/mallet_new.npz) at RES: per covered texel the triangle, barycentric
weights, bind-space position and interpolated normal -> work/mallet_texels.npz (input of mallet_rays.py in Blender).
A texel counts when its centre lies in the triangle, or within 0.7 px of it (keeps island borders filled)."""
import numpy as np
RES = 1024
d = np.load('work/mallet_new.npz'); P, N, UV, I = d['P'].astype(float), d['N'].astype(float), d['UV'].astype(float), d['I']
owner = -np.ones((RES, RES), int); bary = np.zeros((RES, RES, 3)); dist = np.full((RES, RES), np.inf)
for f, (a, b, c) in enumerate(I):
    ua, ub, uc = UV[a] * RES, UV[b] * RES, UV[c] * RES
    lo = np.floor(np.minimum(np.minimum(ua, ub), uc) - 1).astype(int).clip(0, RES - 1)
    hi = np.ceil(np.maximum(np.maximum(ua, ub), uc) + 1).astype(int).clip(0, RES - 1)
    xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
    pc = np.stack([xs + 0.5, ys + 0.5], -1).reshape(-1, 2)
    M = np.array([ub - ua, uc - ua]).T
    if abs(np.linalg.det(M)) < 1e-9:
        continue
    l12 = np.linalg.solve(M, (pc - ua).T).T; l0 = 1 - l12.sum(1); L = np.column_stack([l0, l12])
    # distance outside in px (approximate: most negative barycentric scaled by the triangle's smallest height)
    hmin = abs(np.linalg.det(M)) / max(np.linalg.norm(ub - ua), np.linalg.norm(uc - ub), np.linalg.norm(ua - uc))
    out = np.maximum(-L.min(1), 0) * hmin
    ok = out < 0.7
    xi, yi = xs.reshape(-1)[ok], ys.reshape(-1)[ok]
    better = out[ok] < dist[yi, xi]
    xi, yi = xi[better], yi[better]
    Lc = np.clip(L[ok][better], 0, None); Lc /= Lc.sum(1, keepdims=True)
    owner[yi, xi] = f; bary[yi, xi] = Lc; dist[yi, xi] = out[ok][better]
ys, xs = np.nonzero(owner >= 0); f = owner[ys, xs]; L = bary[ys, xs]
pos = (L[:, :, None] * P[I[f]]).sum(1); nor = (L[:, :, None] * N[I[f]]).sum(1); nor /= np.linalg.norm(nor, axis=1, keepdims=True)
np.savez('work/mallet_texels.npz', x=xs, y=ys, face=f, bary=L, pos=pos, nor=nor)
print('TEXELS', len(xs), 'coverage', round(len(xs) / RES / RES, 3))
