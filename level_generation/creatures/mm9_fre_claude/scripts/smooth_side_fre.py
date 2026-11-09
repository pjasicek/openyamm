#!/usr/bin/env python3
"""Fre pass 5 (orchestrator on r62: hard-edged light/dark panels at the temples and face sides; the unlit base colour is smooth there, so
it is shape): with the old bob gone, F1's pressed ear plates, the old hood's teeth and the face shell's outline beside them are bare, and
they hold folded and creased faces (dihedral angles up to 180 deg at the temples and in front of the ears). Their positions are relaxed:
Taubin smoothing (lambda 0.5 / mu -0.53, PASSES) over the welded face shell + old hood, weighted by a smooth region weight (to the side of
the face |x| 4.5-5.8 cm, behind the brows y > -0.085, between the jaw line and the crown 0.60-0.78 m), so the untouched front face (eyes,
nose, mouth, cheeks) does not move and nothing has a boundary. Rows on the neckline with the bodice are fixed. Positions only; run
before under_hair2_fre.py's clearance in geo_chain_fre.sh. Args: <uv npz in> <out npz>   (project folder)"""
import sys, os
import numpy as np
U = dict(np.load(sys.argv[1])); names = [str(x) for x in U['names']]
co, tri, comp = U['co'].copy(), U['tri'], U['comp']
KH, KS, KD = names.index('head'), names.index('scarf'), names.index('dress')
PASSES = int(os.environ.get('SIDE_PASSES', '0'))      # r69: relaxing did not remove the temple wedge (it was the hair rim's own normals) and pushed shards out at the ear: off
def ss(x, a, b):
    k = np.clip((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k)
key = np.round(co, 5); uq, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); n = len(uq)
P = uq.copy()
tm = np.isin(comp[tri], [KH, KS]).all(1); T = inv[tri[tm]]
e = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
e = e[np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1) < 0.015]      # long slivers of the hidden skull do not pull
onp = np.zeros(n, bool); onp[inv[np.isin(comp, [KH, KS])]] = True
dres = np.zeros(n, bool); dres[inv[comp == KD]] = True
w = ss(np.abs(P[:, 0]), 0.045, 0.058) * ss(P[:, 1], -0.085, -0.07) * ss(P[:, 2], 0.60, 0.62) * (1 - ss(P[:, 2], 0.76, 0.78)) * onp * ~dres
deg = np.bincount(e.ravel(), minlength=n).astype(float)
def lap(X):
    acc = np.zeros_like(X); np.add.at(acc, e[:, 0], X[e[:, 1]]); np.add.at(acc, e[:, 1], X[e[:, 0]])
    return np.where(deg[:, None] > 0, acc / np.maximum(deg, 1)[:, None] - X, 0)
X = P.copy()
for _ in range(PASSES):
    X = X + 0.5 * w[:, None] * lap(X)
    X = X - 0.53 * w[:, None] * lap(X)
MAXD = float(os.environ.get('SIDE_MAX', '0.006')); D_ = X - P; dn = np.linalg.norm(D_, axis=1, keepdims=True)
X = P + D_ * np.minimum(1, MAXD / np.maximum(dn, 1e-12))      # at most SIDE_MAX per vertex
d = np.linalg.norm(X - P, axis=1)
co = X[inv]; keep = ~np.isin(comp, [KH, KS]); co[keep] = U['co'][keep]
U['co'] = co; np.savez(sys.argv[2], **U)
print('SIDESMOOTH vertices weighted', int((w > 0.01).sum()), 'moved max mm', round(float(d.max()) * 1000, 2), 'p95 mm',
      round(float(np.percentile(d[w > 0.01], 95)) * 1000, 2) if (w > 0.01).any() else 0)
