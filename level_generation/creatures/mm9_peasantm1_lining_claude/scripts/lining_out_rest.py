#!/usr/bin/env python3
"""Debug for lining_gate.py at rest: which lining vertices of one op lie outside their cloth (signed distance > tol), with
their rest position, the source vertex they line and the nearest cloth face's normal. Usage: lining_out_rest.py <glb> <npz> <op> [tol 0.0005]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, linz, OP = sys.argv[1:4]; TOL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0005
m = Model(Glb(glb)); z = np.load(linz); name = 'PeasantM1_A'
tags = z[f'vtag_{name}']; n0 = int(z[f'nvert_{name}']); piece = z[f'piece_{name}']
T = m.primitives[0]['triangles']; T0 = T[(T < n0).all(1)]
vs = np.array([n0 + i for i, t in enumerate(tags) if t.split('|')[0] == OP and t.split('|')[1] in ('twin', 'centre')])
ps = {int(x) for t in tags if t.split('|')[0] == OP for x in t.split('|')[2].split(',') if x}
tri = T0[np.isin(piece[T0[:, 0]], list(ps))]
X = m.skinned_positions(m.world({}))[0][0]
tr = X[tri]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True)
Q = X[vs]; _, ids = cKDTree(c).query(Q, k=32); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q)); bi = np.zeros(len(Q), int)
for k in range(32):
    i = ids[:, k]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
    best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1); bi[u] = i[u]
P0 = m.primitives[0]['positions']
for j in np.where(sd > TOL)[0]:
    v = vs[j]; src = np.argmin(np.linalg.norm(P0[:n0] - P0[v], axis=1))
    print(f'v {v} rest {X[v].round(4)} out {sd[j] * 1000:.2f} mm, nearest cloth face {tri[bi[j]]} normal {n[bi[j]].round(2)}, '
          f'nearest original vertex {src} at {np.linalg.norm(P0[src] - P0[v]) * 1000:.2f} mm')
