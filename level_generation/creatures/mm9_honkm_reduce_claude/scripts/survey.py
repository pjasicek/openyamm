#!/usr/bin/env python3
"""Survey of the installed LOD0 (before/mm9_honkm.glb): per primitive, welded connected components with face count,
dominant bones, extents; reversed-duplicate (lining) candidates."""
import sys
from pathlib import Path
import numpy as np
from collections import Counter
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM')
skin = doc['skins'][nd['skin']]; names = [doc['nodes'][j]['name'] for j in skin['joints']]
for name, d in D.items():
    P, T, J, W = d['P'], d['T'], d['J'], d['W']
    w = weld_ids(P); TF = w[T]
    e = np.concatenate([TF[:, [0, 1]], TF[:, [1, 2]], TF[:, [2, 0]]])
    n = w.max() + 1
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fl = lab[TF[:, 0]]
    dom = J[np.arange(len(J)), W.argmax(1)]
    print('==', name, len(T), 'faces', len(P), 'verts', 'components', len(np.unique(fl)))
    for c, cnt in Counter(fl).most_common():
        f = np.flatnonzero(fl == c); v = np.unique(T[f])
        bc = Counter(names[b] for b in dom[v]).most_common(3)
        lo, hi = P[v].min(0), P[v].max(0)
        print(f'  comp {c:4d} faces {cnt:5d}  y {lo[1]:.3f}..{hi[1]:.3f} x {lo[0]:.3f}..{hi[0]:.3f} z {lo[2]:.3f}..{hi[2]:.3f}  ', bc)
