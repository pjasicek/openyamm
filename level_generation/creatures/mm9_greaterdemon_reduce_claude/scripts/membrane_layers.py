#!/usr/bin/env python3
"""Membrane shell analysis (GreaterDemon_Wing: the creature's Coons patches solidified to an 8 mm shell with rims).
Per GLB face: layer label (0 outer = +normal side picked per wing as the larger-normal-z?, here simply the two big sheet
components after removing rim faces), rim flag; per topological vertex its twin on the other sheet; UV seam counts."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb
doc, b = gb.read(HERE / 'before' / 'mm9_greaterdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
pr = {p['material']: p for p in gb.prims(doc, b, node['mesh'])}['GreaterDemon_Wing']
P = pr['POSITION'].astype(float); T = pr['T']; UV = pr['TEXCOORD_0'].astype(float)
_, tp = np.unique(np.round(P, 5), axis=0, return_inverse=True); tp = tp.ravel(); nt = tp.max() + 1
X = np.zeros((nt, 3)); X[tp] = P
TF = tp[T]
# glb vertices per topo vertex
cnt = np.bincount(tp, minlength=nt)
print('topo verts', nt, 'glb verts', len(P), 'seam topo verts (>1 glb)', int((cnt > 1).sum()))
el = np.linalg.norm(X[TF[:, [1, 2, 0]]] - X[TF], axis=2)
print('edge length percentiles mm', np.percentile(el, [0, 1, 5, 25, 50, 75, 99, 100]).round(4) * 1000)
short = el < 0.011
rim = short.any(1)
print('faces with an edge < 11 mm (rim)', int(rim.sum()))
# components without rim faces
F = TF[~rim]
r = np.concatenate([F[:, 0], F[:, 1], F[:, 2]]); c = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
nc, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nt, nt)), directed=False)
fl = lab[F[:, 0]]
print('sheet components (faces)', sorted(np.bincount(fl).tolist(), reverse=True)[:8])
