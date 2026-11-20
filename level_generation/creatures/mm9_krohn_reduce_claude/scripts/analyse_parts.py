#!/usr/bin/env python3
"""Installed Yanmir LOD0: per primitive, welded connected components with size, bbox and dominant joints (orientation pass)."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_yanmir.glb', 'Yanmir')
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
for name, d in D.items():
    P, T, J, W = d['P'], d['T'], d['J'], d['W']
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    fl = lab[FT[:, 0]]
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    dom = acc.argmax(1)
    print('==', name, len(T), 'faces', len(P), 'verts', 'components', len(np.unique(fl)), 'y range', P[:, 1].min().round(3), P[:, 1].max().round(3))
    u, cnt = np.unique(fl, return_counts=True)
    for c in u[np.argsort(-cnt)][:30]:
        m = fl == c; v = P[np.unique(T[m])]
        uj, cj = np.unique(dom[m], return_counts=True); o = np.argsort(-cj)[:5]
        print(f'  comp {c}: {m.sum():5d} f  bbox min {v.min(0).round(3)} max {v.max(0).round(3)}  joints', {jn[uj[k]]: int(cj[k]) for k in o})
    uj, cj = np.unique(dom, return_counts=True); o = np.argsort(-cj)
    print('  by joint', {jn[uj[k]]: int(cj[k]) for k in o})
