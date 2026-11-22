#!/usr/bin/env python3
"""Measure an installed-to-be stone hand GLB in game units at a binding height (448): palm surface heights around the
palm centre (vertical rays), base radius, extents. measure.py <glb> [height] [out.json]"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb  # noqa: E402
g = Glb(sys.argv[1]); target = float(sys.argv[2]) if len(sys.argv) > 2 else 448.0
p = g.json['meshes'][0]['primitives'][0]
v = g.accessor(p['attributes']['POSITION']).astype(float); f = g.accessor(p['indices']).astype(int).reshape(-1, 3)
lo, hi = v.min(0), v.max(0); k = target / (hi[1] - lo[1])
a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
def top(x, z):
    v0 = c - a; v1 = b - a; v2 = np.array([x, 0, z]) - a
    d00 = v0[:, 0] ** 2 + v0[:, 2] ** 2; d01 = v0[:, 0] * v1[:, 0] + v0[:, 2] * v1[:, 2]; d11 = v1[:, 0] ** 2 + v1[:, 2] ** 2
    d20 = v2[:, 0] * v0[:, 0] + v2[:, 2] * v0[:, 2]; d21 = v2[:, 0] * v1[:, 0] + v2[:, 2] * v1[:, 2]
    den = d00 * d11 - d01 * d01; den[den == 0] = 1e-12
    u = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    ok = (u >= 0) & (w >= 0) & (u + w <= 1)
    y = a[:, 1] + u * (c[:, 1] - a[:, 1]) + w * (b[:, 1] - a[:, 1])
    return float(y[ok].max()) if ok.any() else None
grid = {}
for dx in (-0.08, -0.04, 0, 0.04, 0.08):
    for dz in (-0.08, -0.04, 0, 0.04, 0.08):
        t = top(dx, dz); grid[f'{dx:+.2f},{dz:+.2f}'] = None if t is None else round(t * k, 1)
base = v[v[:, 1] < 0.02]
out = {'units_per_model_m': round(k, 2), 'height': target, 'palm_centre_z': round(top(0, 0) * k, 1),
       'palm_grid_units (x,z model m; +z = fingers/front)': grid,
       'base_radius': round(float(np.sqrt(base[:, 0] ** 2 + base[:, 2] ** 2).max()) * k, 1),
       'extent_x': [round(lo[0] * k, 1), round(hi[0] * k, 1)], 'extent_front_back': [round(lo[2] * k, 1), round(hi[2] * k, 1)],
       'triangles_lod0': len(f)}
print(json.dumps(out, indent=1))
if len(sys.argv) > 3:
    json.dump(out, open(sys.argv[3], 'w'), indent=1)
