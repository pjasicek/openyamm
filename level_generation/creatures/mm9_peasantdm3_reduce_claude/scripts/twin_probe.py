#!/usr/bin/env python3
"""Probe: why hair-twin faces (head comp of 483 faces) do not pair in twins.py. Read-only."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm3.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM3' and 'mesh' in n)
pr = [p for p in bglbio.prims(doc, b, node['mesh']) if p['material'] == 'PeasantDM3Head_A'][0]
P = pr['POSITION'].astype(float); T = pr['T']; J = pr['JOINTS_0'].astype(int); W = pr['WEIGHTS_0'].astype(float)
N = pr['NORMAL'].astype(float); N /= np.linalg.norm(N, axis=1, keepdims=True); U = pr['TEXCOORD_0'].astype(float)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
comp = lab[FT[:, 0]]; cnt = np.bincount(comp)
tw = np.load(HERE / 'work' / 'twins.npz'); nb = len(tw['zero_PeasantDM3_A'])
lining = tw['lining'][nb:]; lined = tw['lined'][nb:]
tc = [c for c in np.unique(comp) if cnt[c] == 483][0]
tf = comp == tc
print('twin comp faces', tf.sum(), 'lining', (tf & lining).sum(), 'lined', (tf & lined).sum())
print('outer lined faces by comp', {int(c): int(((comp == c) & lined).sum()) for c in np.unique(comp)}, 'sizes', {int(c): int(cnt[c]) for c in np.unique(comp)})
tv = np.unique(T[tf & ~lining & ~lined].ravel())
ov = np.unique(T[(comp != tc)].ravel())
tr = cKDTree(P[ov]); d, i = tr.query(P[tv], k=3)
def wd(a, b_):
    x = np.zeros(80); y = np.zeros(80); np.add.at(x, J[a], W[a]); np.add.at(y, J[b_], W[b_]); return np.abs(x - y).sum()
ws = []; ns = []; us = []
for k, v in enumerate(tv):
    o = ov[i[k, 0]]; ws.append(wd(v, o)); ns.append(N[v] @ N[o]); us.append(np.abs(U[v] - U[o]).max())
ws = np.array(ws); ns = np.array(ns); us = np.array(us)
print('unpaired twin verts', len(tv), 'nearest dist mm p50/max', np.median(d[:, 0]) * 1000, d[:, 0].max() * 1000)
print('weight L1 p50/max', np.median(ws), ws.max(), 'frac >1e-3', (ws > 1e-3).mean())
print('normal dot p50 / frac > -0.3', np.median(ns), (ns > -0.3).mean(), 'uv diff p50', np.median(us))
pv = np.unique(T[tf & lining].ravel()); d2, i2 = tr.query(P[pv]); print('paired twin verts nearest mm p50', np.median(d2) * 1000)
