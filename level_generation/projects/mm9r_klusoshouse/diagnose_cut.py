#!/usr/bin/env python3
"""
Why an archway cut does not separate two rooms (playbook, "Diagnose a failing cut"): a breadth-first path over the air
minus all barriers between the two sides of the named cuts; prints the path's turning points (LT).

    python3 level_generation/projects/mm9r_beethoven/diagnose_cut.py <portal name> [...]
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import convert  # noqa: E402
from dungeon.build import Build  # noqa: E402
from dungeon.rooms import archway_portals, door_portals, build_voxels, label_rooms, portal_barrier  # noqa: E402
from dungeon.geometry import merge_coplanar, drop_unshared_collinear  # noqa: E402
from dungeon.source import Project  # noqa: E402


def main() -> int:
    project = Project.load(PROJECT, install=False)
    build = Build(project, convert.KlusosHouse())
    polygons = []
    for name in build.plan["static"]:
        polygons += build.source.polygons(name)
    polygons = merge_coplanar(polygons)
    drop_unshared_collinear(polygons)
    polygons = build.hooks.edit_polygons(build, polygons)
    portals = door_portals(build.source, build.plan)
    grid, solid, air, _ = build_voxels(polygons, build.source, build.hooks.extra_seeds(build))
    for extra in project.overrides.get("portals") or []:
        portals.extend(archway_portals(grid, air, extra))
    barrier = np.zeros(grid.shape, bool)
    for portal in portals:
        cells = portal["cells"] if "cells" in portal else portal_barrier(grid, portal)
        barrier[cells[:, 0], cells[:, 1], cells[:, 2]] = True
    free = air & ~barrier
    for name in sys.argv[1:]:
        portal = next(p for p in portals if p["name"] == name)
        start = grid.index((portal["centre"] + portal["normal"] * 32)[None])[0]
        goal = grid.index((portal["centre"] - portal["normal"] * 32)[None])[0]
        start, goal = tuple(int(v) for v in start), tuple(int(v) for v in goal)
        print(name, portal["centre"].round(), "half", round(portal["half_a"]), round(portal["half_b"]), start, goal,
              free[start], free[goal])
        came = {start: None}
        queue = deque([start])
        while queue and goal not in came:
            cell = queue.popleft()
            for axis in range(3):
                for sign in (-1, 1):
                    other = list(cell)
                    other[axis] += sign
                    other = tuple(other)
                    if all(0 <= other[i] < grid.shape[i] for i in range(3)) and free[other] and other not in came:
                        came[other] = cell
                        queue.append(other)
        if goal not in came:
            print("  separated")
            continue
        path = [goal]
        while came[path[-1]] is not None:
            path.append(came[path[-1]])
        points = grid.centre(np.array(path[::-1]))
        print("  path", len(points), [tuple(int(v) for v in points[i]) for i in range(0, len(points), max(1, len(points) // 18))])
    return 0


if __name__ == "__main__":
    sys.exit(main())
