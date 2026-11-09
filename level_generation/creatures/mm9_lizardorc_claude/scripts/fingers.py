"""Finger chains on the fitted body, left hand (x>0), by geodesic merge levels from the wrist. Hand: three clawed fingers and a thumb. Chains: Finger3 outer ... Finger1 inner by base position, Finger0 the thumb. Args: <npz with co, tri> Writes work/fingers.json, work/finger_labels.npy (0 none, 1..3 fingers, 4 thumb, either hand)."""
import sys, json, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
from scipy.spatial import cKDTree
D = np.load(sys.argv[1]); co, tri = D['co'].astype(float), D['tri']
F = json.load(open('work/fit.json'))['tgt']; wr = np.array(F['wr']); hd = np.array(F['hd'])
axis = (hd - wr) / np.linalg.norm(hd - wr)
hand = (((co - wr) @ axis) > -.012) & (co[:, 0] > .45) & (np.linalg.norm(co - wr, axis=1) < .42)
hv = np.where(hand)[0]; rem = -np.ones(len(co), int); rem[hv] = np.arange(len(hv))
tt = tri[hand[tri].all(1)]
print('hand verts', len(hv), 'tris', len(tt))
e = np.vstack([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]); w = np.linalg.norm(co[e[:, 0]] - co[e[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[rem[e[:, 0]], rem[e[:, 1]]], np.r_[rem[e[:, 1]], rem[e[:, 0]]])), shape=(len(hv), len(hv))).tocsr()
seeds = np.where(np.abs((co[hv] - wr) @ axis) < .018)[0]
dd = dijkstra(G, indices=seeds, min_only=True)
print('seeds', len(seeds), 'max geodesic', np.nanmax(dd[np.isfinite(dd)]))
adj = [[] for _ in hv]
for a, b in zip(rem[e[:, 0]], rem[e[:, 1]]): adj[a].append(b); adj[b].append(a)
def parts(lev, excl=None):
    m = np.isfinite(dd) & (dd > lev)
    if excl is not None: m &= ~excl
    idx = np.where(m)[0]; re = -np.ones(len(hv), int); re[idx] = np.arange(len(idx))
    r = [re[i] for i in idx for j in adj[i] if m[j]]; c = [re[j] for i in idx for j in adj[i] if m[j]]
    n, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(len(idx), len(idx))), directed=False)
    sizes = np.bincount(lab); return idx, lab, np.where(sizes >= 6)[0], sizes
lev2 = None
for lev in np.arange(.02, .34, .004):
    idx, lab, big, sizes = parts(lev)
    if len(big) >= 2:
        small = big[np.argmin(sizes[big])]; thumbv = idx[lab == small]; lev2 = lev; print('thumb at', round(lev, 3), sizes[big].tolist()); break
ex = np.zeros(len(hv), bool); ex[thumbv] = True
def inf(vs):
    dv = dd[vs]; q = co[hv[vs]]; return dict(vs=hv[vs], dv=dv, tip=q[dv.argmax()], base=q[dv < dv.min() + .008].mean(0))
thumb = inf(thumbv)
for lev in np.arange(lev2, .34, .004):
    idx, lab, big, sizes = parts(lev, ex)
    if len(big) == 3: print('fingers at', round(lev, 3), sizes[big].tolist()); break
info = [inf(idx[lab == b]) for b in big]
info.sort(key=lambda f: f['base'][2])       # z: back to front across the palm
labels = np.zeros(len(co), int); out = {}
def chain(f):
    vs, dv = f['vs'], f['dv']; a, b = dv.min(), dv.max(); L = b - a
    def ring(t):
        m = np.abs(dv - (a + L * t)) < max(.006, L * .07); return co[vs[m]].mean(0)
    p1, p2, p3 = ring(.04), ring(.36), ring(.66)
    return [p1.tolist(), p2.tolist(), p3.tolist(), f['tip'].tolist()], L, vs
for k, f in enumerate(info, 1):
    ch, L, vs = chain(f); labels[vs] = k; out[f'Finger{k}'] = ch
    print(f'Finger{k}', 'len', round(float(L), 3), 'verts', len(vs), np.round(ch[0], 3).tolist(), np.round(ch[3], 3).tolist())
ch, L, vs = chain(thumb); labels[vs] = 4; out['Finger0'] = ch; print('Thumb', round(float(L), 3), len(vs), np.round(ch[0], 3).tolist(), np.round(ch[3], 3).tolist())
d, m = cKDTree(co * [-1, 1, 1]).query(co); print('mirror residual', d.max())
labels = np.maximum(labels, labels[m])
np.save('work/finger_labels.npy', labels)
json.dump(out, open('work/fingers.json', 'w'), indent=0)
