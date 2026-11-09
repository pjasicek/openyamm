"""Welded connected pieces per face (make_sets.py's pieces())."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from weld import weld_ids


def pieces(P, T):
    w = weld_ids(P); FT = w[T]; n = w.max() + 1
    r = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    return w, FT, lab[FT[:, 0]]
