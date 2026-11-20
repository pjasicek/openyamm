#!/usr/bin/env python3
"""Connected pieces of a dumped mesh npz (work/mesh_in.npz or work/mesh_r55.npz): faces, centre, extent, height
along the longest axis. Usage: pieces_report.py <npz> [min faces shown, default 0]"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load(sys.argv[1]); f = d['faces']; v = d['verts']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl, minlength=lab.max() + 1)
rows = []
for c in np.argsort(-sizes):
    if sizes[c] == 0:
        continue
    p = v[np.unique(f[fl == c])]
    rows.append((c, sizes[c], p.mean(0), p.max(0) - p.min(0)))
print('pieces', len(rows))
for c, s, m, ext in rows:
    print(f'{c:4d} {s:6d} centre {np.round(m, 3)} extent {np.round(ext, 3)}')
