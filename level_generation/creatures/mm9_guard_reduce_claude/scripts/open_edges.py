#!/usr/bin/env python3
"""Open (boundary) edges of an mpqem step against the installed LOD0, welded by position (as the ladder's Blender weld):
prints the step's boundary edges that the installed mesh does not have, with their glTF midpoints and the parts of the faces
beside them. Usage: open_edges.py <mp npz>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, b = bglbio.read(HERE / 'before' / 'mm9_guard.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Guard' and 'mesh' in n)
prims = bglbio.prims(doc, b, node['mesh']); d = np.load(sys.argv[1])
P = np.vstack([p['POSITION'] for p in prims]).astype(np.float64); off = np.cumsum([0] + [len(p['POSITION']) for p in prims])
_, wid = np.unique(np.round(P, 6), axis=0, return_inverse=True); wid = wid.ravel()
def bnd(Ts):
    F = np.vstack([wid[T + o] for T, o in Ts]); E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True); return {tuple(e) for e in u[c == 1]}
a = bnd([(p['T'], off[i]) for i, p in enumerate(prims)]); bb = bnd([(d[p['material']], off[i]) for i, p in enumerate(prims)])
rep = np.zeros(wid.max() + 1, np.int64); rep[wid] = np.arange(len(P))
new = sorted(bb - a); print('installed', len(a), 'step', len(bb), 'new', len(new), 'closed', len(a - bb))
for e in new[:20]:
    print('  new open edge at', np.round((P[rep[e[0]]] + P[rep[e[1]]]) / 2, 3).tolist())
