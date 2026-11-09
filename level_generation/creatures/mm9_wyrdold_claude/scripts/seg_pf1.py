"""PF1: Meshy fused head, hood, bodice and skirt into one shell (comp 0). Split it into labelled parts by multi-seed Dijkstra with a crease
cost (an edge across a sharp fold costs more), then the skirt below the waist line. Writes the raw npz with new comp ids:
0 dress, 1/2 arms (Meshy, replaced later), 3/4 legs, ... and appends: head, hood, skirt. Args: <raw npz> <out npz> [CREASE]"""
import sys, os, heapq
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
w = L * (1 + K * np.clip(cr, 0, 2) ** 1.0)
n = len(co)
G = coo_matrix((np.r_[w, w], (np.r_[ek[:, 0], ek[:, 1]], np.r_[ek[:, 1], ek[:, 0]])), shape=(n, n)).tocsr()
v0 = np.unique(t0)
def near(p):
    d = np.linalg.norm(co[v0] - p, axis=1); return v0[np.argmin(d)]
SEEDS = {'head': [(0, -0.13, 1.60), (0, -0.09, 1.50), (0.05, -0.08, 1.48), (-0.05, -0.08, 1.48), (0, -0.10, 1.66)],
         'hood': [(0, 0.0, 1.80), (0, 0.16, 1.62), (0.10, 0.05, 1.55), (-0.10, 0.05, 1.55), (0.11, -0.05, 1.70), (-0.11, -0.05, 1.70), (0, -0.10, 1.77), (0.05, -0.10, 1.74), (-0.05, -0.10, 1.74)],
         'dress': [(0, -0.15, 1.30), (0, 0.12, 1.30), (0.2, 0, 1.38), (-0.2, 0, 1.38), (0, 0, 0.5)]}
lab = list(SEEDS); idx = []; owner = []
for k, l in enumerate(lab):
    for p in SEEDS[l]: idx.append(near(np.array(p))); owner.append(k)
dist = dijkstra(G, indices=idx, min_only=False)
best = np.argmin(dist, axis=0); L_ = np.array(owner)[best]
print({l: int((L_[v0] == k).sum()) for k, l in enumerate(lab)})
WAIST = float(os.environ.get('WAIST_Z', '1.04'))
new = comp.copy() + 10 * (comp > 0)       # free ids
nmax = new.max() + 1
HEAD, HOOD, SKIRT = nmax, nmax + 1, nmax + 2
# the head below a slanted neck line (front 1.44, back 1.48 over the soles) goes to the dress: the blouse collar is paint, not geometry
NF, NB = float(os.environ.get('NECK_F', '1.44')), float(os.environ.get('NECK_B', '1.48'))
nz = NF + (NB - NF) * np.clip((co[:, 1] + 0.10) / 0.16, 0, 1)
L_[v0[(L_[v0] == 0) & (co[v0, 2] < nz[v0])]] = 2
new[v0[L_[v0] == 0]] = HEAD; new[v0[L_[v0] == 1]] = HOOD
dz = v0[(L_[v0] == 2) & (co[v0, 2] < WAIST)]; new[dz] = SKIRT
u, inv = np.unique(new, return_inverse=True)
print('ids', u.tolist(), 'head', HEAD, 'hood', HOOD, 'skirt', SKIRT)
np.savez(OUT, co=co, tri=tri, comp=new, ids=u)
