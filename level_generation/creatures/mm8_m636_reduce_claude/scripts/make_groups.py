#!/usr/bin/env python3
"""Regions of the template fish (work/mesh_in.npz faces) by connected piece: the two eyes (pieces under 2 cm) are
kept exactly (work/keep.npy); the pectoral fins (FinL/FinR-weighted pieces) are groups 1 and 5
(decimated each on its own: a shared budget left one fin a 4-triangle inside-out shell in the LODs), the two gill covers (the
other small Body pieces) group 2 (work/groups.npy); the body with spines and tail is label 0. Eyes are also group 4,
which the LOD steps decimate. THIN_GROUP (off) would make the body's thin parts (dorsal spines, tail, pelvic and anal
fins: under 1.5 cm thick along the inward face normal) group 3.
Usage: make_groups.py [input npz name] -> work/keep.npy, work/groups.npy (or <name>_keep/_groups.npy)"""
import sys
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.csgraph as cg
W = Path(__file__).resolve().parents[1] / 'work'
name = sys.argv[1] if len(sys.argv) > 1 else 'mesh_in'
m = np.load(W / f'{name}.npz'); f = np.load(W / 'fish.npz')
V, F = m['verts'], m['faces']
e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
nc, lab = cg.connected_components(sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V),) * 2), directed=False)
# region of each piece from the source fish: nearest source vertex's dominant joint (1 Body, 2 FinL, 3 FinR, 4-5 tail)
from scipy.spatial import cKDTree  # noqa: E402
dom = f['J'][np.arange(len(f['J'])), f['W'].argmax(1)]
near = cKDTree(f['P']).query(V)[1]; vdom = dom[near]
THIN = 0.015
THIN_GROUP = False   # tried: decimating the thin parts on their own pinned the body to their cut edges (worse)


def thickness(V, F):
    """distance from each face centre to the opposite surface along the inward normal"""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]; fn = np.cross(b - a, c - a); fn /= np.linalg.norm(fn, axis=1, keepdims=True)
    o, d = (a + b + c) / 3 - fn * 1e-5, -fn; e1, e2 = b - a, c - a
    p = np.cross(d[:, None], e2[None]); det = (e1[None] * p).sum(-1); inv = 1 / np.where(np.abs(det) < 1e-12, 1e-12, det)
    s = o[:, None] - a[None]; u = (s * p).sum(-1) * inv; q = np.cross(s, e1[None]); v = (d[:, None] * q).sum(-1) * inv
    t = (e2[None] * q).sum(-1) * inv
    return np.where((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5), t, np.inf).min(1)


keep = np.zeros(len(F), bool); groups = np.zeros(len(F), int)
for c in range(nc):
    fc = lab[F[:, 0]] == c; vs = np.unique(F[fc]); size = np.ptp(V[vs], 0).max(); jd = np.bincount(vdom[vs], minlength=6)
    if size < 0.02:
        keep[fc] = True; groups[fc] = 4; kind = 'eye (kept at LOD0; group 4 for the LODs)'
    elif jd[2] + jd[3] > len(vs) / 2:
        g = 1 if jd[2] >= jd[3] else 5
        groups[fc] = g; kind = f'pectoral fin (group {g})'
    elif fc.sum() < 100:
        groups[fc] = 2; kind = 'gill cover (group 2)'
    else:
        th = thickness(V, F); kind = f'body ({int((fc & (th < THIN)).sum())} thin faces; label 0)'
        if THIN_GROUP:
            groups[fc & (th < THIN)] = 3
    print(f'piece {c}: {int(fc.sum())} faces, {size * 100:.1f} cm, {kind}')
pre = '' if name == 'mesh_in' else f'{name}_'
np.save(W / f'{pre}keep.npy', keep); np.save(W / f'{pre}groups.npy', groups)
