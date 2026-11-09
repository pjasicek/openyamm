#!/usr/bin/env python3
"""Where uv_gates.py failures sit: faces in overlap pairs and zero-area faces, split into body / bag / cap.
Usage: uv_gate_where.py <uv3d.npz> <uv blend bag npz>"""
import sys
import numpy as np

d = np.load(sys.argv[1])
b = np.load(sys.argv[2])
S = 2048
uv = d['uv'].astype(np.float64) * S
n = len(uv)
new = b['uv_new'].astype(np.float64) * S
kind = np.zeros(n, int)
key = {tuple(np.round(t.ravel(), 2)): k for t, k in zip(new, b['kind'])}
for i, t in enumerate(uv):
    kind[i] = key.get(tuple(np.round(t.ravel(), 2)), 0)
print('kinds', np.unique(kind, return_counts=True))
owner = -np.ones((S, S), np.int32)
pairs = {}
zero = []
for t, p in enumerate(uv):
    a, b_, c = p
    den = (b_[1] - c[1]) * (a[0] - c[0]) + (c[0] - b_[0]) * (a[1] - c[1])
    if abs(den) < 1e-6:
        zero.append(t)
        continue
    x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), S - 1)
    y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    l1 = ((b_[1] - c[1]) * (gx - c[0]) + (c[0] - b_[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    iy, ix = np.nonzero((l1 > 1e-3) & (l2 > 1e-3) & (1 - l1 - l2 > 1e-3))
    iy, ix = iy + y0, ix + x0
    prev = owner[iy, ix]
    for q in np.unique(prev[prev >= 0]):
        pairs[(int(q), t)] = int((prev == q).sum())
    owner[iy, ix] = t
from collections import Counter
print('zero', len(zero), Counter(kind[zero].tolist()), [t for t in zero][:12])
print('pair kinds', Counter(tuple(sorted((kind[a], kind[b_]))) for a, b_ in pairs))
print('texels by pair kind', Counter({}) or {k: sum(v for (a, b_), v in pairs.items() if tuple(sorted((kind[a], kind[b_]))) == k)
                                             for k in {tuple(sorted((kind[a], kind[b_]))) for a, b_ in pairs}})
top = sorted(pairs.items(), key=lambda kv: -kv[1])[:8]
for (a, b_), v in top:
    print(a, b_, v, kind[a], kind[b_], d['xyz'][a].mean(0).round(2), d['xyz'][b_].mean(0).round(2))
