#!/usr/bin/env python3
"""Clearance of the waist backstop tube to the painted cloth (Peasant boy reduction check, 2026-11-05): per clip at FPS, the tube faces'
sample points (corners, edge midpoints, centroids) of <glb>, the smallest unsigned distance to any painted (non-one-texel) body face
and the 1st percentile. A tube that never comes within a few mm of the cloth cannot show through it. Usage: tube_clearance.py <glb> [fps]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
import bglbio  # noqa: E402
glb = sys.argv[1]; FPS = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
m = Model(Glb(glb)); src = Model(Glb(str(HERE / 'before' / 'mm9_peasantboy.glb')))
sets = np.load(HERE / 'work' / 'glb_sets_a.npz'); sp = src.primitives[0]; cp = m.primitives[0]; ns = len(sp['triangles'])
doc, b = bglbio.read(glb); nd = next(n for n in doc['nodes'] if n.get('name') == 'PeasantBoy' and 'mesh' in n)
U = bglbio.prims(doc, b, nd['mesh'])[0]['TEXCOORD_0'].astype(np.float64); T = cp['triangles']
ua = np.abs((U[T[:, 1], 0] - U[T[:, 0], 0]) * (U[T[:, 2], 1] - U[T[:, 0], 1]) - (U[T[:, 2], 0] - U[T[:, 0], 0]) * (U[T[:, 1], 1] - U[T[:, 0], 1]))
outer = T[ua > 1e-10]
d, j = cKDTree(cp['positions']).query(sp['positions'][np.unique(sp['triangles'][sets['part'][:ns] == 6].ravel())])
ist = np.zeros(len(cp['positions']), bool); ist[j[d < 1e-7]] = True; tubeT = T[ist[T].all(1)]
W = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1 / 3, 1 / 3, 1 / 3]])
worst = (1e9, None)
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; mins = []
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        X = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
        Q = np.einsum('sk,fkc->fsc', W, X[tubeT]).reshape(-1, 3); tr = X[outer]
        _, ids = cKDTree(tr.mean(1)).query(Q, k=12); best = np.full(len(Q), 1e9)
        for k in range(12):
            q, _ = closest_on_triangles(Q, tr[ids[:, k], 0], tr[ids[:, k], 1], tr[ids[:, k], 2]); best = np.minimum(best, np.linalg.norm(q - Q, axis=1))
        mins.append((best.min(), np.percentile(best, 1)))
    a = np.array(mins); print(f'{clip:12s} min clearance {a[:, 0].min() * 1000:6.2f} mm, p1 {a[:, 1].min() * 1000:6.2f} mm', flush=True)
