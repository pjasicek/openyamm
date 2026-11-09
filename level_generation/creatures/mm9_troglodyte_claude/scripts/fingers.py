"""Finger chains on the fitted body, left hand (x>0), by geodesic merge levels from the wrist. MM9's hand: three long fingers, chains Finger1 (inner), Finger2, Finger3 (outer), no thumb.
Args: <npz> Writes work/fingers.json, work/finger_labels.npy (0 none, 1..3 either hand)."""
import sys, json, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
from scipy.spatial import cKDTree
D = np.load(sys.argv[1]); co, tri = D['co'].astype(float), D['tri']
F = json.load(open('work/fit.json'))['tgt']; wr, hd = np.array(F['wr']), np.array(F['hd']); el = np.array(F['el'])
axis = (hd - wr) / np.linalg.norm(hd - wr)
hand = (((co - wr) @ axis) > -0.002) & (co[:, 0] > .25) & (np.linalg.norm(co - wr, axis=1) < .5)
hv = np.where(hand)[0]; rem = -np.ones(len(co), int); rem[hv] = np.arange(len(hv))
tt = tri[hand[tri].all(1)]
e = np.vstack([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]); w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[rem[e[:, 0]], rem[e[:, 1]]], np.r_[rem[e[:, 1]], rem[e[:, 0]]])), shape=(len(hv), len(hv))).tocsr()
seeds = np.where(np.abs((co[hv] - wr) @ axis) < 0.01)[0]
dd = dijkstra(G, indices=seeds, min_only=True)
print('hand verts', len(hv), 'seeds', len(seeds), 'max geodesic', np.nanmax(dd[np.isfinite(dd)]))
# finger cut level: sweep the level upward, count the components above it
order = np.argsort(-dd)
adj = [[] for _ in hv]
for a, b in zip(rem[e[:, 0]], rem[e[:, 1]]): adj[a].append(b); adj[b].append(a)
best = None
for lev in np.arange(.02, .25, .004):
    m = np.isfinite(dd) & (dd > lev); idx = np.where(m)[0]; re = -np.ones(len(hv), int); re[idx] = np.arange(len(idx))
    r = [re[i] for i in idx for j in adj[i] if m[j]]; c = [re[j] for i in idx for j in adj[i] if m[j]]
    n, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(len(idx), len(idx))), directed=False)
    sizes = np.bincount(lab); big = np.where(sizes > 20)[0]
    print('level', round(lev, 3), 'parts', len(big))
    if len(big) == 3 and best is None: best = (lev, idx, lab, big)
    if len(big) == 3: break
lev, idx, lab, big = best
info = []
for b in big:
    vs = idx[lab == b]; dv = dd[vs]; q = co[hv[vs]]
    tip = q[dv.argmax()]; base = q[dv < dv.min() + .006].mean(0); info.append(dict(vs=hv[vs], dv=dv, tip=tip, base=base))
info.sort(key=lambda f: f['base'][0])       # inner to outer
labels = np.zeros(len(co), int); out = {}
for k, f in enumerate(info, 1):
    vs, dv = f['vs'], f['dv']; a, b = dv.min(), dv.max(); L = b - a; labels[vs] = k
    def ring(t):
        m = np.abs(dv - (a + L * t)) < max(.004, L * .05); return co[vs[m]].mean(0)
    p1, p2, p3 = ring(.03), ring(.34), ring(.62)
    dirn = (p2 - p1) / np.linalg.norm(p2 - p1); p0 = p1 - dirn * .012
    out[f'Finger{k}'] = [p0.tolist(), p2.tolist(), p3.tolist(), f['tip'].tolist()]
    print(f'Finger{k}', 'len', round(float(L), 3), 'verts', len(vs), np.round(p0, 3).tolist(), np.round(f['tip'], 3).tolist())
d, m = cKDTree(co * [-1, 1, 1]).query(co); print('mirror residual', d.max())
labels = np.maximum(labels, labels[m])
np.save('work/finger_labels.npy', labels)
json.dump(out, open('work/fingers.json', 'w'), indent=0)
