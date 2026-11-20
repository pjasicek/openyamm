#!/usr/bin/env python3
"""Connected components (by welded position) of each LOD0 primitive, twin (reversed copy) detection, dominant joint."""
import sys, json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_compare import lod0, read_glb
path = sys.argv[1] if len(sys.argv) > 1 else 'before/mm9_peasantdf1.glb'
doc, _ = read_glb(Path(path))
skin = doc['skins'][0]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
for pi, A in enumerate(lod0(path)):
    P, T = A['P'], A['T']
    key = np.round(P / 1e-6).astype(np.int64)
    _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
    WT = wid[T]
    # twins: a face whose welded vertex set equals another face with opposite orientation
    fk = {}
    for f, t in enumerate(WT):
        s = tuple(sorted(t)); fk.setdefault(s, []).append(f)
    twin = np.zeros(len(T), bool)
    for s, fs in fk.items():
        if len(fs) >= 2:
            for f in fs: twin[f] = True
    n = wid.max() + 1
    r = np.concatenate([WT[:, 0], WT[:, 1], WT[:, 2]]); c = np.concatenate([WT[:, 1], WT[:, 2], WT[:, 0]])
    ncomp, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    flab = lab[WT[:, 0]]
    print(f'== prim{pi} tris {len(T)} verts {len(P)} comps {len(np.unique(flab))} faces in coincident pairs {twin.sum()}')
    rows = []
    for l in np.unique(flab):
        fm = flab == l; vs = np.unique(T[fm])
        dj = np.bincount(A['J'][vs][:, 0].astype(int), weights=A['W'][vs][:, 0], minlength=len(jn))
        top = [jn[i] for i in np.argsort(-dj)[:2]]
        lo, hi = P[vs].min(0), P[vs].max(0)
        rows.append((fm.sum(), twin[fm].sum(), top, lo.round(3).tolist(), hi.round(3).tolist(), np.unique(A['UV'][vs].round(2),axis=0).shape[0]))
    for r in sorted(rows, key=lambda r: -r[0])[:40]:
        print(f'  {r[0]:5d} tris twin {r[1]:5d} {r[2]} {r[3]} {r[4]}')
