"""Ground height of the remade isle (read only): bilinear over the remade ODM's 128x128 height map (512-unit cells,
32 units per step, x = (column - 64) * 512, y = (64 - row) * 512)."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
REMADE = REPO / 'output/mm9_rework/assets_dev/worlds/mm9/maps/isleofashes.odm'
_heights = None


def heights():
    global _heights
    if _heights is None:
        from util.map_export import parse_odm_file
        payload = parse_odm_file(REMADE)['payload']
        _heights = np.array(payload['height_map'], float).reshape(128, 128) * 32.0
    return _heights


def ground(x, y):
    h = heights()
    col = x / 512.0 + 64.0
    row = 64.0 - y / 512.0
    c0, r0 = int(np.floor(col)), int(np.floor(row))
    fc, fr = col - c0, row - r0
    c0, r0 = np.clip(c0, 0, 126), np.clip(r0, 0, 126)
    return float(h[r0, c0] * (1 - fc) * (1 - fr) + h[r0, c0 + 1] * fc * (1 - fr)
                 + h[r0 + 1, c0] * (1 - fc) * fr + h[r0 + 1, c0 + 1] * fc * fr)


_terrain = None


def terrain_top(x, y):
    """The MM9 terrain's own top surface at (x, y) in the remade frame (the terrain-textured world-model polygons,
    as the conversion reads them: mm9r_isleofashes/convert.py load_terrain, imported read only), or None."""
    global _terrain
    if _terrain is None:
        sys.path.insert(0, str(REPO / 'level_generation/projects/mm9r_isleofashes'))
        import convert  # noqa: E402
        tx, ty, tz, *_ = convert.load_terrain()
        _terrain = (tx, ty, tz)
    tx, ty, tz = _terrain
    inside = (tx.min(1) <= x) & (tx.max(1) >= x) & (ty.min(1) <= y) & (ty.max(1) >= y)
    best = None
    for i in np.nonzero(inside)[0]:
        (x0, x1, x2), (y0, y1, y2), (z0, z1, z2) = tx[i], ty[i], tz[i]
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(d) < 1e-9:
            continue
        a = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d
        b = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d
        c = 1 - a - b
        if min(a, b, c) < -1e-6:
            continue
        h = a * z0 + b * z1 + c * z2
        best = h if best is None else max(best, h)
    return None if best is None else float(best)
