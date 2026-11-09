#!/usr/bin/env python3
"""Texel -> rest position map of one primitive (by material name) of an export GLB, rasterised in its UV layout.
Library: texel_positions(glb, material, size) -> (pos HxWx3 with NaN outside, covered HxW). glTF UV (v down)."""
import numpy as np
from pygltflib import GLTF2


def texel_positions(glb, material, size):
    g = GLTF2().load(glb)
    blob = g.binary_blob()

    def acc(i):
        a = g.accessors[i]
        bv = g.bufferViews[a.bufferView]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
        return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
    prim = next(p for m in g.meshes for p in m.primitives if material is None or g.materials[p.material].name == material)
    P = acc(prim.attributes.POSITION).astype(np.float64)
    UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
    TRI = acc(prim.indices).reshape(-1, 3).astype(int)
    N = size
    pos = np.full((N, N, 3), np.nan)
    for t in TRI:
        uv = UV[t] * N
        x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), N - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = uv
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        L = np.stack([l0, l1, 1 - l0 - l1], -1)
        ins = (L >= -1e-3).all(-1)
        if ins.any():
            pos[(ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)] = L[ins] @ P[t]
    return pos, ~np.isnan(pos[..., 0])
