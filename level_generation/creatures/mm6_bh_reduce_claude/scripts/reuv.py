#!/usr/bin/env python3
"""Re-project the UVs of a reduced mesh from the source: every corner takes the source UV at its closest point on the
source surface, restricted to the UV island of the source face under the reduced face's centre, so one face never
spans a seam (the collapse can slide wedge UVs across islands; the eye's face showed dark slivers). Kept faces get
their own UVs back unchanged. Usage: reuv.py work/mesh_rNN.npz [...]  (rewrites wuv in place)"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from err_regions import pt_tri  # noqa: E402

s = np.load('work/mesh_in.npz'); sv, sf = s['verts'], s['faces']; suv = s['wuv'].reshape(-1, 3, 2)
# UV islands: faces joined across an edge whose two corners carry the same UVs on both sides
edges = {}
for i, f in enumerate(sf):
    for k in range(3):
        a, b = f[k], f[(k + 1) % 3]
        edges.setdefault((min(a, b), max(a, b)), []).append((i, suv[i, k] if a < b else suv[i, (k + 1) % 3],
                                                             suv[i, (k + 1) % 3] if a < b else suv[i, k]))
rows, cols = [], []
for l in edges.values():
    if len(l) == 2 and np.allclose(l[0][1], l[1][1], atol=1e-6) and np.allclose(l[0][2], l[1][2], atol=1e-6):
        rows.append(l[0][0]); cols.append(l[1][0])
n_isl, isl = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(sf),) * 2), directed=False)
tri = sv[sf]; cen = tri.mean(1); tree = cKDTree(cen)
by_isl = {}
for i, k in enumerate(isl):
    by_isl.setdefault(k, []).append(i)
trees = {}


def closest(p, cand):
    t = tri[cand]; d = pt_tri(p[None], t[:, 0], t[:, 1], t[:, 2]); j = int(np.argmin(d)); return cand[j], d[j]


def bary(p, t):
    v0, v1, v2 = t[1] - t[0], t[2] - t[0], p - t[0]
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01; b1 = (d11 * d20 - d01 * d21) / den; b2 = (d00 * d21 - d01 * d20) / den
    b = np.clip(np.array([1 - b1 - b2, b1, b2]), 0, None); return b / b.sum()


def island_closest(p, k):
    ids = by_isl[k]
    if k not in trees:
        trees[k] = cKDTree(cen[ids])
    _, j = trees[k].query(p, min(12, len(ids)))
    return closest(p, np.array(ids)[np.atleast_1d(j)])[0]


print('ISLANDS', n_isl)
for path in sys.argv[1:]:
    d = dict(np.load(path)); v, f = d['verts'], d['faces']; w = d['wuv'].reshape(-1, 3, 2).copy(); moved = 0
    for i, face in enumerate(f):
        c = v[face].mean(0); _, near = tree.query(c, 12); src, _ = closest(c, near); k = isl[src]
        for m in range(3):
            q = island_closest(v[face[m]], k)
            uv = bary(v[face[m]], tri[q]) @ suv[q]
            moved += np.abs(uv - w[i, m]).max() > 1e-4; w[i, m] = uv
    d['wuv'] = w.reshape(-1, 2); np.savez(path, **d); print('REUV', path, len(f), 'faces', moved, 'corners changed')
