#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_peasantf2.glb, node PeasantF2, primitives PeasantF2_A then
PeasantF2Head) from the creature project's last mesh npz (../mm9_peasantf2_claude/work/uv_lined.npz: comp per vertex,
names head/dress/skirt/hair/necklace/buckle/legs/hands/lining, inner per face).
Body faces match by rest centroid (exact). Head faces were moved after uv_lined (mouth/nose, neck projection), so they
match by centroid + 1000 x UV and the part is then voted per connected piece (position-welded) of the GLB head.
Writes work/glb_parts.npz: part (index into NAMES), inner, mat, piece (connected piece id per face, per primitive),
cen (glTF rest centroid). Usage: pf2_parts.py"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as g  # noqa: E402

doc, b = g.read(HERE / 'before' / 'mm9_peasantf2.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantF2' and 'mesh' in n)
prims = g.prims(doc, b, node['mesh'])
d = np.load(HERE.parent / 'mm9_peasantf2_claude' / 'work' / 'uv_lined.npz')
co, tri, mat, uv, comp, inner = d['co'], d['tri'], d['mat'], d['uv'], d['comp'], d['inner']
NAMES = [str(x) for x in d['names']]
fpart = comp[tri[:, 0]]
part, inn, mats, piece, cen = [], [], [], [], []
for k, p in enumerate(prims):
    P = p['POSITION'].astype(float); T = p['T']; UV = p['TEXCOORD_0'].astype(float)
    pb = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
    sel = np.flatnonzero(mat == k)
    if k == 0:
        dd, nn = cKDTree(co[tri[sel]].mean(1)).query(pb[T].mean(1))
        assert dd.max() < 2e-3, dd.max()
    else:
        su = uv[tri[sel]].mean(1); su = np.c_[su[:, 0], 1 - su[:, 1]]
        dd, nn = cKDTree(np.c_[co[tri[sel]].mean(1), 1000 * su]).query(np.c_[pb[T].mean(1), 1000 * UV[T].mean(1)])
    pa = fpart[sel[nn]].copy(); ii = inner[sel[nn]].copy()
    # connected pieces by welded position
    _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.reshape(-1)
    TT = tp[T]; nf = len(T); nv = tp.max() + 1
    rows = np.repeat(np.arange(nf), 3); A = coo_matrix((np.ones(3 * nf), (rows, TT.reshape(-1))), shape=(nf, nv)).tocsr()
    ncomp, lab = connected_components(A @ A.T, directed=False)
    if k == 1:
        for c in range(ncomp):
            m = lab == c
            vals = pa[m & ~ii] if (m & ~ii).any() else pa[m]
            pa[m] = np.bincount(vals).argmax()
    part.append(pa); inn.append(ii); mats.append(np.full(nf, k)); piece.append(lab); cen.append(P[T].mean(1))
    print(p['material'], nf, 'pieces', ncomp, {NAMES[i]: int((pa == i).sum()) for i in np.unique(pa)},
          'inner', int(ii.sum()), 'match max', float(dd.max()))
np.savez(HERE / 'work' / 'glb_parts.npz', part=np.concatenate(part), inner=np.concatenate(inn), mat=np.concatenate(mats),
         piece=np.concatenate(piece), cen=np.concatenate(cen), names=np.array(NAMES))
