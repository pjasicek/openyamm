#!/usr/bin/env python3
"""Labels robe faces that are the inside: hood lining, sleeve cups, the hem's cap. Writes work/inner.npy (per face of the asm, bool). Args: <asm npz> <out npy>"""
import sys, numpy as np
D = np.load(sys.argv[1]); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]; ax, sh = D['ax'], D['sh']
k = names.index('robe'); ft = comp[tri[:, 0]] == k
c = co[tri].mean(1); n = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
inner = np.zeros(len(tri), bool)
# hood lining: facing the head, above the collar
rad = c - np.c_[np.zeros(len(c)), np.full(len(c), -0.01), c[:, 2]]
hood = ft & (c[:, 2] > 0.60) & ((n * rad).sum(1) < 0)
inner |= hood
# sleeve cups: per side, facing the sleeve's axis or out of the cup's bottom
for s in (1, -1):
    a = ax * [s, 1, 1]; o = sh * [s, 1, 1]; t = (c - o) @ a; p = c - o - t[:, None] * a; r = np.linalg.norm(p, axis=1)
    cup = ft & (c[:, 0] * s > 0.3) & (t > 0.24) & (((n * p).sum(1) < -0.02 * r) | (r < 0.05))
    inner |= cup
# hem cap: facing down or in
rr = c.copy(); rr[:, 2] = 0
cap = ft & (c[:, 2] < -0.74) & (((n * rr).sum(1) < 0) | (n[:, 2] < -0.6))
inner |= cap
print('inner faces hood', int(hood.sum()), 'cups+cap', int(inner.sum() - hood.sum()), 'of', int(ft.sum()))
np.save(sys.argv[2], inner)
