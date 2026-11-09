#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (prims Ghoul_A body, GhoulHead_A head) from the creature's own pre-export face dump
(../mm9_ghoul_claude/work/faces.npz: rest positions, part, head flag), matched by centroid (GLB = Blender x, z + LIFT, -y).
Faces export_ghoul.py added after that dump (flap lining and rim on the body, the skull plug on the head) do not match and
are labelled from their geometry: lining = reversed copy 4 mm inside a flap face, rim = quad strip on the open edge, plug = the
dark icosphere. Parts: 0 skin, 3 belt/other, 6 front flap, 7 back flap, 10 face, 11 hair, 12 teeth, 13 eyes;
extra labels 20 lining, 21 rim, 22 plug. Writes work/labels.npz (part per GLB face, in primitive order)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
LIFT = 1.1093
doc, b = gb.read(HERE / 'before' / 'mm9_ghoul.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Ghoul' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Ghoul_A', 'GhoulHead_A']
F = np.load(HERE.parent / 'mm9_ghoul_claude' / 'work' / 'faces.npz')
co = F['co'].astype(float); cen = co.mean(1); cen = np.c_[cen[:, 0], cen[:, 2] + LIFT, -cen[:, 1]]
tree = cKDTree(cen)
out = []
for k, p in enumerate(pr):
    P = p['POSITION'].astype(float); T = p['T']; c = P[T].mean(1)
    d, i = tree.query(c)
    lab = np.where(d < 2e-4, F['part'][i], -1)
    hd = F['head'][i]
    ok = d < 2e-4
    print(p['material'], len(T), 'matched', int(ok.sum()), 'head flag mismatch', int((ok & (hd != k)).sum()), 'dist max matched', d[ok].max())
    un = np.flatnonzero(~ok)
    if k == 1:
        lab[un] = 22
    else:
        # lining faces lie 4 mm inside a flap face; the rim quads join both
        d2, _ = cKDTree(c[ok & np.isin(lab, (6, 7))]).query(c[un])
        lab[un] = np.where(d2 > 0.0035, 20, 21)
        n_ = np.cross(P[T[un, 1]] - P[T[un, 0]], P[T[un, 2]] - P[T[un, 0]])
    print('  labels', {int(u): int((lab == u).sum()) for u in np.unique(lab)})
    out.append(lab)
np.savez(HERE / 'work' / 'labels.npz', body=out[0], head=out[1])
