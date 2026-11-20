#!/usr/bin/env python3
"""Rest-pose lining check of one GLB (PeasantDM2 reduction): lining_gate.py's signed distance with K nearest outer faces by
centroid (gate: 8); lists the worst lining vertices (position, distance, whether the vertex belongs to a re-emitted or an
exact lining face). Usage: lining_probe_rest.py <glb> [K]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
K = int(sys.argv[2]) if len(sys.argv) > 2 else 8
m = Model(Glb(sys.argv[1])); src = Model(Glb(str(HERE / 'before' / 'mm9_peasantdm2.glb')))
tw = np.load(HERE / 'work' / 'twins.npz'); lin = tw['lining'] | tw['lining2']
sp = src.primitives[0]; cp = m.primitives[0]
lv_src = np.unique(sp['triangles'][lin[:len(sp['triangles'])]].ravel())
d, j = cKDTree(sp['positions'][lv_src]).query(cp['positions']); is_lin = d < 1e-7
T = cp['triangles']; outer = T[~is_lin[T].any(1)]
linv = np.flatnonzero(is_lin & np.isin(np.arange(len(is_lin)), T.ravel()))
X = cp['positions']; tr = X[outer]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
Q = X[linv]; _, ids = cKDTree(c).query(Q, k=K); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
for k in range(K):
    i = ids[:, k]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); dd = np.linalg.norm(q - Q, axis=1); u = dd < best
    best[u] = dd[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
o = np.argsort(-sd)[:12]
for i in o:
    print(f'v{linv[i]} pos {X[linv[i]].round(4)} out {sd[i] * 1000:.2f} mm nearest {best[i] * 1000:.2f} mm')
print('K', K, 'over 0.5 mm', int((sd > 0.0005).sum()), 'max', round(float(sd.max()) * 1000, 2))
