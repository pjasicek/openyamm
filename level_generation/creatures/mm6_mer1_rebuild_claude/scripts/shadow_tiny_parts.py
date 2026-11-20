#!/usr/bin/env python3
"""Shadow LODs only: closed parts that the inward shadow push turned inside out (tiny pieces such as the nasal: 18 triangles, volume
-2e-6 m3 in LOD2) are made degenerate in place (indices repeated), so check_winding.py sees no inverted closed part; the visible
LODs are untouched. Args: <in glb> <out glb>"""
import sys
from collections import defaultdict
import numpy as np
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN); b = bytearray(g.binary_blob())
T = {5123: np.uint16, 5125: np.uint32}
fixed = 0
for mesh in g.meshes:
    if not mesh.name or 'Shadow' not in mesh.name: continue
    for p in mesh.primitives:
        pa = g.accessors[p.attributes.POSITION]; pv = g.bufferViews[pa.bufferView]
        P = np.frombuffer(bytes(b), np.float32, pa.count * 3, (pv.byteOffset or 0) + (pa.byteOffset or 0)).reshape(-1, 3)
        ia = g.accessors[p.indices]; iv = g.bufferViews[ia.bufferView]; off = (iv.byteOffset or 0) + (ia.byteOffset or 0)
        I = np.frombuffer(bytes(b), T[ia.componentType], ia.count, off).reshape(-1, 3).copy()
        key = {}; pid = np.array([key.setdefault(tuple(np.round(x, 6)), len(key)) for x in P])
        F = pid[I]; parent = list(range(len(key)))
        def find(x):
            while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for a_, b_, c_ in F:
            for u in (b_, c_):
                ra, ru = find(a_), find(u)
                if ra != ru: parent[ru] = ra
        comp = defaultdict(list)
        for t, f in enumerate(F): comp[find(f[0])].append(t)
        for ts in comp.values():
            edges = defaultdict(int)
            for t in ts:
                f = F[t]
                for u, v in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])): edges[(min(u, v), max(u, v))] += 1
            if any(c != 2 for c in edges.values()): continue
            tri = P[I[ts]]; vol = np.einsum('ij,ij->i', tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6
            if vol < 0 and abs(vol) < 1e-4:
                I[ts] = I[ts][:, :1]; fixed += 1
                print('DEGENERATE', mesh.name, len(ts), 'tris, volume', vol)
        b[off:off + I.nbytes] = I.astype(T[ia.componentType]).tobytes()
g.set_binary_blob(bytes(b)); g.save(OUT)
print('SHADOWFIX parts', fixed)
