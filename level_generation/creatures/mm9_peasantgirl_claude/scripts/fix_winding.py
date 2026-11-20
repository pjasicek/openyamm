#!/usr/bin/env python3
"""Reversed thin closed pieces in the coarse LODs and shrunken shadow meshes (a panel pushed through itself): each connected closed part with negative signed volume gets its triangles reversed, in place. LOD0 is never touched. Args: <in> <out>"""
import sys
import numpy as np
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def view(i):
    a = g.accessors[i]; v = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3}[a.type]; ct = {5126: 'f4', 5123: 'u2', 5125: 'u4'}[a.componentType]
    o = (v.byteOffset or 0) + (a.byteOffset or 0); return np.frombuffer(blob, ct, a.count * n, o).reshape(a.count, n).copy(), o, ct
fixed = 0
for mesh in g.meshes:
    if 'LOD' not in (mesh.name or '') and 'Shadow' not in (mesh.name or ''): continue
    Ps, Ts, spans = [], [], []; off_v = 0
    for p in mesh.primitives:
        P, _, _ = view(p.attributes.POSITION); I, off, ct = view(p.indices)
        Ps.append(P); Ts.append(I.reshape(-1, 3).astype(int) + off_v); spans.append((off, ct, off_v, len(I) // 3)); off_v += len(P)
    P = np.vstack(Ps); T = np.vstack(Ts)
    key = np.round(P * 1e4).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    par = np.arange(inv.max() + 1)
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    Tw = inv[T]
    for t in Tw: a_ = f(t[0]); par[f(t[1])] = a_; par[f(t[2])] = a_
    root = np.array([f(i) for i in Tw[:, 0]])
    for r in np.unique(root):
        s_ = root == r; tt = Tw[s_]
        e = np.sort(np.vstack([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True)
        if (c == 2).all():
            v0, v1, v2 = P[T[s_, 0]].astype(float), P[T[s_, 1]].astype(float), P[T[s_, 2]].astype(float)
            if (np.cross(v0, v1) * v2).sum() < 0:
                T[s_] = T[s_][:, ::-1]; fixed += 1
    k = 0
    for off, ct, ov, n in spans:
        Tn = T[k:k + n] - ov; k += n
        blob[off:off + Tn.size * int(ct[1])] = Tn.astype(ct).tobytes()
print('FIXWIND', fixed)
g.set_binary_blob(bytes(blob)); g.save(OUT)
