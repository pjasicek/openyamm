#!/usr/bin/env python3
"""Re-pad the head set's gutters from the islands themselves (mm9_markel, 2026-11-02): a light U-shaped line across the back of the
head (review/hair_r4.png) was the hair chart's border reading the flat pink padding of a neighbouring neck-skin island through
bilinear filtering and mips. Every texel not covered by a head-primitive triangle (work/pm5_body_tex.glb, rasterised with a 0.5 px
tolerance) within PAD px of one takes the colour of the nearest covered texel. Runs last on textures/pm5_tp_head_basecolor.png
(after hand_clean.py). Usage (project folder): pad_head.py [pad 8]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from pygltflib import GLTF2
PAD = int(sys.argv[1]) if len(sys.argv) > 1 else 8
T = 'textures/pm5_tp_head_basecolor.png'
img = np.asarray(Image.open(T).convert('RGB')).copy()
N = img.shape[0]
g = GLTF2().load('work/pm5_body_tex.glb'); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('PeasantM5Head'))
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64); I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
cov = np.zeros((N, N), bool)
for tri in I:
    uv = UV[tri] * N
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0 - 1, 0), min(x1 + 1, N)), np.arange(max(y0 - 1, 0), min(y1 + 1, N)))
    if xs.size == 0:
        continue
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = uv; m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T
    # 0.5 px tolerance in barycentric terms, scaled by the triangle's size
    tol = 0.5 / max(np.sqrt(abs(np.linalg.det(m))), 1.0)
    ok = (l >= -tol).all(1) & (l.sum(1) <= 1 + tol)
    cov[q[ok, 1].astype(int), q[ok, 0].astype(int)] = True
dist, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True)
gut = (~cov) & (dist <= PAD)
img[gut] = img[iy[gut], ix[gut]]
Image.fromarray(img).save(T)
print('PAD_HEAD covered', int(cov.sum()), 'gutter texels re-padded', int(gut.sum()))
