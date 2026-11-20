"""Connected components (welded) of a GLB: size, bbox. Args: glb"""
import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
import demon_common as C
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P, F, _ = C.load_mesh(sys.argv[1])
key = np.round(P / 1e-6).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
f = inv[F]; n = inv.max() + 1
e = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]
k, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)))
Q = np.zeros((n, 3)); Q[inv] = P
fl = lab[f[:, 0]]
# boundary edges per component
es = np.sort(e, 1); u, c = np.unique(es, axis=0, return_counts=True)
bnd = u[c == 1]
for i in np.argsort(-np.bincount(fl))[:40]:
    m = lab == i
    nb = int(m[bnd[:, 0]].sum())
    print(i, 'faces', int((fl == i).sum()), 'bbox', Q[m].min(0).round(3), Q[m].max(0).round(3), 'open edges', nb)
print('components', k)
