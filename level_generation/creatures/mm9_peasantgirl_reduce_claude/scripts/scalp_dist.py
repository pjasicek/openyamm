#!/usr/bin/env python3
"""Scalp under the hair (installed elf head prim): for each face of the head shell (largest connected head-part piece; the eyeballs
are separate) the distance along its normal to the hair shell (ray / triangle, Moeller-Trumbore) and the distance of its centroid to
the hair shell's open edges. Writes work/scalp_dist.npy: rows (head-prim face index, ray distance or inf, edge distance)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantgirl1e.glb', 'PeasantGirl')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part'][g['mat'] == 1]
H = D['PeasantGirlHead']; P, T = H['P'], H['T']
head = np.flatnonzero(part == 0); hair = np.flatnonzero(part == 3)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; shell = head[fl[head] == np.bincount(fl[head]).argmax()]
c = P[T[shell]].mean(1); nn = np.cross(P[T[shell, 1]] - P[T[shell, 0]], P[T[shell, 2]] - P[T[shell, 0]])
nn /= np.linalg.norm(nn, axis=1, keepdims=True)
A = P[T[hair, 0]]; E1 = P[T[hair, 1]] - A; E2 = P[T[hair, 2]] - A
dist = np.full(len(shell), np.inf)
for i0 in range(0, len(shell), 256):
    o = c[i0:i0 + 256, None, :]; d = nn[i0:i0 + 256, None, :]
    pv = np.cross(d, E2[None]); det = (E1[None] * pv).sum(-1); inv = 1 / np.where(np.abs(det) < 1e-12, np.nan, det)
    tv = o - A[None]; u = (tv * pv).sum(-1) * inv; qv = np.cross(tv, E1[None]); v = (d * qv).sum(-1) * inv; t = (E2[None] * qv).sum(-1) * inv
    ok = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5)
    dist[i0:i0 + 256] = np.nanmin(np.where(ok, t, np.inf), 1)
ed = {}
for t in w[T[hair]]:
    for a, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        k = (min(a, b_), max(a, b_)); ed[k] = ed.get(k, 0) + 1
bv = np.unique([x for k, v in ed.items() if v == 1 for x in k]); Pw = np.zeros((n, 3)); Pw[w] = P
de = cKDTree(Pw[bv]).query(c)[0]
print('shell faces', len(shell), 'under the hair (< 4 cm)', int((dist < 0.04).sum()), '; and > 2.5 cm from its edges', int(((dist < 0.04) & (de > 0.025)).sum()))
np.save(HERE / 'work' / 'scalp_dist.npy', np.c_[shell, dist, de])
