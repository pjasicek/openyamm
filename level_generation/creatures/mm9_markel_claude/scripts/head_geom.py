#!/usr/bin/env python3
"""Print the head primitive's loose parts (bind pose, glTF y-up metres) of work/mk_body_tex.glb: faces, bounds."""
import numpy as np
from pygltflib import GLTF2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
g = GLTF2().load('work/mk_body_tex.glb'); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('MarkelHead'))
P = acc(prim.attributes.POSITION).astype(float); I = acc(prim.indices).reshape(-1, 3)
_, weld = np.unique(np.round(P, 5), axis=0, return_inverse=True); weld = weld.ravel(); F = weld[I]
n = weld.max() + 1
r = np.concatenate([F[:, 0], F[:, 1], F[:, 2]]); c = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
fp = lab[F[:, 0]]
for k in np.unique(fp):
    v = P[I[fp == k]].reshape(-1, 3)
    print(k, (fp == k).sum(), v.min(0).round(3), v.max(0).round(3))
