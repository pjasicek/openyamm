#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Verhoffin Ruins: eye-level views through every room type, in MM9 (LithTech)
coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_verhoffinruins/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_verhoffinruins/make_tour.py <name> --original    # same views, old map

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original. One storey: the ruins' floor is at -128 LT (query -100); the crevasse
under the middle is at about -320 (query -250).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
F, WATER = -100, -150
VIEWS = {
    # by hand: the arrival, the scripted objects and traps, the crevasse
    "a01_start_stair": (-480, -2331, -480, -2000, F),
    "a02_bust_corridor": (-700, -2112, -1400, -2112, F),
    "a03_falling_door": (-300, -1976, -500, -1976, F),
    "a04_bolted_door": (-1760, -1550, -1760, -1800, F),
    "a05_pentagram": (-1550, -1456, -1840, -1456, F),
    "a06_torture_chamber": (-2000, -1456, -2700, -1456, F),
    "a07_capstone_block": (-2620, -1300, -2728, -1460, F),
    "a08_paddle_pit": (-2150, -1456, -2450, -1456, F),
    "a09_saw_corridor": (-1770, -560, -1770, -1000, F),
    "a10_water_trap_room": (150, -350, 150, -1000, F),
    "a11_door5": (-120, 120, -300, 190, F),
    "a12_book": (-140, 180, -140, 0, F),
    "a13_key_table": (1300, -2100, 1200, -2336, F),
    "a14_crevasse_ramp": (-1600, -600, -1000, -1000, WATER),
    "a15_crevasse_south": (0, -1350, 400, -1700, F, -10),
}
WATER_TEXTURES = ("WATEQOBX0Z", "INVIZVJN7N")


def room_views() -> dict:
    """Two views per room of the built map (work/runtime): between the two floor faces farthest apart that see each
    other at eye height, each looking at the other, where the party fits (Beethoven's make_tour), so every room is
    seen. Water faces and invisible faces are not floors to stand on."""
    import numpy as np
    sys.path.insert(0, str(PROJECT.parents[2]))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime/verhoffinruins.blv")["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    rooms, a, e1, e2 = {}, [], [], []
    water = {f["texture_name"] for f in blv["faces"] if str(f["texture_name"]).upper().startswith(("WATE", "OCEA"))}
    for face in blv["faces"]:
        if face["is_portal"]:
            continue
        points = vertices[face["vertex_indices"]]
        if face["texture_name"] not in ("INVIZVJN7N",):
            for i in range(1, len(points) - 1):
                a.append(points[0]); e1.append(points[i] - points[0]); e2.append(points[i + 1] - points[0])
        if face["texture_name"] in WATER_TEXTURES or face["texture_name"] in water:
            continue
        normal = sum(np.cross(points[i] - points[0], points[i + 1] - points[0]) for i in range(1, len(points) - 1))
        length = np.linalg.norm(normal)
        if length > 1 and normal[2] / length > 0.9 and -600 < points[:, 2].mean() < 0:   # not the bed under the water, not the roofs
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
                if gap < 250 or (best is not None and gap <= best[0]) or hit(p, (q - p) / np.linalg.norm(q - p),
                                                                            np.linalg.norm(q - p)):
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


# Feature checks: the pentagram's flames (standing on the centre starts the puzzle), the torture chamber's sconces from
# the side and the front (flame cards), the stained glass, the electrified pit.
FEATURE_VIEWS = {
    "f01_pentacenter": (-1712, -1456, -1840, -1456, F),
    "f02_pentagram_flames": (-1560, -1300, -1712, -1456, F, -12),
    "f03_pentagram_flames_side": (-1712, -1250, -1712, -1456, F, -12),
    "f04_sconce_side": (-2560, -1250, -2676, -1460, F),
    "f05_sconce_front": (-2560, -1460, -2676, -1460, F),
    "f06_stained_glass": (-2450, -1030, -2552, -1030, F),
    "f07_pit": (-2280, -1300, -2440, -1456, F, -20),
}


# The lighting compare (MM9 original | native unbaked | native baked): one view per room kind.
LIGHTING_VIEWS = ["a01_start_stair", "a02_bust_corridor", "a05_pentagram", "a06_torture_chamber", "a09_saw_corridor",
                  "a10_water_trap_room", "a13_key_table", "a14_crevasse_ramp", "a15_crevasse_south"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else {**VIEWS, **room_views()}
    views = FEATURE_VIEWS if name.startswith("features") else views
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
