#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Thjorad Mine: eye-level views of the scripted places by hand and two views
per room of the built map (Beethoven's room_views), in MM9 (LithTech) coordinates, converted by the shared tour helper
(../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_thjoradmine/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_thjoradmine/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_thjoradmine/make_tour.py lighting<n> [--original]   # the lighting subset

The BLV keeps the old map's frame (no offset), so the --original tour uses the same positions and runs against
output/mm9_rework/assets_original.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT.parents[2]))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

SKIP_TEXTURES = ("INVIZVJN7N", "WATE27JPCX", "WATENZD35K", "PERCEPTION")
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    "a01_start": (1088, -1088, 1088, -600, -200),
    "a02_refinery": (-450, 0, 0, 0, 100),
    "a03_slag_machine": (-1060, 520, -1060, 380, 200),
    "a04_barwall1": (0, 1750, 0, 1536, 200),
    "a05_barwall0": (-768, 250, -768, 448, 700),
    "a06_cavein": (2500, 700, 2864, 976, -450),
    "a07_deep_pool": (2952, 1928, 2700, 1000, -1000),   # the pool's north rim (v01-v03: in the rock)
    "a08_hard_rock": (9150, -520, 9440, -520, -400),
    "a09_ebora": (10000, -700, 9600, -560, -400),
    "a10_gnoll_cages": (10250, -1872, 10528, -1830, -350),
    "a11_torch_barrels": (1800, -4950, 2150, -5150, -380),
    "a12_mine_cart": (3550, -5103, 3800, -5103, -420),
    "a13_valve": (3078, -4950, 3078, -5240, -420, -8),
    "a14_spiked_boards": (4140, -5700, 4140, -5880, -500),
}


def room_views() -> dict:
    """Two views per room of the built map (work/runtime): between the two floor faces farthest apart that see each other
    at eye height, each looking at the other, where the party fits (not in the low culverts), so every room is seen."""
    import numpy as np
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime/thjoradmine.blv")["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    rooms, a, e1, e2 = {}, [], [], []
    for face in blv["faces"]:
        if face["is_portal"]:
            continue
        points = vertices[face["vertex_indices"]]
        if face["texture_name"] not in SKIP_TEXTURES:
            for i in range(1, len(points) - 1):
                a.append(points[0]); e1.append(points[i] - points[0]); e2.append(points[i + 1] - points[0])
        if face["texture_name"] in SKIP_TEXTURES:
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


LIGHTING_VIEWS = ["a01_start", "a02_refinery", "a03_slag_machine", "a06_cavein", "a07_deep_pool", "a08_hard_rock",
                  "a10_gnoll_cages", "a11_torch_barrels", "a12_mine_cart"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    rooms = room_views()
    if "--all" not in sys.argv:
        rooms = {k: v for k, v in rooms.items() if k.endswith("_a")}
    views = {**VIEWS, **rooms}
    if name.startswith("lighting"):
        views = {k: views[k] for k in LIGHTING_VIEWS + sorted(k for k in rooms if k.endswith("_a"))[::3]}
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
