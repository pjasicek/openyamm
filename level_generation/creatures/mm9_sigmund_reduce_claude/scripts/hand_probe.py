#!/usr/bin/env python3
"""Which body faces the arm/hand gate's 'hand in body' reads on a candidate: posed installed vertices (clip, t), body faces of
work/mp_<tag>.npz vs the installed LOD0; hand vertices of side S (joint names) with signed distance below -DEPTH to the nearest
body face (normal side test), per nearest-face class (glb_sets_<sets>.npz cls of the face it came from). Usage:
hand_probe.py <mp tag|inst> <clip> <t> <side L|R> [sets c]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import glbio  # noqa: E402
tag, clip, t, side = sys.argv[1:5]; sets = sys.argv[5] if len(sys.argv) > 5 else 'c'
_, _, nd, D = glbio.load(HERE / 'before' / 'mm9_sigmund.glb', 'Sigmund')
s = np.load(HERE / 'work' / f'glb_sets_{sets}.npz'); g = np.load(HERE / 'work' / 'glb_parts.npz'); jn = [str(x) for x in g['jnames']]
m = Model(Glb(str(HERE / 'before' / 'mm9_sigmund.glb')))
pos = [p for p, _ in m.skinned_positions(m.world(m.sample(clip, float(t))))]
T0 = D['Sigmund']['T']; Tb = T0 if tag == 'inst' else np.load(HERE / 'work' / f'mp_{tag}.npz')['Sigmund']
key = {tuple(sorted(x)): i for i, x in enumerate(T0.tolist())}
P = pos[0]; Vb = P[Tb]; cen = Vb.mean(1); nrm = np.cross(Vb[:, 1] - Vb[:, 0], Vb[:, 2] - Vb[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
cls = s['cls'][:len(T0)]
fcls = np.array([cls[key[tuple(sorted(x))]] if tuple(sorted(x)) in key else -2 for x in Tb.tolist()])
H = D['SigmundHead']; J = H['J']; W = H['W']; ph = pos[1]
hs = np.array([(' ' + side + ' ') in x and any(k in x for k in ('Hand', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb', 'Finger')) for x in jn])
hv = np.flatnonzero((W * hs[J]).sum(1) > 0.5)
# signed distance to the nearest body face centroid's plane among the 8 nearest outer faces
outer = ~np.isin(fcls, (30, 31))
tr = cKDTree(cen[outer]); idx = np.flatnonzero(outer)
d, nn = tr.query(ph[hv], 8)
out = []
for v, row in zip(hv, nn):
    fs = idx[row]; sd = ((ph[v] - cen[fs]) * nrm[fs]).sum(1); k = np.abs(np.linalg.norm(ph[v] - cen[fs], axis=1)).argmin()
    out.append((sd[k], fs[k], fcls[fs[k]]))
out = np.array(out)
bad = out[out[:, 0] < -0.01]
print(tag, clip, t, side, 'hand verts', len(hv), 'deeper than 1 cm (nearest outer face plane):', len(bad))
if len(bad):
    u, c = np.unique(bad[:, 2], return_counts=True); print('  by nearest face class', dict(zip(u.astype(int).tolist(), c.tolist())),
                                                          'min', bad[:, 0].min().round(3), 'faces', np.unique(bad[:, 1]).astype(int)[:12])
    print('  hand pts', ph[hv][out[:, 0] < -0.01].mean(0).round(3))
