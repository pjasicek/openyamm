"""Reduced half -> mirrored symmetric body0, spine keel faired. Args: <half npz> <out npz>"""
import sys, numpy as np
from scipy.sparse import coo_matrix
D = np.load(sys.argv[1]); P, T = D['co'].astype(float), D['tri']
on = np.where(np.abs(P[:, 0]) < 2e-5)[0]; P[on, 0] = 0
n = len(P); M_ = P * [-1, 1, 1]; rem = np.arange(n, 2 * n); rem[on] = on
T2 = rem[T][:, [0, 2, 1]]
co = np.vstack([P, M_]); tri = np.vstack([T, T2])
used, inv = np.unique(tri, return_inverse=True); co = co[used]; tri = inv.reshape(-1, 3)
def boundary(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True); return u[c == 1]
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]); N = len(co)
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(N, N)).tocsr(); A.data[:] = 1
deg = np.asarray(A.sum(1)).ravel()
kee = (np.abs(co[:, 0]) < .07) & (co[:, 2] < .25)
w = np.clip(1 - np.abs(co[:, 0]) / .07, 0, 1)[:, None] * kee[:, None]
for it in range(40):
    co += (.5 if it % 2 == 0 else -.46) * w * ((A @ co) / deg[:, None] - co)
print('body0', len(co), len(tri), 'open', len(boundary(tri)), 'bbox', co.min(0).round(3), co.max(0).round(3))
np.savez(sys.argv[2], co=co, tri=tri)
