#!/usr/bin/env python3
"""Survey of the installed LOD0: per primitive connected components (welded by position), UV-degenerate (one-texel) faces,
dominant joint per component. Read-only."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_annud.glb', 'Annud')
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
for name, d in D.items():
    P, T, U, J, W = d['P'], d['T'], d['UV'], d['J'], d['W']
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    fl = lab[FT[:, 0]]
    ua = np.abs((U[T[:, 1], 0] - U[T[:, 0], 0]) * (U[T[:, 2], 1] - U[T[:, 0], 1]) - (U[T[:, 2], 0] - U[T[:, 0], 0]) * (U[T[:, 1], 1] - U[T[:, 0], 1]))
    zero = ua < 1e-10
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    dj = acc.argmax(1)
    print(name, 'faces', len(T), 'verts', len(P), 'uv-zero faces', int(zero.sum()), 'components', len(np.unique(fl)))
    for c in sorted(np.unique(fl), key=lambda c: -(fl == c).sum()):
        m = fl == c; cen = P[T[m]].reshape(-1, 3)
        u, k = np.unique(dj[m], return_counts=True); top = sorted(zip(k, u), reverse=True)[:4]
        print(f'  comp {c:3d} faces {m.sum():5d} zeroUV {int(zero[m].sum()):5d} y {cen[:,1].min():.3f}..{cen[:,1].max():.3f} '
              f'x {cen[:,0].min():.3f}..{cen[:,0].max():.3f} z {cen[:,2].min():.3f}..{cen[:,2].max():.3f} '
              + ' '.join(f'{jn[j]}:{kk}' for kk, j in top))
