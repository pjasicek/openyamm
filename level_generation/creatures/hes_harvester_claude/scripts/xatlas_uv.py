#!/usr/bin/env python3
"""UV atlas with xatlas (run in work/xatlas_venv: `python3 -m venv work/xatlas_venv && work/xatlas_venv/bin/pip
install xatlas==0.0.11 numpy`). Reads <in.npz> (positions float32 Nx3, triangles int32 Mx3), writes <out.npz> with
`uv` (Mx3x2, per triangle corner, v up) for the same triangle order. Packed at RES with
PADDING texels (of the atlas's own size, a little over 2048), rotated, bilinear-safe. Args: <in.npz> <out.npz>"""
import sys

import numpy as np
import xatlas

RES = 2048
PADDING = 5

data = np.load(sys.argv[1])
pos, tri = data['positions'].astype(np.float32), data['triangles'].astype(np.uint32)
atlas = xatlas.Atlas()
atlas.add_mesh(pos, tri)
chart = xatlas.ChartOptions()
chart.max_cost = 16.0                                 # a little larger charts (1 470 instead of 1 646)
chart.normal_deviation_weight = 1.0
pack = xatlas.PackOptions()
pack.resolution = RES
pack.padding = PADDING
pack.bilinear = True
pack.rotate_charts = True
pack.bruteForce = False                               # brute force packs tighter but not square (anisotropic)
atlas.generate(chart, pack)
vmap, idx, uvs = atlas[0]
assert len(idx) == len(tri)
corner_uv = uvs[idx]                                  # M x 3 x 2, xatlas v down from the top? -> flip below
# xatlas normalises uv to 0..1 with v growing with the image row; Blender v grows upward
corner_uv[..., 1] = 1.0 - corner_uv[..., 1]
# sanity: every triangle keeps its original vertex positions
assert np.allclose(pos[vmap[idx]], pos[tri])
area = np.abs((corner_uv[:, 1, 0] - corner_uv[:, 0, 0]) * (corner_uv[:, 2, 1] - corner_uv[:, 0, 1])
              - (corner_uv[:, 2, 0] - corner_uv[:, 0, 0]) * (corner_uv[:, 1, 1] - corner_uv[:, 0, 1])) / 2
assert atlas.atlas_count == 1 and abs(atlas.width - atlas.height) <= 0.01 * atlas.width, (atlas.width, atlas.height)
print('XATLAS charts', atlas.chart_count, 'coverage', round(float(area.sum()), 3), 'size', atlas.width, atlas.height)
np.savez(sys.argv[2], uv=corner_uv.astype(np.float32))
