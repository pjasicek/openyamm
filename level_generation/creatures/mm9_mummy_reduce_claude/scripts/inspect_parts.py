#!/usr/bin/env python3
"""Connected pieces and dominant bones per primitive of the installed Mummy LOD0 (orientation for make_sets.py)."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio
from weld import weld_ids
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_mummy.glb', 'Mummy')
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
for name, d in D.items():
    P, T, J, W = d['P'], d['T'], d['J'], d['W']
    w = weld_ids(P); FT = w[T]; n = w.max() + 1
    r = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fl = lab[FT[:, 0]]
    print(name, 'faces', len(T), 'verts', len(P), 'pieces', len(np.unique(fl)), 'bbox', P.min(0).round(3), P.max(0).round(3))
    for comp in np.unique(fl):
        s = fl == comp; vs = np.unique(T[s])
        acc = np.zeros(len(names)); np.add.at(acc, J[vs].ravel(), W[vs].ravel())
        top = np.argsort(-acc)[:4]
        print(f'  piece {comp:3d} faces {s.sum():5d} c {P[vs].mean(0).round(3)} bones', [(names[i], round(acc[i] / len(vs), 2)) for i in top])
    # faces by dominant bone
    dom = J[np.arange(len(P)), W.argmax(1)]
    fd = dom[T[:, 0]]
    u, cnt = np.unique(fd, return_counts=True)
    print('  faces by dominant bone of corner 0:', sorted([(names[a], int(b)) for a, b in zip(u, cnt)], key=lambda x: -x[1]))
