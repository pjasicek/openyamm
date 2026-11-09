#!/usr/bin/env python3
"""F1's skirt lining (hidden in the skirt) against the outer skirt: points on every lining face (centroid + 3 inner barycentric
samples) that lie in front of the nearest skirt face (outside the skirt) by more than TOL, at rest and at every clip at 10 Hz.
Usage: lining_poke.py <glb> [TOL m, default 0.001]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
import bglbio as g  # noqa: E402
GLB = sys.argv[1]; TOL = float(sys.argv[2]) if len(sys.argv) > 2 else 0.001
L = np.load(HERE / 'work' / 'glb_labels.npz'); names = [str(x) for x in L['names']]
d0, b0 = g.read(HERE / 'before' / 'mm9_peasantf4.glb'); P0 = g.prims(d0, b0, 0)
d1, b1 = g.read(GLB); P1 = g.prims(d1, b1, 0)
dq, jq = cKDTree(np.c_[P0[0]['POSITION'], P0[0]['TEXCOORD_0'] * 0.01]).query(np.c_[P1[0]['POSITION'], P1[0]['TEXCOORD_0'] * 0.01])
assert dq.max() < 1e-6
vc = L['vcomp'][jq]; T = P1[0]['T']; fc = vc[T[:, 0]]
lin = T[fc == names.index('lining')]; sk = T[fc == names.index('skirt')]
M = Model(Glb(GLB)); B = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4]], float); B /= B.sum(1, keepdims=True)
def check(X):
    S = X[sk]; c = S.mean(1); n = np.cross(S[:, 1] - S[:, 0], S[:, 2] - S[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    p = np.einsum('sk,fkc->fsc', B, X[lin]).reshape(-1, 3); _, j = cKDTree(c).query(p)
    s = np.einsum('ij,ij->i', p - c[j], n[j]); return (s > TOL).reshape(len(lin), -1).any(1), s.max()
res = {}
bad, mx = check(M.skinned_positions(M.world({}))[0][0]); res['rest'] = (int(bad.sum()), round(float(mx) * 1000, 1))
for clip in M.clips:
    t1 = M.clip_times(clip)[-1]; worst = (0, 0.0)
    for t in np.append(np.arange(0, t1, 0.1), t1):
        bad, mx = check(M.skinned_positions(M.world(M.sample(clip, t)))[0][0])
        worst = max(worst, (int(bad.sum()), round(float(mx) * 1000, 1)))
    res[clip] = worst
print('LINING faces in front of the skirt (count, max mm):', res)
