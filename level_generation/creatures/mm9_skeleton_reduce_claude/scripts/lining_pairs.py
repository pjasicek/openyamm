#!/usr/bin/env python3
"""Find reversed coincident face pairs (outer face + lining copy) in the Skel primitive of a GLB; report the lining
faces' UVs against their outer twin and which components carry them. Args: <glb> [out npy of lining flags]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g)
prim = g.json['meshes'][0]['primitives'][0]
uv = g.accessor(prim['attributes']['TEXCOORD_0']); nrm = g.accessor(prim['attributes']['NORMAL'])
P, T = m.primitives[0]['positions'], m.primitives[0]['triangles']
key = np.round(P / 1e-6).astype(np.int64); _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
t = wid[T]
canon = {}
for i, f in enumerate(t):
    canon.setdefault(tuple(sorted(f)), []).append(i)
pairs = [v for v in canon.values() if len(v) > 1]
print('coincident face groups', len(pairs), 'sizes', np.unique([len(v) for v in pairs], return_counts=True))
# geometric normal vs stored vertex normals: the lining's stored normals point opposite to the outer's
lin = np.zeros(len(T), bool)
for a, b in [v[:2] for v in pairs]:
    na = nrm[T[a]].mean(0); nb = nrm[T[b]].mean(0)
    ga = np.cross(P[T[a][1]] - P[T[a][0]], P[T[a][2]] - P[T[a][0]])
    # the lining was added later; assume the face with the higher index is the lining
    lin[max(a, b)] = True
li = np.where(lin)[0]
print('lining faces', len(li))
d_uv = []
for a, b in [v[:2] for v in pairs]:
    lo, hi = min(a, b), max(a, b)
    ua = {wid[T[lo][k]]: uv[T[lo][k]] for k in range(3)}
    d_uv.append(max(np.abs(ua[wid[T[hi][k]]] - uv[T[hi][k]]).max() for k in range(3)))
d_uv = np.array(d_uv); print('lining uv vs outer uv: max diff p50 %.4g max %.4g' % (np.median(d_uv), d_uv.max()))
print('lining uv range', uv[T[li]].reshape(-1, 2).min(0), uv[T[li]].reshape(-1, 2).max(0))
print('index range of lining', li.min(), li.max())
if len(sys.argv) > 2: np.save(sys.argv[2], lin)
