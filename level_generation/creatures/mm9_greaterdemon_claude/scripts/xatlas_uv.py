#!/usr/bin/env python3
"""xatlas charts for a triangle mesh (after hes_machines_claude/scripts/xatlas_uv.py; run with a Python that has
xatlas, XATLAS_PYTHON). Reads <in.npz> (co: Vx3, tri: Tx3); writes <out.npz> with uv: Tx3x2 (per corner, v up) and
the chart count. Larger charts than Smart UV, so a Meshy retexture paints whole surfaces instead of a mosaic.
Square texels on one square page: texels_per_unit is searched (bisection) for the largest value whose pack still fits
one <resolution> page, and the UVs are divided by that resolution (xatlas otherwise normalises a non-square atlas
per axis, which stretches the texels).
Usage: xatlas_uv.py <in.npz> <out.npz> <resolution> [max_cost] [padding]"""
import sys

import numpy as np
import xatlas

src, dst, res = sys.argv[1], sys.argv[2], int(sys.argv[3])
cost = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
padding = int(sys.argv[5]) if len(sys.argv) > 5 else 8
d = np.load(src)
co, tri = d['co'].astype(np.float32), d['tri'].astype(np.uint32)


def run(tpu):
    atlas = xatlas.Atlas()
    atlas.add_mesh(co, tri)
    chart = xatlas.ChartOptions()
    chart.max_cost = cost
    chart.normal_deviation_weight = 1.0
    chart.max_iterations = 4
    pack = xatlas.PackOptions()
    pack.resolution = res
    pack.padding = padding
    pack.bilinear = True
    pack.blockAlign = False
    pack.bruteForce = True
    pack.texels_per_unit = tpu
    atlas.generate(chart, pack)
    return atlas


# surface area -> a first guess of the texels per unit that fills about 60 % of the page
v = co[tri]
area = 0.5 * np.linalg.norm(np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]), axis=1).sum()
lo, hi = 0.0, float(np.sqrt(res * res * 0.95 / area))
best = None
for _ in range(9):
    mid = (lo + hi) / 2 if lo else hi * 0.75
    a = run(mid)
    fits = a.atlas_count == 1 and a.width <= res and a.height <= res
    if fits:
        lo, best = mid, a
    else:
        hi = mid
    if lo and hi - lo < 0.01 * hi:
        break
atlas = best
vmap, idx, uvs = atlas[0]
assert len(idx) == len(tri)
uv = uvs[idx] * np.array([atlas.width, atlas.height]) / res
print('XATLAS charts', atlas.chart_count, 'page', atlas.width, atlas.height, 'of', res, 'texels/unit', round(lo, 1),
      'utilisation', round(float(np.mean(atlas.utilization)), 3))
np.savez(dst, uv=uv, charts=atlas.chart_count)
