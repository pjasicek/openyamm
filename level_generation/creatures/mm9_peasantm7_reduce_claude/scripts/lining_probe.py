#!/usr/bin/env python3
"""Rest-pose lining vertices outside the outer surface of their primitive (lining_gate.py's measure) with positions, for
installed vs candidate. Usage: lining_probe.py <glb> <prim> [n] [clip:seconds]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
m = Model(Glb(sys.argv[1])); src = Model(Glb(str(HERE / 'before' / 'mm9_peasantm7.glb'))); k = int(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 10
tw = np.load(HERE / 'work' / 'twins.npz'); lin = tw['lining']; nf = len(src.primitives[0]['triangles']); sl = slice(0, nf) if k == 0 else slice(nf, None)
sp, cp = src.primitives[k], m.primitives[k]
lv = np.unique(sp['triangles'][lin[sl]].ravel()); d, _ = cKDTree(sp['positions'][lv]).query(cp['positions']); is_lin = d < 1e-7
T = cp['triangles']; outer = T[~is_lin[T].any(1)]; linv = np.flatnonzero(is_lin & np.isin(np.arange(len(is_lin)), T.ravel()))
X = cp['positions'].astype(float)
if len(sys.argv) > 4:
    cl, sec = sys.argv[4].split(':'); X = m.skinned_positions(m.world(m.sample(cl, float(sec))))[k][0].astype(float)
tr = X[outer]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
Q = X[linv]; _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
for j in range(8):
    i = ids[:, j]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); dd = np.linalg.norm(q - Q, axis=1); u = dd < best
    best[u] = dd[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
o = np.argsort(-sd)[:N]
for i in o:
    print(f'{sd[i] * 1000:6.2f} mm at {Q[i].round(3)}')
print('over 0.5 mm', int((sd > 0.0005).sum()), 'over 2 mm', int((sd > 0.002).sum()))
