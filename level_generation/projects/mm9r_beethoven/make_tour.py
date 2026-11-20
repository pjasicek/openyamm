#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Beethoven: eye-level views through every room type of its three storeys, in
MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_beethoven/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_beethoven/make_tour.py <name> --original    # same views, old map

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT.parents[2]))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
SEWER, PLANKS, CATACOMB, BATHS, LOWER, MAZE = 100, 300, -600, -500, -1100, -1300
VIEWS = {
    # by hand: the arrivals, the shaft, the scripted objects
    "a01_south_arrival": (-3830, 212, -3400, 212, PLANKS),
    "a02_west_arrival": (-6420, 5120, -6000, 5120, PLANKS),
    "a03_grate_landing": (-672, 1120, -672, 500, SEWER),
    "a04_east_door": (1600, 6864, 1790, 6864, SEWER),
    "a05_shaft_rim": (-672, -700, -672, -930, SEWER, -18),
    "a06_hub": (-672, -480, -672, -800, SEWER),
    "a07_caldarium": (-1536, 2200, -1536, 3400, BATHS),
    "a08_well": (-4700, -9632, -4992, -9632, MAZE),
    "a09_manuscript": (-3330, -2700, -3330, -3250, LOWER),
    "a10_great_door": (-5000, -7300, -5000, -7440, -1000),
}


def room_views() -> dict:
    """Two views per room of the built map (work/runtime): between the two floor faces farthest apart that see each other
    at eye height, each looking at the other, where the party fits (not in the low culverts), so every room is seen."""
    import numpy as np
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime/beethoven.blv")["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    rooms, a, e1, e2 = {}, [], [], []
    for face in blv["faces"]:
        if face["is_portal"]:
            continue
        points = vertices[face["vertex_indices"]]
        if face["texture_name"] not in ("INVIZVJN7N", "WEB32N735S", "FIRE6YTKLQ"):
            for i in range(1, len(points) - 1):
                a.append(points[0]); e1.append(points[i] - points[0]); e2.append(points[i + 1] - points[0])
        if face["texture_name"] in ("INVIZVJN7N", "SLIM91P4YN", "WATE27JPCX", "WATENZD35K"):
            continue
        normal = sum(np.cross(points[i] - points[0], points[i + 1] - points[0]) for i in range(1, len(points) - 1))
        length = np.linalg.norm(normal)
        if length > 1 and normal[2] / length > 0.9:
            rooms.setdefault(face["room_number"], []).append((length / 2, points.mean(0)))
    a, e1, e2 = np.array(a), np.array(e1), np.array(e2)

    def hit(origin, direction, reach):
        p = np.cross(direction, e2)
        det = (e1 * p).sum(1)
        with np.errstate(divide="ignore", invalid="ignore"):
            inv = 1.0 / det
            s = origin - a
            u = (s * p).sum(1) * inv
            q = np.cross(s, e1)
            v = (direction * q).sum(1) * inv
            t = (e2 * q).sum(1) * inv
        return bool(((np.abs(det) > 1e-6) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1.0) & (t < reach)).any())

    views = {}
    for room, floors in sorted(rooms.items()):
        floors.sort(key=lambda f: -f[0])
        centres = np.array([f[1] for f in floors[:14]])
        best = None
        for i in range(len(centres)):
            for j in range(i + 1, len(centres)):
                p, q = centres[i] + [0, 0, 160], centres[j] + [0, 0, 160]
                gap = np.linalg.norm(q[:2] - p[:2])
                if gap < 300 or (best is not None and gap <= best[0]) or hit(p, (q - p) / np.linalg.norm(q - p), np.linalg.norm(q - p)):
                    continue
                if hit(p, np.array([0, 0, 1.0]), 30.0) or hit(q, np.array([0, 0, 1.0]), 30.0):
                    continue
                best = (gap, centres[i], centres[j])
        if best is None:
            continue
        p, q = best[1] / 2.56, best[2] / 2.56
        views[f"r{room:02d}_a"] = (round(p[0]), round(p[1]), round(q[0]), round(q[1]), round(p[2] + 30))
        views[f"r{room:02d}_b"] = (round(q[0]), round(q[1]), round(p[0]), round(p[1]), round(q[2] + 30))
    return views


# The lighting compare (MM9 original | native unbaked | native baked): one view per room kind.
# From lighting_v05 (the re-light against the DAT lightmaps, 2026-10-30): every arrival and every zone of hue_zones.py.
LIGHTING_VIEWS = ["a01_south_arrival", "a02_west_arrival", "a03_grate_landing", "a04_east_door", "a05_shaft_rim",
                  "a06_hub", "a07_caldarium", "a08_well", "a09_manuscript", "a10_great_door", "r01_b", "r02_b",
                  "r03_a", "r05_a", "r07_a", "r12_a", "r17_a", "r19_a", "r21_a", "r28_a", "r29_a", "r35_a", "r38_a"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {**VIEWS, **room_views()}
    if name.startswith("lighting"):
        views = {k: views[k] for k in LIGHTING_VIEWS}
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
