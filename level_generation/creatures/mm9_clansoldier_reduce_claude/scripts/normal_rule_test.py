#!/usr/bin/env python3
"""Which normal rule reproduces the installed LOD0 normals: angle- or area-weighted face normals over the welded source topology
(work/mesh_in.npz, Blender's shade_smooth on the creature's final mesh). Prints deviation per material."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
X = V[F]; fn = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]); area = np.linalg.norm(fn, axis=1); un = fn / np.maximum(area, 1e-15)[:, None]
def ang(a, b, c):
    u, v = b - a, c - a
    return np.arccos(np.clip((u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-15), -1, 1))
rules = {}
for name, wt in (('angle', [ang(X[:, k], X[:, (k + 1) % 3], X[:, (k + 2) % 3]) for k in range(3)]), ('area', [area] * 3)):
    N = np.zeros_like(V)
    for k in range(3): np.add.at(N, F[:, k], un * wt[k][:, None])
    rules[name] = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-15)
m = Model(Glb(str(HERE / 'before' / 'mm9_clansoldier.glb')))
g = Glb(str(HERE / 'before' / 'mm9_clansoldier.glb'))
mesh = g.json['meshes'][0]
for k, p in enumerate(mesh['primitives']):
    P = np.asarray(g.accessor(p['attributes']['POSITION'])); N = np.asarray(g.accessor(p['attributes']['NORMAL']))
    Pb = P[:, [0, 2, 1]] * [1, -1, 1]; Pb[:, 2] -= 1.0438244
    Nb = N[:, [0, 2, 1]] * [1, -1, 1]
    dd, nn = cKDTree(V).query(Pb)
    for r, R in rules.items():
        dev = np.degrees(np.arccos(np.clip((R[nn] * Nb).sum(1), -1, 1)))
        print(k, r, 'match d max', dd.max().round(6), 'median', np.median(dev).round(3), 'p99', np.percentile(dev, 99).round(2), '>1deg', int((dev > 1).sum()), 'of', len(dev))
