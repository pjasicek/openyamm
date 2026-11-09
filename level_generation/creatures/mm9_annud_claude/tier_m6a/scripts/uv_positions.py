#!/usr/bin/env python3
"""Rest-pose position per body texel of the installed mm9_annud.glb (LOD0, one material: 0 "Annud" body, 1 "AnnudHead"), for the M6a tier masks.
Rasterises every LOD0 body triangle into UV space at the mask size and stores the bind-pose vertex position (glTF, Y up)
by barycentric interpolation, plus a coverage flag. Usage: uv_positions.py <glb> <out.npz> [size] [material]"""
import io, json, struct, sys
import numpy as np

src, out = sys.argv[1], sys.argv[2]
size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
material = int(sys.argv[4]) if len(sys.argv) > 4 else 0
b = open(src, 'rb').read()
jl = struct.unpack('<I', b[12:16])[0]
doc = json.loads(b[20:20 + jl])
binary = b[20 + jl + 8:]
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def acc(i):
    a = doc['accessors'][i]; bv = doc['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']]); n = NC[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', dt.itemsize * n)
    raw = np.frombuffer(binary, dtype=np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * n, offset=off)
    rows = np.lib.stride_tricks.as_strided(raw, (a['count'], dt.itemsize * n), (stride, 1))
    return np.frombuffer(rows.copy().tobytes(), dtype=dt).reshape(a['count'], n).astype(np.float64)


prim = next(p for p in doc['meshes'][0]['primitives'] if p['material'] == material)
pos = acc(prim['attributes']['POSITION']); uv = acc(prim['attributes']['TEXCOORD_0'])
idx = acc(prim['indices']).astype(np.int64).reshape(-1, 3)
P = np.zeros((size, size, 3)); C = np.zeros((size, size), bool)
px = uv * size - 0.5
for t in idx:
    (x0, y0), (x1, y1), (x2, y2) = px[t]
    xmin, xmax = int(np.floor(min(x0, x1, x2))), int(np.ceil(max(x0, x1, x2)))
    ymin, ymax = int(np.floor(min(y0, y1, y2))), int(np.ceil(max(y0, y1, y2)))
    xmin, ymin = max(xmin, 0), max(ymin, 0); xmax, ymax = min(xmax, size - 1), min(ymax, size - 1)
    if xmax < xmin or ymax < ymin:
        continue
    gx, gy = np.meshgrid(np.arange(xmin, xmax + 1), np.arange(ymin, ymax + 1))
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(d) < 1e-12:
        continue
    l0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / d
    l1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / d
    l2 = 1 - l0 - l1
    inside = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
    if not inside.any():
        continue
    p = l0[..., None] * pos[t[0]] + l1[..., None] * pos[t[1]] + l2[..., None] * pos[t[2]]
    P[gy[inside], gx[inside]] = p[inside]; C[gy[inside], gx[inside]] = True
np.savez_compressed(out, pos=P.astype(np.float32), covered=C)
print('UV_POSITIONS', out, size, 'triangles', len(idx), 'covered', round(C.mean(), 3),
      'y range', np.round(pos[:, 1].min(), 3), np.round(pos[:, 1].max(), 3))
