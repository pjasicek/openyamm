#!/usr/bin/env python3
"""Nocked-arrow LODs (make_bow.py: a straight 6-sided shaft of 24 rings with constant radius, u constant and v linear
along it, plus flat head and vane quads): dropping intermediate shaft rings leaves the shape and texture mapping
exactly as they were. LOD0 keeps every 2nd ring (and the last), LOD1 every 4th; head and vanes are kept; LOD2/LOD3
stay the source's (60 / 24 triangles). Usage: arrow_rings.py -> work/arrow_lod0.npz, work/arrow_lod1.npz"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/arrow.npz'); V, N, UV, F = d['verts'], d['normals'], d['uv'], d['faces']; n = len(V)
e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[F[:, 0]]; shaft_c = np.bincount(fl).argmax(); shaft = fl == shaft_c
sv = np.unique(F[shaft]); ys = np.unique(np.round(V[sv, 1], 5)); R = len(ys)
ring = {int(i): np.searchsorted(ys, np.round(V[i, 1], 5)) for i in sv}
order = []
for r in range(R):
    ids = np.array([i for i in sv if ring[i] == r]); ang = np.arctan2(V[ids, 2], V[ids, 0])
    ang = np.where(ang < -np.pi + 1e-3, np.pi, ang); order.append(ids[np.argsort(ang)])
# source winding: orient new quads like the source shaft faces (outward normal)
src_tri = F[np.flatnonzero(shaft)[0]]; p = V[src_tri]; outward = np.cross(p[1] - p[0], p[2] - p[0]) @ (p.mean(0) * [1, 0, 1]) > 0
for level, step in ((0, 2), (1, 4)):
    keep = sorted(set(range(0, R, step)) | {R - 1})
    tris = [list(t) for t in F[~shaft]]
    for a, b in zip(keep, keep[1:]):
        oa, ob = order[a], order[b]
        for k in range(6):
            j = (k + 1) % 6
            for t in ((oa[k], oa[j], ob[j]), (oa[k], ob[j], ob[k])):
                q = V[list(t)]; o = np.cross(q[1] - q[0], q[2] - q[0]) @ (q.mean(0) * [1, 0, 1]) > 0
                tris.append(list(t) if o == outward else [t[0], t[2], t[1]])
    tris = np.array(tris); used = np.unique(tris); remap = -np.ones(n, int); remap[used] = np.arange(len(used))
    np.savez(f'work/arrow_lod{level}.npz', verts=V[used], normals=N[used], uv=UV[used], faces=remap[tris], src=used)
    print(f'ARROW LOD{level}: shaft {len(keep)} of {R} rings, {len(tris)} tris')
