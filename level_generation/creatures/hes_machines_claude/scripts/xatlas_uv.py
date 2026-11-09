#!/usr/bin/env python3
"""xatlas charts for a triangle mesh (run with a Python that has xatlas, e.g. LOD_REPAIR_PYTHON).
Reads <in.npz> (co: Vx3 float, tri: Tx3 int, nrm: Vx3 optional); writes <out.npz> with uv: Tx3x2 (per corner, v up)
and charts: chart count. Larger charts than Smart UV on thin organic parts, so a retexture paints whole surfaces.
Usage: xatlas_uv.py <in.npz> <out.npz> <resolution>"""
import sys

import numpy as np
import xatlas

src, dst, res = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = np.load(src)
atlas = xatlas.Atlas()
atlas.add_mesh(d['co'].astype(np.float32), d['tri'].astype(np.uint32))
chart = xatlas.ChartOptions()
chart.max_cost = 4.0                 # allow more stretch per chart than the default (2): fewer, larger charts
chart.normal_deviation_weight = 1.0
chart.max_iterations = 4
pack = xatlas.PackOptions()
pack.resolution = res
pack.padding = 6
pack.bilinear = True
pack.blockAlign = True
atlas.generate(chart, pack)
vmap, idx, uvs = atlas[0]
assert len(idx) == len(d['tri'])
print('XATLAS charts', atlas.chart_count, 'atlas', atlas.width, atlas.height, 'utilisation',
      round(float(np.mean(getattr(atlas, 'utilization', [0]))), 3))
np.savez(dst, uv=uvs[idx], charts=atlas.chart_count)
