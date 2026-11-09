#!/usr/bin/env python3
"""xatlas UV atlas for a shell (run with work/venv/bin/python). <in.npz> (positions, triangles) -> <out.npz> with
`uv` (Mx3x2 per triangle corner, v up), packed for RES with PADDING texels."""
import sys
import numpy as np
import xatlas
RES, PADDING = int(sys.argv[3]) if len(sys.argv) > 3 else 2048, 6
d = np.load(sys.argv[1])
pos, tri = d['positions'].astype(np.float32), d['triangles'].astype(np.uint32)
atlas = xatlas.Atlas(); atlas.add_mesh(pos, tri)
chart = xatlas.ChartOptions(); chart.max_cost = 8.0; chart.normal_deviation_weight = 2.0
pack = xatlas.PackOptions(); pack.resolution = RES; pack.padding = PADDING; pack.bilinear = True
pack.rotate_charts = True
atlas.generate(chart, pack)
vmap, idx, uvs = atlas[0]
assert len(idx) == len(tri)
uv = uvs[idx].copy()
uv[..., 1] = 1 - uv[..., 1]
np.savez(sys.argv[2], uv=uv.astype(np.float32))
print('UV charts', atlas.chart_count, 'atlas', atlas.width, atlas.height, 'utilization', atlas.utilization)
