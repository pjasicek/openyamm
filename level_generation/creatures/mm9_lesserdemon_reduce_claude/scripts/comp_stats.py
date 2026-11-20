#!/usr/bin/env python3
"""Connected components (position-welded) per GLB primitive with part label, size, bbox: what is a piece, what is a surface."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
doc, b = bglbio.read(HERE / 'before' / 'mm9_lesserdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'LesserDemon' and 'mesh' in n)
pr = bglbio.prims(doc, b, node['mesh']); g = np.load(HERE / 'work' / 'glb_parts.npz')
names = [n['name'] for n in doc['nodes']]
off = 0; comps = []
for m, p in enumerate(pr):
    P = p['POSITION'].astype(np.float64); T = p['T']
    _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.reshape(-1); TT = tp[T]
    n = tp.max() + 1; r = np.r_[TT[:, 0], TT[:, 1], TT[:, 2]]; c = np.r_[TT[:, 1], TT[:, 2], TT[:, 0]]
    k, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), (n, n)), directed=False)
    fl = lab[TT[:, 0]]; part = g['part'][off:off + len(T)]
    J = p['JOINTS_0']; W = p['WEIGHTS_0']
    for ci in np.unique(fl):
        f = np.flatnonzero(fl == ci); vs = np.unique(T[f]); bb = P[vs]
        dom = J[vs, W[vs].argmax(1)]; jn = np.bincount(dom).argmax()
        comps.append((m, int(np.bincount(part[f] + 1).argmax() - 1), len(f), bb.min(0).round(2).tolist(), bb.max(0).round(2).tolist(), doc['skins'][0]['joints'][jn]))
    np.save(HERE / 'work' / f'comp_{m}.npy', fl)
    off += len(T)
comps.sort(key=lambda x: (x[0], x[1], -x[2]))
for c in comps:
    print(c[0], 'part', c[1], 'faces', c[2], 'min', c[3], 'max', c[4], names[c[5]])
