"""Geodesic helpers on work/pieces.npz (system python: numpy, scipy)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
import os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_d = np.load(os.path.join(HERE, 'work', 'pieces.npz'))
co, lab, faces = _d['co'], _d['label'], _d['faces']
e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.concatenate([w, w]), (np.concatenate([e[:, 0], e[:, 1]]), np.concatenate([e[:, 1], e[:, 0]]))),
               shape=(len(co), len(co))).tocsr()


def gdist(seeds):
    d = dijkstra(G, indices=np.atleast_1d(seeds), min_only=True)
    return d


def piece(i):
    return np.where(lab == i)[0]


def junction(a, b):
    """closest vertex pair between pieces a and b: (index in a, index in b, distance)"""
    A, B = piece(a), piece(b)
    t = cKDTree(co[B]); dd, j = t.query(co[A]); k = int(dd.argmin())
    return A[k], B[j[k]], float(dd[k])


def centreline(idx, dist, nb=40, upto=None):
    """per geodesic-distance bin centroid of the vertices idx"""
    dd = dist[idx]
    top = dd.max() if upto is None else upto
    edges = np.linspace(0, top, nb + 1)
    pts = []
    for a, b in zip(edges, edges[1:]):
        s = idx[(dd >= a) & (dd < b)]
        if len(s):
            pts.append(((a + b) / 2, co[s].mean(0), np.linalg.norm(co[s] - co[s].mean(0), axis=1).mean()))
    return pts
