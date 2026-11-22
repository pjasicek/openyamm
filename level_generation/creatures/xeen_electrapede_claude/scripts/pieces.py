#!/usr/bin/env python3
"""Connected pieces of work/<name>.npz with box, centroid, triangle count, boundary edges. Usage: pieces.py <name>"""
import sys, numpy as np
from collections import Counter
d = np.load(f'work/{sys.argv[1]}.npz'); co = d['co']; tris = d['tris']
n = len(co); par = np.arange(n)
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for t in tris:
    a = find(t[0])
    for b in t[1:]:
        b = find(b)
        if a != b: par[b] = a
lab = np.array([find(i) for i in range(n)])
u, inv = np.unique(lab, return_inverse=True)
tl = inv[tris[:, 0]]
ec = Counter()
for t in tris:
    for i in range(3):
        e = tuple(sorted((t[i], t[(i + 1) % 3]))); ec[e] += 1
bnd = Counter(inv[e[0]] for e, c in ec.items() if c == 1)
rows = []
for k in range(len(u)):
    p = co[inv == k]
    rows.append((k, len(p), int((tl == k).sum()), p.min(0), p.max(0), p.mean(0), bnd.get(k, 0)))
rows.sort(key=lambda r: r[5][1])
for k, nv, nt, mn, mx, c, b in rows:
    print(f'{k:3d} v{nv:4d} t{nt:4d} y[{mn[1]:+.3f},{mx[1]:+.3f}] x[{mn[0]:+.3f},{mx[0]:+.3f}] z[{mn[2]:+.3f},{mx[2]:+.3f}] bnd {b}')
np.save(f'work/{sys.argv[1]}_label.npy', inv)
