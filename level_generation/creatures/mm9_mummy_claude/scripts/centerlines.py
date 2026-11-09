"""Limb centre lines of the body from geodesic level sets. Args: <npz> <out npz>. Prints landmarks."""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
npz, out = sys.argv[1:3]
D = np.load(npz); co, tri = D['co'], D['tri']
n = len(co)
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
seed = int(np.argmin(np.linalg.norm(co - np.array([0, -0.05, 1.2]), axis=1)))
dist, pred = dijkstra(G, indices=seed, return_predecessors=True)
tips = {'handL': int(np.argmin(co[:, 0])), 'handR': int(np.argmax(co[:, 0])), 'head': int(np.argmax(co[:, 2]))}
low = np.where(co[:, 2] < 0.05)[0]
tips['footL'] = int(low[np.argmin(co[low, 1] + 3 * (co[low, 0] > 0))]); tips['footR'] = int(low[np.argmin(co[low, 1] + 3 * (co[low, 0] < 0))])
res = {}
for name, tip in tips.items():
    path = [tip]
    while path[-1] != seed: path.append(int(pred[path[-1]]))
    path = np.array(path)
    dmax = dist[tip]; bins = np.arange(0.02, dmax, 0.012)
    C = []
    for b in bins:
        m = np.where((dist > b - 0.012) & (dist < b + 0.012))[0]
        sub = G[m][:, m]
        nc, lab = connected_components(sub, directed=False)
        # the component holding the path
        pv = path[np.abs(dist[path] - b).argmin()]
        idx = np.where(m == pv)[0]
        if len(idx) == 0: continue
        q = co[m[lab == lab[idx[0]]]]
        c = q.mean(0); r = np.linalg.norm(q - c, axis=1)
        C.append((b, *c, r.mean(), len(q), nc))
    res[name] = np.array(C)
    print(name, 'tip', co[tip].round(3), 'dist', round(float(dmax), 3))
    for row in res[name][::6]: print('   ', row.round(3).tolist())
np.savez(out, **res)
