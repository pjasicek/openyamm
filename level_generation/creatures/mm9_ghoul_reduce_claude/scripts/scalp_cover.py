#!/usr/bin/env python3
"""Face-set skin (part 10) hidden under the hair mass: a vertex is covered when rays along its rest normal and along four
directions tilted 35 deg from it all hit a hair triangle within MAXD m. A face counts as scalp when all three corners are covered
and it stays more than RINGS edge rings from any uncovered face-skin face (margin at the hairline). Writes work/scalp.npy
(per GhoulHead_A face). Usage: scalp_cover.py [MAXD] [RINGS]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
MAXD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.06; RINGS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
doc, b = gb.read(HERE / 'before' / 'mm9_ghoul.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Ghoul' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); h = pr[1]
lab = np.load(HERE / 'work' / 'labels.npz')['head']
P = h['POSITION'].astype(float); T = h['T']; N = h['NORMAL'].astype(float)
hair = T[lab == 11]; A, B, C = P[hair[:, 0]], P[hair[:, 1]], P[hair[:, 2]]


def hits(o, d):
    e1, e2 = B - A, C - A
    pv = np.cross(d[:, None], e2[None]); det = (e1[None] * pv).sum(-1)
    inv = 1 / np.where(np.abs(det) < 1e-12, np.nan, det)
    tv = o[:, None] - A[None]; u = (tv * pv).sum(-1) * inv
    qv = np.cross(tv, e1[None]); v = (d[:, None] * qv).sum(-1) * inv; t = (e2[None] * qv).sum(-1) * inv
    ok = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < MAXD)
    return np.nan_to_num(ok).any(1)


fs = np.flatnonzero(lab == 10); vs = np.unique(T[fs])
cov = np.ones(len(P), bool); cov[:] = False
n = N[vs] / np.linalg.norm(N[vs], axis=1, keepdims=True)
a = np.cross(n, [0, 1, 0]); a[np.linalg.norm(a, axis=1) < 1e-3] = [1, 0, 0]; a /= np.linalg.norm(a, axis=1, keepdims=True); bb = np.cross(n, a)
c = np.ones(len(vs), bool)
for d in (n, n * .82 + a * .57, n * .82 - a * .57, n * .82 + bb * .57, n * .82 - bb * .57):
    d = d / np.linalg.norm(d, axis=1, keepdims=True)
    c &= np.concatenate([hits(P[vs[i:i + 400]] + d[i:i + 400] * 1e-4, d[i:i + 400]) for i in range(0, len(vs), 400)])
cov[vs] = c
key = np.round(P, 6); _, tp = np.unique(key, axis=0, return_inverse=True); tp = tp.ravel()
covt = np.zeros(tp.max() + 1, bool); covt[tp[vs[c]]] = True
fc = covt[tp[T[fs]]].all(1)
bad = set(tp[T[fs[~fc]]].ravel().tolist())          # topological vertices of visible face skin
for _ in range(RINGS):
    grow = set(bad)
    for f in fs:
        tt = tp[T[f]]
        if any(x in bad for x in tt):
            grow.update(tt.tolist())
    bad = grow
scalp = np.zeros(len(T), bool)
for f in fs[fc]:
    if not any(x in bad for x in tp[T[f]]):
        scalp[f] = True
print('face skin', len(fs), 'covered faces', int(fc.sum()), 'scalp after', RINGS, 'rings', int(scalp.sum()))
print('scalp y range', P[T[scalp]][..., 1].min().round(3), P[T[scalp]][..., 1].max().round(3), 'face skin y', P[T[fs]][..., 1].min().round(3), P[T[fs]][..., 1].max().round(3))
np.save(HERE / 'work' / 'scalp.npy', scalp)
