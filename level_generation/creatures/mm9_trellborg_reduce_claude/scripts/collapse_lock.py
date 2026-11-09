#!/usr/bin/env python3
"""Keep the source faces within R m (rest) of the faces creature_gates/collapse_gate.py found collapsing or flipping in a candidate
(work/<tag>.json.npz) in the given regions, for the next ladder. Usage: collapse_lock.py <coll npz> <regions,> <base keep> <out>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
R = float(os.environ.get('R', .025))
c = np.load(sys.argv[1]); regs = sys.argv[2].split(',')
f = np.unique(np.concatenate([c[k] for k in c.files if k.startswith('f_')])); f = f[np.isin(c['label'][f], regs)]
d = np.load(HERE / 'work/mesh_in.npz'); FC = d['verts'][d['faces']].mean(1)
_, _, _, S = glbio.load(HERE / 'before/mm9_trellborg.glb', 'Trellborg')
allc = np.vstack([S[n]['P'][S[n]['T']].mean(1) for n in S])[:, [0, 2, 1]] * [1, -1, 1]
off = np.median(FC, 0) - np.median(allc, 0)
for _ in range(5):
    dist, nn = cKDTree(FC).query(allc + off); off += np.median(FC[nn] - (allc + off), 0)
P = c['cen'][f][:, [0, 2, 1]] * [1, -1, 1] + off
keep = np.load(sys.argv[3]).copy(); n0 = int(keep.sum()); t = cKDTree(FC)
for p in P:
    keep[t.query_ball_point(p, R)] = True
np.save(sys.argv[4], keep); print('COLLAPSELOCK', len(f), 'faces;', n0, '->', int(keep.sum()))
