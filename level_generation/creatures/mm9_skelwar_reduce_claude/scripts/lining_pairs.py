#!/usr/bin/env python3
"""Find reversed coincident face pairs (outer face + lining copy) in LOD0 primitive PRIM (0 body, 1 head) of a GLB; report
the lining faces' UVs and which components carry them. Skelwar: finish_skelwar.py added the linings after the paint, each a
flipped coincident copy on one dark texel of its own set. Args: <glb> <prim> [out npy of lining flags]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g); pi = int(sys.argv[2])
prim = g.json['meshes'][0]['primitives'][pi]
uv = g.accessor(prim['attributes']['TEXCOORD_0'])
P, T = m.primitives[pi]['positions'], m.primitives[pi]['triangles']
key = np.round(P / 1e-6).astype(np.int64); _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
t = wid[T]
canon = {}
for i, f in enumerate(t):
    canon.setdefault(tuple(sorted(f)), []).append(i)
pairs = [v for v in canon.values() if len(v) > 1]
print('coincident face groups', len(pairs), 'sizes', np.unique([len(v) for v in pairs], return_counts=True))
lin = np.zeros(len(T), bool)
for v in pairs:
    lin[max(v[:2])] = True
li = np.where(lin)[0]
print('lining faces', len(li), 'index range', li.min(), li.max(), 'contiguous at end', li.min() == len(T) - len(li))
u = uv[T[li]].reshape(-1, 2)
print('lining uv unique', np.unique(np.round(u, 6), axis=0)[:6], 'n', len(np.unique(np.round(u, 6), axis=0)))
# orientation: the lining's geometric normal opposite to the outer's
bad = 0
for v in pairs:
    a, b = min(v[:2]), max(v[:2])
    na = np.cross(P[T[a][1]] - P[T[a][0]], P[T[a][2]] - P[T[a][0]]); nb = np.cross(P[T[b][1]] - P[T[b][0]], P[T[b][2]] - P[T[b][0]])
    bad += na @ nb > 0
print('pairs with same orientation (not reversed)', bad)
if len(sys.argv) > 3: np.save(sys.argv[3], lin)
