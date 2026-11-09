"""Compare two upload GLBs: triangle corners as (rounded position, UV); how many corners of A exist in B unchanged,
and whether the UV sets are equal. Args: a.glb b.glb  (run with claude_shared/gltf_venv/bin/python)"""
import sys, numpy as np, pygltflib
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def acc(g, blob, i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    dt = np.dtype(CT[a.componentType]); n = NC[a.type]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0); st = bv.byteStride or dt.itemsize * n
    raw = np.frombuffer(blob, np.uint8, count=st * (a.count - 1) + dt.itemsize * n, offset=off)
    return np.lib.stride_tricks.as_strided(raw.view(dt), (a.count, n), (st, dt.itemsize)).copy() if st != dt.itemsize * n else np.frombuffer(blob, dt, a.count * n, off).reshape(a.count, n)
def corners(p):
    g = pygltflib.GLTF2().load(p); blob = g.binary_blob(); out = []
    for m in g.meshes:
        for pr in m.primitives:
            V = acc(g, blob, pr.attributes.POSITION); U = acc(g, blob, pr.attributes.TEXCOORD_0)
            I = acc(g, blob, pr.indices).ravel() if pr.indices is not None else np.arange(len(V))
            out.append(np.concatenate([V[I], U[I]], 1))
    return np.concatenate(out)
A, B = corners(sys.argv[1]), corners(sys.argv[2])
print('corners', len(A), len(B))
ka = {tuple(np.round(r, 4)) for r in A}; kb = {tuple(np.round(r, 4)) for r in B}
print('A corners found unchanged in B (pos+uv):', len(ka & kb), 'of', len(ka))
ua = {tuple(np.round(r[3:], 4)) for r in A}; ub = {tuple(np.round(r[3:], 4)) for r in B}
print('UV sets equal:', ua == ub, len(ua), len(ub))
