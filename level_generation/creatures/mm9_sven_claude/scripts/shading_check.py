#!/usr/bin/env python3
"""Flat-shading check of a GLB's LOD0 primitives (2026-10-30, Forad v2 rendered faceted): per primitive the vertex
count, unique positions, and the share of triangles whose three vertex normals all equal the face normal (flat).
A smooth export has well under 10 % flat triangles; a faceted one has vertices = 3 x triangles and ~100 %.
Usage: shading_check.py <glb> [mesh name filter]"""
import json, struct, sys
import numpy as np
b = open(sys.argv[1], 'rb').read()
n = struct.unpack_from('<I', b, 12)[0]
J = json.loads(b[20:20 + n])
off = 20 + n + 8
W = {5126: ('f', 4), 5125: ('I', 4), 5123: ('H', 2), 5121: ('B', 1)}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def acc(i):
    a = J['accessors'][i]; v = J['bufferViews'][a['bufferView']]
    t, s = W[a['componentType']]; c = NC[a['type']]
    o = off + v.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = v.get('byteStride', s * c)
    raw = np.frombuffer(b, np.uint8, count=st * (a['count'] - 1) + s * c, offset=o)
    out = np.lib.stride_tricks.as_strided(raw, (a['count'], s * c), (st, 1)).copy().view(np.dtype(t).newbyteorder('<'))
    return out.reshape(a['count'], c)


flt = sys.argv[2] if len(sys.argv) > 2 else ''
for m in J['meshes']:
    if 'LOD' in m['name'] or 'Shadow' in m['name'] or flt not in m['name']:
        continue
    for k, p in enumerate(m['primitives']):
        P = acc(p['attributes']['POSITION']); N = acc(p['attributes']['NORMAL']); I = acc(p['indices']).ravel()
        T = I.reshape(-1, 3)
        fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        flat = np.all([np.einsum('ij,ij->i', N[T[:, j]], fn) > 0.9995 for j in range(3)], axis=0)
        up = len(np.unique(P.round(6), axis=0))
        print(f"SHADING {m['name']} prim {k}: {len(T)} tris, {len(P)} verts, {up} unique positions, "
              f"flat {100 * flat.mean():.1f} %")
