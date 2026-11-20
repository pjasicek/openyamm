#!/usr/bin/env python3
"""Per material of the LOD0 mesh: positions of the reduced GLB found in the source GLB (exact to 1e-5) and, for those,
the angle between the normals and the UV distance. Kept parts must match exactly. Usage: prim_compare.py <src glb> <new glb>"""
import json, struct, sys
import numpy as np
from scipy.spatial import cKDTree
def load(p):
    d = open(p, 'rb').read(); n = struct.unpack('<I', d[12:16])[0]; g = json.loads(d[20:20 + n]); b = d[20 + n + 8:]
    def acc(i):
        a = g['accessors'][i]; bv = g['bufferViews'][a['bufferView']]
        k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]; dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(b, dt, a['count'] * k, off).reshape(a['count'], k)
    out = {}
    for p in g['meshes'][0]['primitives']:
        at = p['attributes']; out[g['materials'][p['material']]['name']] = (acc(at['POSITION']), acc(at['NORMAL']), acc(at['TEXCOORD_0']), acc(p['indices']).reshape(-1, 3))
    return out
A, B = load(sys.argv[1]), load(sys.argv[2])
for m in A:
    pa, na, ua, _ = A[m]; pb, nb, ub, ib = B[m]
    t = cKDTree(np.hstack([pa, ua * 0.001])); d, j = t.query(np.hstack([pb, ub * 0.001]))
    ok = d < 2e-5
    ang = np.degrees(np.arccos(np.clip((na[j[ok]] * nb[ok]).sum(1), -1, 1)))
    print(m, 'new verts', len(pb), 'found in source', int(ok.sum()), 'normal diff deg p50/p90/max', np.round(np.percentile(ang, [50, 90, 100]), 2) if ok.any() else '-',
          'tris', len(ib))
