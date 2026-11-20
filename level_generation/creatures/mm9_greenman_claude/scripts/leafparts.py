#!/usr/bin/env python3
"""Loose-part label image of one material of an export GLB (mm9_greenman: Meshy's leaves are separate small parts).
Library: part_labels(glb, material, size) -> (label HxW int32, -1 empty; part sizes in triangles; the largest part id)
Parts: triangles connected through positions welded at 1e-5. glTF UV (v down) = image rows."""
import numpy as np
from pygltflib import GLTF2


def part_labels(glb, material, size):
    g = GLTF2().load(glb); blob = g.binary_blob()

    def acc(i):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
        return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
    prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == material)
    P = acc(prim.attributes.POSITION).astype(np.float64); UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
    TRI = acc(prim.indices).reshape(-1, 3).astype(int)
    _, inv = np.unique(np.round(P, 5), axis=0, return_inverse=True); inv = inv.ravel()
    par = np.arange(inv.max() + 1)
    def find(x):
        r = x
        while par[r] != r:
            r = par[r]
        while par[x] != r:
            par[x], x = r, par[x]
        return r
    for t in TRI:
        a, b, c = find(inv[t[0]]), find(inv[t[1]]), find(inv[t[2]])
        par[b] = a; par[find(c)] = a
    tp = np.array([find(inv[t[0]]) for t in TRI])
    ids, tp = np.unique(tp, return_inverse=True)
    sizes = np.bincount(tp)
    N = size; lab = np.full((N, N), -1, np.int32)
    for k, t in enumerate(TRI):
        uv = UV[t] * N
        x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), N - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = uv
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (1 - l0 - l1 >= -1e-3)
        lab[(ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)] = tp[k]
    return lab, sizes, int(np.argmax(sizes))
