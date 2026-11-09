#!/usr/bin/env python3
"""Rest position (glTF, floor 0, +Z front) of every head-set texel, rasterised from the textured export's head
material (work/pboy_body_tex.glb, unmirrored). Writes work/head_texel_pos.npz (pos[N, N, 3], NaN outside) at N = 2048.
Usage (project folder): head_texel_pos.py [glb] [out npz]"""
import sys
import numpy as np
from pygltflib import GLTF2
G = sys.argv[1] if len(sys.argv) > 1 else 'work/pboy_body_tex.glb'
OUTP = sys.argv[2] if len(sys.argv) > 2 else 'work/head_texel_pos.npz'
g = GLTF2().load(G); blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


N = 2048
pos = np.full((N, N, 3), np.nan, np.float32)
for m in g.meshes:
    for p in m.primitives:
        if not g.materials[p.material].name.endswith('Head'):
            continue
        P = acc(p.attributes.POSITION).astype(np.float64); UV = acc(p.attributes.TEXCOORD_0).astype(np.float64)
        T = acc(p.indices).reshape(-1, 3)
        for t in T:
            # needles: degenerate midline slivers whose UVs run across the face chart; rasterised, they stamped +x positions
            # in a line over the face's -x texels (a pale streak after the paint fixes); they cover no visible area
            e3 = max(np.linalg.norm(P[t[i]] - P[t[(i + 1) % 3]]) for i in range(3))
            eu = max(np.linalg.norm(UV[t[i]] - UV[t[(i + 1) % 3]]) for i in range(3))
            if eu > 0.01 and eu / max(e3, 1e-9) > 8.0:
                continue
            uv = UV[t] * N
            x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, N - 1), min(y1, N - 1)
            if x1 < x0 or y1 < y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            a, b, c = uv
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
            l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
            l2 = 1 - l0 - l1
            ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
            if not ins.any():
                continue
            L = np.stack([l0, l1, l2], -1)[ins]
            yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
            pos[yy, xx] = L @ P[t]
        break
np.savez_compressed(OUTP, pos=pos)
print('HEADPOS covered', int(np.isfinite(pos[..., 0]).sum()))
