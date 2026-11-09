#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Ta'Sar Academy: eye-level views through every room type, in MM9 (LithTech)
coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_tasaracademy/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_tasaracademy/make_tour.py <name> --original    # same views, old map

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original. Storeys (LT): the halls at 0 (query 100), the south wing at 128-136 (query
300), the library tower's floors at 208 and 416 (queries 300 and 500), the spike pit and its tunnel -256 to 0
(query -50).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
F, S, G, B, P = 100, 300, 300, 500, -50
VIEWS = {
    "a01_start_hall": (1024, 240, 1024, -150, F),
    "a02_entry_west_room": (560, 0, 100, -100, F),
    "a03_entry_east_room": (1500, 0, 2050, -150, F),
    "a04_chalices": (1580, 8, 1800, 8, F, -12),
    "a05_arena_north": (1120, -580, 1120, -1400, F),
    "a06_arena_south": (1120, -1650, 1120, -800, F),
    "a07_arena_mouth": (450, -850, 1000, -850, F),
    "a08_west_corridor": (350, -1010, -900, -1010, F),
    "a09_west_dormitory": (-150, -650, -900, -700, F),
    "a10_east_corridor": (1920, -1620, 3200, -1620, F),
    "a11_dorm_cubicles": (2400, -1880, 2800, -1950, F),
    "a12_switch_corridor": (1920, -200, 1920, -900, F),
    "a13_secret_door0": (1900, -500, 2060, -552, F),
    "a14_store_room": (2700, -160, 2980, -80, F),
    "a15_south_corridor": (1300, -1950, 1300, -2600, F),
    "a16_olive_hall": (1650, -2400, 1900, -3200, F),
    "a17_library_corridor": (1300, -2912, 700, -2912, F),
    "a18_library_floor": (250, -2700, 600, -3000, F),
    "a19_start_table": (480, -3200, 480, -3058, F, -15),
    "a20_library_gallery": (300, -2560, 700, -2560, G),
    "a21_tower_bridge": (200, -2880, 800, -2880, B),
    "a22_ladder_foot": (496, -2760, 496, -2900, F, 20),
    "a23_pit_tower": (496, -2350, 496, -1950, F),
    "a24_podium_trap": (496, -2150, 496, -1912, F, -15),
    "a25_pit_tunnel": (40, -2780, 40, -2100, 100),
    "a26_door_crack": (300, -2912, 104, -2912, F),
    "a27_south_hall": (496, -3700, 1100, -4100, S),
    "a28_bookcase": (150, -3696, -16, -3696, S),
    "a29_rules_room": (-180, -3700, -366, -3700, S),
    "a30_behind_library_door": (496, -3420, 496, -3640, B),
    "a31_east_stair": (1960, -3330, 1960, -3700, 200),
    "a32_octagon_hall": (2000, -3750, 2400, -4100, S),
    "a33_chest_room": (2700, -4125, 2755, -4040, S),
    "a34_barn": (1700, -4560, 2350, -4600, S),
}


def room_views() -> dict:
    """Two views per room of the built map (work/runtime): between the two floor faces farthest apart that see each
    other at eye height, each looking at the other, where the party fits (Beethoven's make_tour)."""
    import numpy as np
    sys.path.insert(0, str(PROJECT.parents[2]))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime/tasaracademy.blv")["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    rooms, a, e1, e2 = {}, [], [], []
    for face in blv["faces"]:
        if face["is_portal"]:
            continue
        points = vertices[face["vertex_indices"]]
        if face["texture_name"] not in ("INVIZVJN7N",):
            for i in range(1, len(points) - 1):
                a.append(points[0]); e1.append(points[i] - points[0]); e2.append(points[i + 1] - points[0])
        else:
            continue
        normal = sum(np.cross(points[i] - points[0], points[i + 1] - points[0]) for i in range(1, len(points) - 1))
        length = np.linalg.norm(normal)
        if length > 1 and normal[2] / length > 0.9 and length > 2 * 120 * 120:
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


# Feature checks: a brazier's flame card from the side and the front, the barn's pens through their gates, the
# arena's skylight and the library's lantern (sky04), the trap doors and the podium.
FEATURE_VIEWS = {
    "f01_brazier_side": (1232, 60, 1232, 160, F),
    "f02_brazier_front": (1140, 160, 1232, 160, F),
    "f03_pen_gates": (2000, -4560, 2000, -4780, S),
    "f04_arena_skylight": (1120, -1300, 1120, -1100, F, 40),
    "f05_library_lantern": (250, -2900, 496, -2900, B, 30),
    "f06_trap_doors": (496, -2250, 496, -2000, F, -25),
}


# The lighting compare (MM9 original | native unbaked | native baked): one view per room kind.
LIGHTING_VIEWS = ["a01_start_hall", "a04_chalices", "a05_arena_north", "a08_west_corridor", "a09_west_dormitory",
                  "a10_east_corridor", "a14_store_room", "a16_olive_hall", "a18_library_floor", "a20_library_gallery",
                  "a23_pit_tower", "a27_south_hall", "a29_rules_room", "a32_octagon_hall", "a34_barn"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else {**VIEWS, **room_views()}
    views = FEATURE_VIEWS if name.startswith("features") else views
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
