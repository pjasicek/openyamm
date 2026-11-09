import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm4.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)
for pr in bglbio.prims(doc, b, node['mesh']):
    P = pr['POSITION'].astype(float); T = pr['T']; J = pr['JOINTS_0'].astype(int); W = pr['WEIGHTS_0'].astype(float)
    _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel(); n = tp.max() + 1
    X = np.zeros((n, 3)); X[tp] = P
    # topo vertex normal from faces (area weighted), NOT the GLB normal (seam splits)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros((n, 3))
    for c in range(3):
        np.add.at(N, tp[T[:, c]], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    WD = np.zeros((n, int(J.max()) + 1))
    for c in range(4):
        np.add.at(WD, (tp, J[:, c]), 0)
    rep = np.zeros(n, int); rep[tp] = np.arange(len(P))
    for c in range(4):
        WD[np.arange(n), J[rep, c]] += W[rep, c]
    pairs = np.array(sorted(cKDTree(X).query_pairs(0.0042)))
    d = X[pairs[:, 1]] - X[pairs[:, 0]]; L = np.linalg.norm(d, axis=1)
    dn = (N[pairs[:, 0]] * N[pairs[:, 1]]).sum(1)
    al = np.abs((d * N[pairs[:, 0]]).sum(1)) / np.maximum(L, 1e-12)
    wd = np.abs(WD[pairs[:, 0]] - WD[pairs[:, 1]]).sum(1)
    ok = (dn < -0.3) & (al > 0.7)
    print(pr['material'], 'topo', n, 'pairs<4.2mm', len(pairs), 'opp+along', int(ok.sum()))
    h = np.histogram(L[ok] * 1000, bins=[0, 0.45, 0.55, 1, 2, 2.9, 2.98, 3.02, 3.5, 4.2])[0]; print('  offset hist mm [0,.45,.55,1,2,2.9,2.98,3.02,3.5,4.2]', h.tolist())
    print('  weight L1 of ok pairs pctl 50/90/99/max', np.percentile(wd[ok], [50, 90, 99, 100]).round(3))
    deg = np.bincount(pairs[ok].ravel(), minlength=n); print('  vertices with 1/2/3+ partners', int((deg == 1).sum()), int((deg == 2).sum()), int((deg >= 3).sum()))
