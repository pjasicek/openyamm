#!/usr/bin/env python3
"""PeasantDM1 protected-share survey of the installed LOD0: welded components per primitive with face counts, dominant joints,
bbox; zero-UV (one-texel) faces; hands (Hand/finger-dominated components). Read-only."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantdm1.glb', 'PeasantDM1')
jn = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
for name, d in D.items():
    P, T, U = d['P'], d['T'], d['UV']
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
    UT = U[T]; area = np.abs((UT[:, 1, 0] - UT[:, 0, 0]) * (UT[:, 2, 1] - UT[:, 0, 1]) - (UT[:, 2, 0] - UT[:, 0, 0]) * (UT[:, 1, 1] - UT[:, 0, 1])) / 2
    zero = area < 1e-9
    dj = np.array([jn[d['J'][v][d['W'][v].argmax()]] for v in range(len(P))])
    print(name, 'faces', len(T), 'verts', len(P), 'components', len(cnt), 'zero-UV faces', int(zero.sum()))
    for c in np.argsort(-cnt):
        m = fl == c; C = P[T[m]].reshape(-1, 3)
        js, jc = np.unique(dj[T[m].ravel()], return_counts=True)
        top = ', '.join(f'{a}:{b}' for a, b in sorted(zip(js, jc), key=lambda x: -x[1])[:3])
        print(f'  comp {c:3d} faces {cnt[c]:5d} zeroUV {int(zero[m].sum()):4d} x {C[:,0].min():+.3f}..{C[:,0].max():+.3f} '
              f'y {C[:,1].min():.3f}..{C[:,1].max():.3f} z {C[:,2].min():+.3f}..{C[:,2].max():+.3f}  {top}')
