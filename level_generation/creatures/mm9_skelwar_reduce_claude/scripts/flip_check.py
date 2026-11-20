#!/usr/bin/env python3
"""Faces of a candidate's LOD0 (body and head primitives, outer faces only: UV area > 0) whose geometric normal points away
(> 90 deg) from the installed surface's nearest outer face, in the rest pose. Usage: flip_check.py <installed.glb> <candidate.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
A, B = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
def outer(m, pi):
    p = m.primitives[pi]; P, T = p['positions'], p['triangles']
    uv = np.asarray(m.glb.accessor(m.glb.json['meshes'][0]['primitives'][pi]['attributes']['TEXCOORD_0']))
    a = np.abs(np.cross(np.c_[uv[T[:, 1]] - uv[T[:, 0]], np.zeros(len(T))], np.c_[uv[T[:, 2]] - uv[T[:, 0]], np.zeros(len(T))])[:, 2])
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-20
    return P, T, n, a > 1e-9
for pi in (0, 1):
    Pa, Ta, na, oa = outer(A, pi); Pb, Tb, nb, ob = outer(B, pi)
    Ta, na = Ta[oa], na[oa]; sel = np.flatnonzero(ob)
    cb = Pb[Tb[sel]].mean(1); _, nn = cKDTree(Pa[Ta].mean(1)).query(cb, k=32)
    pts = np.repeat(cb, 32, 0); f = nn.ravel()
    q, _ = closest_on_triangles(pts, Pa[Ta[f, 0]], Pa[Ta[f, 1]], Pa[Ta[f, 2]])
    d = np.linalg.norm(q - pts, axis=1).reshape(-1, 32); best = nn[np.arange(len(sel)), d.argmin(1)]
    dot = np.einsum('ij,ij->i', nb[sel], na[best])
    bad = sel[dot < 0]
    print('prim', pi, 'outer faces', len(sel), 'turned over (> 90 deg from the installed nearest face):', len(bad))
    for k in bad: print('   face', k, np.round(Pb[Tb[k]].mean(0), 3).tolist(), 'dot', round(float(dot[np.searchsorted(sel, k)]), 2))
