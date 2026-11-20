#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Yanmir's Fort: eye-level views through every room, in MM9 (LithTech)
coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_yanmirsfort/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_yanmirsfort/make_tour.py <name> --original    # same views, old map

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original. Room views come from the built map (two per room, Beethoven's make_tour);
feature views are set on the DAT objects they show.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project, Source  # noqa: E402

# Feature views: name -> (eye x, eye z, target x, target z, floor query y[, pitch]) LT, or an object to look at:
# name -> ("@<object>", dx, dz, query y[, pitch]): the eye at the object + (dx, dz), looking at it.
FEATURES = {
    "f01_start": (-3150, -960, -2400, -960, 300),
    "f02_entrance_corridor": (-2900, -960, -1300, -960, 300),
    "f03_yanmir": ("@Yanmir0", -900, 0, 300, 10),
    "f04_great_hall_south": (600, -1900, 600, -400, 300),
    "f05_great_hall_stairs": (600, -900, 600, 300, 300),
    "f06_trap_hall_north": (192, -2350, 192, -3700, 300),
    "f07_trap_hall_south": (192, -4200, 192, -2700, 300),
    "f08_support": (100, -4280, 48, -3984, -200, 10),
    "f09_basement": (192, -4250, 192, -3000, -300),
    "f10_spiral_stair": (128, -5300, 128, -5760, -200),
    "f11_cages_near": (2500, -2000, 2820, -2098, 300),
    "f12_key": ("@Yanmir'sKey", 0, -200, 400, -15),
    "f13_children_room": (6528, -900, 6528, -300, 300),
    "f14_teleporter": (6528, -300, 6528, 279, 300),
    "f15_pool": (-1900, -4300, -2600, -4300, 300),
    "f16_west_cave": (-1200, -4500, -2600, -4700, 300),
    "f17_secret_wall": ("@Secretdoor", 250, 0, 300),
    "f18_treasury": (1800, -8100, 1800, -8448, 300),
    "f19_throne_room": (0, 2400, 0, 3500, 700),
    "f20_east_cave": (5600, -5200, 5000, -6000, 300),
    "f21_exit_gate_west": (-3150, -960, -3415, -960, 300),
    "f22_torch_side": (1300, -1756, 1500, -1756, 300, 30),       # Torch4: the blue flame card from the side
    "f23_lamp": (1408, -5650, 1408, -5888, 300, 25),             # Lamp4: a hanging claw lamp's glowing orb
}

# The flame check (the brief: look at a flame from the side): Torch4's blue flame card from below and the side.
FLAME_VIEWS = {
    "g01_torch_side": (1250, -1756, 1500, -1756, 300, 48),
    "g02_torch_front": (1340, -1600, 1500, -1756, 300, 45),
    "g03_lamp": (1408, -5650, 1408, -5888, 300, 25),
}


# The lighting compare (MM9 original | native unbaked | native baked): one view per room kind.
LIGHTING_VIEWS = ["f01_start", "f02_entrance_corridor", "f04_great_hall_south", "f05_great_hall_stairs",
                  "f06_trap_hall_north", "f09_basement", "f11_cages_near", "f13_children_room", "f15_pool",
                  "f16_west_cave", "f18_treasury", "f19_throne_room", "f20_east_cave"]


def resolve(views: dict) -> dict:
    source = Source(Project.load(PROJECT, install=False))
    out = {}
    for name, view in views.items():
        if isinstance(view[0], str):
            target = view[0][1:]
            if target in source.models:
                pts = np.concatenate([p.points for p in source.polygons(target)])
                pos = (pts.min(0) + pts.max(0)) / 2
            else:
                pos = source.properties(target)["Pos"]
            out[name] = (pos[0] + view[1], pos[2] + view[2], pos[0], pos[2], *view[3:])
        else:
            out[name] = view
    return out


def room_views() -> dict:
    """Two views per room of the built map (work/runtime): between the two floor faces farthest apart that see each
    other at eye height, each looking at the other, where the party fits (Beethoven's make_tour)."""
    sys.path.insert(0, str(PROJECT.parents[2]))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime/yanmirsfort.blv")["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    rooms, a, e1, e2 = {}, [], [], []
    for face in blv["faces"]:
        if face["is_portal"]:
            continue
        points = vertices[face["vertex_indices"]]
        if face["texture_name"] in ("INVIZVJN7N",):
            continue
        for i in range(1, len(points) - 1):
            a.append(points[0]); e1.append(points[i] - points[0]); e2.append(points[i + 1] - points[0])
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


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    features = resolve(FEATURES)
    if name.startswith("lighting"):
        views = {k: features[k] for k in LIGHTING_VIEWS}
    elif name.startswith("features"):
        views = features
    elif name.startswith("flames"):
        views = FLAME_VIEWS
    else:
        views = {**features, **room_views()}
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
