#!/usr/bin/env python3
"""
Zones for hue_vs_lightmaps.py / relight_fit.py when a map has none: a k-d split of MM9's lightmapped DAT polygons by
area into N boxes that tile the map (MM9 units, y up). Prints a ZONES dict to paste into the project's hue_zones.py,
with each box's polygon count, area share and mean lightmap RGB (0-255).

    python3 level_generation/projects/mm9r_common/relight_zones.py MAP.dat [N]
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402


def area(points):
    total = np.zeros(3)
    for i in range(len(points)):
        total += np.cross(points[i], points[(i + 1) % len(points)])
    return float(np.linalg.norm(total) / 2)


def main() -> int:
    world = read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS" / sys.argv[1])
    leaves_wanted = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    model = next(m for m in world.world_models if m.name == "PhysicsBSP")
    centres, areas, colours = [], [], []
    for poly in model.polies:
        pixels = getattr(poly, "lightmap_pixels_bgra", None)
        if not pixels:
            continue
        value = np.array(pixels, np.int64)
        rgb = np.stack([(value >> 16) & 255, (value >> 8) & 255, value & 255], 1).astype(float).mean(0)
        pts = np.array([model.points[d.vertex_index] for d in poly.disk_verts], float)
        centres.append(np.array(poly.center, float))
        areas.append(area(pts) if len(pts) >= 3 else 1.0)
        colours.append(rgb)
    centres, areas, colours = np.array(centres), np.array(areas), np.array(colours)
    low, high = centres.min(0) - 64, centres.max(0) + 64
    leaves = [(low, high, np.arange(len(centres)))]
    while len(leaves) < leaves_wanted:
        leaves.sort(key=lambda leaf: -areas[leaf[2]].sum())
        lo, hi, idx = leaves.pop(0)
        spread = centres[idx].max(0) - centres[idx].min(0)
        spread[1] *= 2.5  # storeys: prefer a horizontal cut when the box is tall enough
        axis = int(np.argmax(spread))
        order = idx[np.argsort(centres[idx, axis])]
        cum = np.cumsum(areas[order])
        k = int(np.searchsorted(cum, cum[-1] / 2))
        cut = float(round((centres[order[k], axis] + centres[order[min(k + 1, len(order) - 1)], axis]) / 2))
        left, right = order[centres[order, axis] <= cut], order[centres[order, axis] > cut]
        if not len(left) or not len(right):
            leaves.append((lo, hi, idx))
            break
        hi_l, lo_r = hi.copy(), lo.copy()
        hi_l[axis], lo_r[axis] = cut, cut
        leaves += [(lo, hi_l, left), (lo_r, hi, right)]
    leaves.sort(key=lambda leaf: (round(leaf[0][1], -2), leaf[0][0], leaf[0][2]))
    total = areas.sum()
    print("ZONES = {")
    for i, (lo, hi, idx) in enumerate(leaves):
        rgb = (colours[idx] * areas[idx, None]).sum(0) / areas[idx].sum()
        box = ", ".join(str(int(round(v))) for v in (*lo, *hi))
        print(f'    "z{i + 1:02d}": ({box}),  # {len(idx)} polys, {areas[idx].sum() / total:.0%} of the area, '
              f'MM9 RGB {np.round(rgb).astype(int).tolist()}')
    print("}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
