"""Compare two upload GLBs: per-corner (position, uv) sets. Args: a.glb b.glb (system python + pygltflib venv)"""
import sys, numpy as np
from pygltflib import GLTF2
def load(p):
    g = GLTF2().load(p); blob = g.binary_blob(); out_p, out_u = [], []
    def acc(i):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
        n = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a.type]; dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
        return np.frombuffer(blob, dt, a.count * n, bv.byteOffset + (a.byteOffset or 0)).reshape(a.count, n) if n > 1 else np.frombuffer(blob, dt, a.count, bv.byteOffset + (a.byteOffset or 0))
    for m in g.meshes:
        for pr in m.primitives:
            P = acc(pr.attributes.POSITION); U = acc(pr.attributes.TEXCOORD_0); I = acc(pr.indices)
            out_p.append(P[I]); out_u.append(U[I])
    return np.concatenate(out_p), np.concatenate(out_u)
pa, ua = load(sys.argv[1]); pb, ub = load(sys.argv[2])
from scipy.spatial import cKDTree
ka = np.concatenate([pa, ua * 1.0], 1); kb = np.concatenate([pb, ub * 1.0], 1)
d, _ = cKDTree(kb).query(ka)
print('corners', len(ka), len(kb), 'match p50 %.2e p99 %.2e max %.2e' % (np.median(d), np.percentile(d, 99), d.max()))
