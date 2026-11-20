"""Which parts the bad faces of a clip time are on. Args: glb uv_npz clip t"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); doc = m.glb.json; D = np.load(sys.argv[2]); co, comp = D['co'], D['comp']; pn = [str(x) for x in D['names']]
g_ = np.c_[co[:, 0], co[:, 2], -co[:, 1]]
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
PR = m.primitives; rest = np.vstack([np.asarray(p['positions'], float) for p in PR]); OFF = np.cumsum([0] + [len(p['positions']) for p in PR])
SK = lambda w: np.vstack([x[0] for x in m.skinned_positions(w)])
T = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
_, nr = cKDTree(g_).query(rest); part = comp[nr][T[:, 0]]
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); ok = a0 > 1e-9
for t in [float(x) for x in sys.argv[4:]]:
    w = m.world(m.sample(sys.argv[3], t)); P = SK(w); pal = w[m.joints] @ m.inverse_binds
    nr_ = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0); n, a = tri(P)
    d = (n * nr_).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr_, axis=1), 1e-12)
    bad = ok & ((a < 0.2 * a0) | (d < 0))
    print(t, int(bad.sum()), {pn[k]: int((bad & (part == k)).sum()) for k in np.unique(part[bad])})
