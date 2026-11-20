#!/usr/bin/env python3
"""Dagrell component census: connected pieces (welded by position), their size, dominant bone, extent and thinness."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb
doc, b = gb.read(HERE / 'before' / 'mm9_dagrell.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Dagrell' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])[0]
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float)
nF = len(T)
_, wv = np.unique(np.round(P, 6), axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
dom = fw.argmax(1)
print('faces', nF, 'verts', len(P), 'welded', nW, 'components', len(np.unique(fl)), 'size', np.ptp(P, 0).round(3))
rows = []
for c in np.unique(fl):
    f = np.where(fl == c)[0]; v = np.unique(T[f]); ext = np.sort(np.ptp(P[v], 0))
    bone = joints[np.bincount(dom[f]).argmax()]
    rows.append((len(f), bone, ext[2], ext[0] / max(ext[2], 1e-9)))
rows.sort(key=lambda r: -r[0])
for r in rows:
    print(f'{r[0]:5d} {r[1]:12s} len {r[2]*100:5.1f} cm thin {r[3]:.2f}')
# --- shares
head = np.isin(dom, [joints.index(n) for n in ('Xheadpiv', 'Xjawbase', 'Xjawpiv', 'Xnose', 'XneckB')])
cnt = np.bincount(fl); small = cnt[fl] <= 20
thin = np.zeros(nF, bool)
for c in np.unique(fl):
    f = fl == c; v = np.unique(T[f]); ext = np.sort(np.ptp(P[v], 0))
    if ext[0] / max(ext[2], 1e-9) < 0.3 and cnt[c] < 60: thin |= f
digit = np.array([joints[d].startswith(('Xfin', 'Xtoe', 'Xfmid')) for d in dom])
sole = P[T][:, :, 2].min(1) < P[:, 2].min() + 0.03
print('head-dominant', int(head.sum()), 'small<=20', int(small.sum()), 'thin pieces<60', int((thin & ~head).sum()),
      'digit-dominant', int(digit.sum()), 'sole(z)', int(sole.sum()))
keep = head | small | thin | digit | sole
print('protected share', round(keep.mean() * 100, 1), '%; free', int((~keep).sum()))
for bn in sorted(set(joints[d] for d in dom[~keep])):
    print('  free', bn, int(((dom == joints.index(bn)) & ~keep).sum()))
