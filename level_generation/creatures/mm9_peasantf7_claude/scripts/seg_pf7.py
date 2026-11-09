"""PF7 (from seg_pf1.py): Meshy fused head (face and neck skin), bodice/chemise and skirt with the apron into one shell (comp 0). Split it by
multi-seed Dijkstra with a crease cost into head and dress, then the head below a slanted neck line goes to the dress and the dress below the
waist to the skirt. Writes the raw npz with comp ids: Meshy comps shifted by 10 (1 hair -> 11, ...), and HEAD, SKIRT appended (dress stays 0).
Args: <raw npz> <out npz> [CREASE]"""
import sys, os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
IN, OUT = sys.argv[1:3]; K = float(sys.argv[3]) if len(sys.argv) > 3 else 40.0
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
X0 = float(os.environ.get('X0', '0.008'))
def near(p):
    p = np.array(p, float); p[0] -= X0; d = np.linalg.norm(co[v0] - p, axis=1); return v0[np.argmin(d)]
SEEDS = {'head': [(0, -0.10, 1.60), (0, -0.06, 1.49), (0.05, -0.07, 1.56), (-0.05, -0.07, 1.56), (0, -0.09, 1.66)],
         'dress': [(0, -0.15, 1.30), (0, 0.10, 1.30), (0.2, 0, 1.36), (-0.2, 0, 1.36), (0, 0, 0.5)]}
lab = list(SEEDS); idx = []; owner = []
for k, l in enumerate(lab):
    for p in SEEDS[l]: idx.append(near(p)); owner.append(k)
dist = dijkstra(G, indices=idx, min_only=False)
best = np.argmin(dist, axis=0); L_ = np.array(owner)[best]
print({l: int((L_[v0] == k).sum()) for k, l in enumerate(lab)})
new = comp.copy() + 10 * (comp > 0)
nmax = new.max() + 1; HEAD, SKIRT = nmax, nmax + 1
NF, NB = float(os.environ.get('NECK_F', '1.44')), float(os.environ.get('NECK_B', '1.48'))
nz = NF + (NB - NF) * np.clip((co[:, 1] + 0.10) / 0.16, 0, 1)
L_[v0[(L_[v0] == 0) & (co[v0, 2] < nz[v0])]] = 1
new[v0[L_[v0] == 0]] = HEAD
WAIST = float(os.environ.get('WAIST_Z', '1.10'))
new[v0[(L_[v0] == 1) & (co[v0, 2] < WAIST)]] = SKIRT
u = np.unique(new)
print('ids', u.tolist(), 'head', HEAD, 'skirt', SKIRT, {int(c): int((new == c).sum()) for c in u})
np.savez(OUT, co=co, tri=tri, comp=new, ids=u)
