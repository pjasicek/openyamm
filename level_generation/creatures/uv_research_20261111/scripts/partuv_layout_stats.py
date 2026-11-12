"""PartUV study: layout measures texture_quality.py does not report.

  partuv_layout_stats.py <mesh.npz> <uv.npz | -> [size=2048]   ('-': the mesh npz's own uv, i.e. the current layout)
seam_length: total 3D length of mesh edges cut in UV (boundary of an island, or the two faces' UVs differ at an end),
  in units of the square root of the surface area (scale free; a sphere cut once around is about 3.5);
open_edges: mesh boundary edges (not seams; reported apart); zero_area: triangles whose UV area is under 0.01 texel at
`size` while their 3D area is not zero; flipped: triangles whose UV winding is against their island's majority.
Prints one JSON line.
"""
import json
import sys
from collections import defaultdict

import numpy as np

mesh = np.load(sys.argv[1])
uv = mesh['uv'] if sys.argv[2] == '-' else np.load(sys.argv[2])['uv']
size = int(dict(a.split('=', 1) for a in sys.argv[3:]).get('size', 2048))
pos, tri = mesh['pos'], mesh['tri']
p3 = pos[tri]
area3 = np.linalg.norm(np.cross(p3[:, 1] - p3[:, 0], p3[:, 2] - p3[:, 0]), axis=1) / 2
px = uv * size
signed = ((px[:, 1, 0] - px[:, 0, 0]) * (px[:, 2, 1] - px[:, 0, 1])
          - (px[:, 2, 0] - px[:, 0, 0]) * (px[:, 1, 1] - px[:, 0, 1])) / 2
edges = defaultdict(list)
for f, t in enumerate(tri):
    for k in range(3):
        a, b = int(t[k]), int(t[(k + 1) % 3])
        edges[(min(a, b), max(a, b))].append((f, k, (k + 1) % 3) if a < b else (f, (k + 1) % 3, k))
seam = open_len = 0.0
parent = np.arange(len(tri))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for (a, b), uses in edges.items():
    length = float(np.linalg.norm(pos[a] - pos[b]))
    if len(uses) == 1:
        open_len += length
        continue
    (f0, a0, b0), (f1, a1, b1) = uses[0], uses[1]
    same = (np.abs(uv[f0, a0] - uv[f1, a1]).max() < 1e-6 and np.abs(uv[f0, b0] - uv[f1, b1]).max() < 1e-6
            and len(uses) == 2)
    if same:
        ra, rb = find(f0), find(f1)
        if ra != rb:
            parent[ra] = rb
    else:
        seam += length
island = np.array([find(i) for i in range(len(tri))])
flipped = 0
for i in np.unique(island):
    s = signed[island == i]
    flipped += int(((np.sign(s) != np.sign(s.sum())) & (np.abs(s) > 1e-9)).sum())
norm = float(np.sqrt(area3.sum()))
print(json.dumps({'seam_length': round(seam / norm, 2), 'open_edge_length': round(open_len / norm, 2),
                  'islands': int(len(np.unique(island))),
                  'zero_area': int(((np.abs(signed) < 0.01) & (area3 > 1e-12)).sum()), 'flipped': flipped}))
