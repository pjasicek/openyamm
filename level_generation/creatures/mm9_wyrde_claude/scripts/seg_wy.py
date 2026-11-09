"""Wyrde: Meshy fused head, hair, hood, cowl, mantle and gown into one shell (comp 0). Split it into labelled parts by multi-seed
Dijkstra with a crease cost (an edge across a sharp fold costs more), as PF1's seg_pf1.py. Seeds in scripts/seg_seeds.json
({label: [[x, y, z], ...]}, our frame over the soles, before the X0 shift). Other comps keep their ids + 10*(id>0).
Writes the raw npz with comp = 0 for the first label's ... no: comp = 100 + label index for comp-0 vertices.
Args: <raw npz> <out npz> [CREASE]"""
import sys, json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
IN, OUT = sys.argv[1:3]; K = float(sys.argv[3]) if len(sys.argv) > 3 else 40.0
SEEDS = json.load(open(__file__.rsplit('/', 1)[0] + '/seg_seeds.json'))
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']
t0 = tri[comp[tri[:, 0]] == 0]
fn = np.cross(co[t0[:, 1]] - co[t0[:, 0]], co[t0[:, 2]] - co[t0[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
E = np.vstack([t0[:, [0, 1]], t0[:, [1, 2]], t0[:, [2, 0]]]); F = np.tile(np.arange(len(t0)), 3)
key = np.sort(E, axis=1); order = np.lexsort((key[:, 1], key[:, 0])); key, F = key[order], F[order]
same = np.all(key[1:] == key[:-1], axis=1)
crease = {}
for i in np.where(same)[0]:
    crease[tuple(key[i])] = 1 - float(fn[F[i]] @ fn[F[i + 1]])
ek = np.unique(key, axis=0)
cr = np.array([crease.get(tuple(k), 1.0) for k in ek])
L = np.linalg.norm(co[ek[:, 0]] - co[ek[:, 1]], axis=1)
w = L * (1 + K * np.clip(cr, 0, 2))
n = len(co)
G = coo_matrix((np.r_[w, w], (np.r_[ek[:, 0], ek[:, 1]], np.r_[ek[:, 1], ek[:, 0]])), shape=(n, n)).tocsr()
v0 = np.unique(t0)
def near(p):
    d = np.linalg.norm(co[v0] - p, axis=1); return v0[np.argmin(d)]
lab = list(SEEDS); idx = []; owner = []
for k, l in enumerate(lab):
    for p in SEEDS[l]:
        for sx in ((1, -1) if abs(p[0]) > 1e-6 else (1,)):
            idx.append(near(np.array([p[0] * sx, p[1], p[2]]))); owner.append(k)
dist = dijkstra(G, indices=idx, min_only=False)
best = np.argmin(dist, axis=0); L_ = np.array(owner)[best]
new = comp.copy() + 10 * (comp > 0)
new[v0] = 100 + L_[v0]
print('SEG', {l: int((L_[v0] == k).sum()) for k, l in enumerate(lab)})
np.savez(OUT, co=co, tri=tri, comp=new, labels=np.array(lab))
