"""PartUV study: is the island margin really there? Rasterises a measurement GLB's LOD0 UVs per island (texel-centre,
like texture_quality.py) at 2048 and counts texels that have a texel of another island within 1 / 2 / 3 texels
(Chebyshev distance), i.e. where bilinear sampling or mips would mix neighbours at a 2 px margin.

  partuv_gap.py <glb> [material=<substring>]   -> one JSON line
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import texture_quality as tq  # noqa: E402

glb = sys.argv[1]
mat = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('material=')), None)
doc, binary = tq.read_glb(glb)
pos, uvs = [], []
for prim in doc['meshes'][0]['primitives']:
    name = doc['materials'][prim['material']].get('name', '')
    if mat and mat not in name:
        continue
    idx = tq.accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
    pos.append(tq.accessor(doc, binary, prim['attributes']['POSITION'])[idx])
    uvs.append(tq.accessor(doc, binary, prim['attributes']['TEXCOORD_0'])[idx])
pos, uv = np.concatenate(pos), np.concatenate(uvs)
island = np.unique(tq.islands(uv, pos), return_inverse=True)[1] + 1
size = 2048
label = np.zeros((size, size), np.int32)
for t, lab in zip(uv * size, island):
    x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
    x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), size)
    if x1 <= x0 or y1 <= y0:
        continue
    gy, gx = np.mgrid[y0:y1, x0:x1] + 0.5
    a, b, c = t
    w0 = (b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])
    w1 = (c[0] - b[0]) * (gy - b[1]) - (c[1] - b[1]) * (gx - b[0])
    w2 = (a[0] - c[0]) * (gy - c[1]) - (a[1] - c[1]) * (gx - c[0])
    inside = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
    label[y0:y1, x0:x1][inside] = lab
result = {'glb': os.path.basename(glb)}
for r in (1, 2, 3):
    bad = np.zeros_like(label, bool)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx == 0 and dy == 0:
                continue
            shifted = np.roll(np.roll(label, dy, 0), dx, 1)
            bad |= (label > 0) & (shifted > 0) & (shifted != label)
    result[f'texels_within_{r}'] = int(bad.sum())
print(json.dumps(result))
