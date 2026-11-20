#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Connecting Tunnels: eye-level views of the starts and the scripted places by
hand and one view per room of the built map (Thjorad Mine's room_views), in MM9 (LithTech) coordinates, converted by
the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_connectingtunnels/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_connectingtunnels/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_connectingtunnels/make_tour.py lighting<n> [--original]   # lighting subset

The BLV's frame is shifted by overrides.yml `offset` (x 17 000); the old map keeps MM9's frame, so the --original tour
adds the offset back to every position (tour.write converts with the new frame).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT.parents[2]))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

SKIP_TEXTURES = ("INVIZVJN7N",)
OFFSET = np.array([17000.0, 0.0, 0.0])
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    "a01_start0_thronheim": (13408, -1376, 13408, -1000, 800),
    "a02_start1_yorwick": (-64, -3040, 300, -3010, 800),
    "a03_start2_yorwick_upper": (220, 3602, -110, 3482, 2700),
    "a04_rockfall": (2540, -1300, 2540, -880, 100),
    "a05_coffin": (5850, -5100, 6272, -5184, 0, -8),
    "a06_coffin_chamber": (7300, -5000, 5600, -5100, 0),
    "a07_coffin_side": (5980, -5184, 6272, -5184, 0, -18),
    "a08_chest0": (10800, 150, 11008, 64, 300, -10),
}


def room_views() -> dict:
    """Two views per room of the built map (work/runtime): between the two floor faces farthest apart that see each other
    at eye height, each looking at the other, where the party fits (not in the low culverts), so every room is seen."""
    import numpy as np
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime/connectingtunnels.blv")["payload"]
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
        p, q = (best[1] + OFFSET) / 2.56, (best[2] + OFFSET) / 2.56
        views[f"r{room:02d}_a"] = (round(p[0]), round(p[1]), round(q[0]), round(q[1]), round(p[2] + 30))
        views[f"r{room:02d}_b"] = (round(q[0]), round(q[1]), round(p[0]), round(p[1]), round(q[2] + 30))
    return views


LIGHTING_VIEWS = ["a01_start0_thronheim", "a02_start1_yorwick", "a03_start2_yorwick_upper", "a04_rockfall",
                  "a05_coffin", "a06_coffin_chamber", "a07_coffin_side"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    original = "--original" in sys.argv
    rooms = room_views()
    if "--all" not in sys.argv:
        rooms = {k: v for k, v in rooms.items() if k.endswith("_a")}
    views = {**VIEWS, **rooms}
    if name.startswith("lighting"):
        views = {k: views[k] for k in LIGHTING_VIEWS + sorted(k for k in rooms if k.endswith("_a"))[::2]}
    project = Project.load(PROJECT, install=False)
    result = tour.write(project, views, name, original=original)
    if original:                      # the old map's frame: native x + offset
        path = PROJECT / f"review_tour_{name}_original.yml"
        for shot in result["shots"]:
            shot["position"] = [int(round(v + o)) for v, o in zip(shot["position"], project.offset)]
        path.write_text(yaml.safe_dump(result, sort_keys=False))
        print("original frame: first shot", result["shots"][0]["position"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
