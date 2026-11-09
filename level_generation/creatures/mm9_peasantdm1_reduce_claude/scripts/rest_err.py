#!/usr/bin/env python3
"""Rest-pose source -> candidate distances (work/mesh_in.npz vs work/mp_<label>_r<NN> mesh) by GLB set part/group: where the
candidate lost surface at rest. Usage: rest_err.py <mesh npz> <sets tag> [mm]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from detached_parts_audit import closest_on_triangles  # noqa: E402
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
c = np.load(sys.argv[1]); CV, CF = c['verts'], c['faces']; LIM = float(sys.argv[3]) / 1000 if len(sys.argv) > 3 else 0.003
tr = CV[CF]; cen = tr.mean(1); kd = cKDTree(cen)
used = np.unique(F); Q = V[used]; _, ids = kd.query(Q, 16); best = np.full(len(Q), 9.0)
for k in range(16):
    i = ids[:, k]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); best = np.minimum(best, np.linalg.norm(q - Q, axis=1))
s = np.load(HERE / 'work' / f'glb_sets_{sys.argv[2]}.npz')
# mesh_in faces are in GLB face order (prim 0 then prim 1): label a vertex by the faces using it
lab = {}
for f in range(len(F)):
    for v in F[f]:
        lab.setdefault(v, (int(s['part'][f]), int(s['group'][f]), bool(s['keep'][f]), bool(s['lining'][f]), bool(s['lined'][f])))
bad = used[best > LIM]
from collections import Counter
print('verts >', LIM * 1000, 'mm:', len(bad), 'max', round(best.max() * 1000, 1))
print(Counter(lab[v] for v in bad).most_common(12))
for v in bad[np.argsort(-best[best > LIM])][:10]:
    print(v, V[v].round(3), round(best[np.searchsorted(used, v)] * 1000, 1), lab[v])
