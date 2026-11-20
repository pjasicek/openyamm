"""Topological vertex ids by position within TOL (default 1e-5 m), union-find over KD-tree pairs: glTF splits vertices at
UV/normal seams and np.round on positions splits pairs that straddle a rounding boundary."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def weld_ids(P, tol=1e-5):
    pairs = cKDTree(P).query_pairs(tol, output_type='ndarray')
    n = len(P)
    if len(pairs) == 0:
        return np.arange(n)
    _, lab = connected_components(coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n)), directed=False)
    return lab
