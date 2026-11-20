"""Probe 2: lining (tiny-UV) body faces -> outer faces by nearest outer topo vertex; face-level check."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm4.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)
pr = bglbio.prims(doc, b, node['mesh'])[0]
g = np.load(HERE / 'work' / 'glb_parts.npz'); m = g['mat'] == 0
P = pr['POSITION'].astype(float); T = pr['T']; tiny = g['uvarea'][m] < 0.5; comp = g['comp'][m]
_, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel(); TF = tp[T]
X = np.zeros((tp.max() + 1, 3)); X[tp] = P
lv = np.unique(TF[tiny]); ov = np.unique(TF[~tiny])
print('topo lining', len(lv), 'outer', len(ov), 'shared', len(np.intersect1d(lv, ov)))
d, q = cKDTree(X[ov]).query(X[lv]); tw = -np.ones(len(X), int); tw[lv] = ov[q]
print('nearest outer mm p50/p90/p99/max', *(np.percentile(d, [50, 90, 99, 100]) * 1000).round(2))
u, c = np.unique(tw[lv], return_counts=True); print('outer verts hit more than once', int((c > 1).sum()))
fset = {tuple(sorted(t)): i for i, t in enumerate(TF) if not tiny[i]}
L = TF[tiny]; M = tw[L]
hit = np.array([tuple(sorted(t)) in fset for t in M]); print('lining faces', len(L), 'mapped to an outer face', int(hit.sum()))
# orientation: lining should be reversed relative to outer
n = lambda A: np.cross(X[A[:, 1]] - X[A[:, 0]], X[A[:, 2]] - X[A[:, 0]])
nl = n(L); nm = n(M); dots = (nl * nm).sum(1) / (np.linalg.norm(nl, axis=1) * np.linalg.norm(nm, axis=1) + 1e-20)
print('lining vs mapped-outer normal dot: <-0.5', int((dots < -0.5).sum()), '>0.5', int((dots > 0.5).sum()))
# outer faces that have a lining twin
lined_outer = set(tuple(sorted(t)) for t in M[hit])
print('outer faces with a twin', len(lined_outer), 'of', int((~tiny).sum()))
bad = np.flatnonzero(~hit); print('unmatched lining faces by comp', dict(zip(*np.unique(comp[tiny][bad], return_counts=True))))
print('unmatched centroids sample', X[L[bad]].mean(1)[:10].round(3))
