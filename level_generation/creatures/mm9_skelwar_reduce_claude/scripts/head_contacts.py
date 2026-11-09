#!/usr/bin/env python3
"""Rest gaps between the pieces of the head primitive (PRIM=0 MAXT=2000: the body primitive) (all rigid on Bip01 Head, so no clip changes them): for every piece of
<= 200 triangles (horns, guards, insignia), the nearest distance to any other head piece, installed vs candidate, matched by
centroid. Usage: head_contacts.py <installed.glb> <candidate.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402


import os
PRIM = int(os.environ.get('PRIM', '1')); MAXT = int(os.environ.get('MAXT', '200'))


def pieces(path):
    m = Model(Glb(path)); P, T = m.primitives[PRIM]['positions'], m.primitives[PRIM]['triangles']
    k = np.round(P / 1e-6).astype(np.int64); _, w = np.unique(k, axis=0, return_inverse=True); w = w.ravel(); t = w[T]; n = w.max() + 1
    r = np.concatenate([t[:, 0], t[:, 1], t[:, 2]]); c = np.concatenate([t[:, 1], t[:, 2], t[:, 0]])
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fl = lab[t[:, 0]]
    out = {}
    for q in np.unique(fl):
        s = fl == q
        if s.sum() > MAXT or np.ptp(P[T[s]].reshape(-1, 3), 0).max() < 0.03:
            continue
        others = T[~s]; vs = P[np.unique(T[s])]
        cen = P[others].mean(1); _, nn = cKDTree(cen).query(vs, k=64); f = nn.ravel()
        qq, _ = closest_on_triangles(np.repeat(vs, 64, 0), P[others[f, 0]], P[others[f, 1]], P[others[f, 2]])
        out[tuple(np.round(P[T[s]].mean((0, 1)), 2))] = (int(s.sum()), float(np.linalg.norm(qq - np.repeat(vs, 64, 0), axis=1).min()) * 1000)
    return out


A, B = pieces(sys.argv[1]), pieces(sys.argv[2])
kb = np.array(list(B)); 
for ka, (na, ga) in sorted(A.items(), key=lambda x: x[0][1]):
    j = int(np.linalg.norm(kb - np.array(ka), axis=1).argmin()); nb, gb = B[tuple(kb[j])]
    print(f'piece at {ka}: {na:4d} -> {nb:4d} tris, gap to the rest of the head {ga:5.2f} -> {gb:5.2f} mm')
