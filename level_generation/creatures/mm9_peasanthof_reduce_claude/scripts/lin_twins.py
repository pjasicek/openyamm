#!/usr/bin/env python3
"""Lining twins of the half-orc women's body primitive (rim_lining.py of the creature: each band face duplicated `offset` behind
itself along the vertex normal, reversed, with the band vertices' weights, all corners on one dark texel; inner-layer bands moved
only 0.5 mm and keeping their own UVs; a rim strip of two faces per loop edge joins the outer rim to its twin).
find_twins(P, UV, J, W, T): a face L is the twin of an outer face O when L's corners are O's reversed (some rotation), each
corner within DMAX of O's corner, behind O (against O's normal), with equal joints and weights (tolerance WTOL); candidates are
L faces whose UV triangle is degenerate (one texel) or whose corner UVs equal O's (inner-layer twins). Each outer face takes at
most one twin, best (smallest max corner distance) first.
Returns role (0 plain, 1 outer with a twin, 2 twin), partner, and per face (outer) twin corner GLB vertices."""
import numpy as np
from scipy.spatial import cKDTree

DMAX = 0.012
WTOL = 0.02


def face_normals(P, T):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)


def find_twins(P, UV, J, W, T):
    ua = np.abs((UV[T[:, 1], 0] - UV[T[:, 0], 0]) * (UV[T[:, 2], 1] - UV[T[:, 0], 1])
                - (UV[T[:, 2], 0] - UV[T[:, 0], 0]) * (UV[T[:, 1], 1] - UV[T[:, 0], 1]))
    zero = ua < 1e-12
    n = face_normals(P, T); cen = P[T].mean(1)
    tree = cKDTree(cen)
    # dense joint-weight vectors per vertex for the weight comparison
    nj = int(J.max()) + 1
    WD = np.zeros((len(P), nj)); np.add.at(WD, (np.repeat(np.arange(len(P)), 4), J.reshape(-1)), W.reshape(-1))
    cands = []
    for f in range(len(T)):
        for o in tree.query_ball_point(cen[f], DMAX):
            if o == f or np.dot(n[o], n[f]) > -0.3:
                continue
            best = None
            for s in range(3):
                r = np.roll(T[o][::-1], s)               # O's corners reversed: r[k] pairs with T[f][k]
                d = P[T[f]] - P[r]
                dist = np.linalg.norm(d, axis=1)
                if dist.max() > DMAX or (d @ n[o]).max() > 1e-5:
                    continue
                if np.abs(WD[T[f]] - WD[r]).max() > WTOL:
                    continue
                if not zero[f] and np.abs(UV[T[f]] - UV[r]).max() > 1e-6:
                    continue
                if best is None or dist.max() < best[0]:
                    best = (dist.max(), r)
            if best is not None:
                cands.append((best[0], f, o, best[1]))
    cands.sort(key=lambda c: c[0])
    role = np.zeros(len(T), int); partner = -np.ones(len(T), int); twinv = -np.ones((len(T), 3), np.int64)
    for dmax, f, o, r in cands:
        if role[f] or role[o]:
            continue
        role[f] = 2; role[o] = 1; partner[f] = o; partner[o] = f
        # outer corner k -> twin vertex: T[f][j] pairs with r[j]
        for j in range(3):
            k = int(np.flatnonzero(T[o] == r[j])[0]); twinv[o, k] = T[f][j]
    return role, partner, twinv, zero
