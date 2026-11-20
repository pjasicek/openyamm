#!/usr/bin/env python3
"""Archway cut lab: builds the voxels once (cached in work/cutlab.npz), then checks every overrides.yml cut and door
portal: whether its two sides end in different components of the air minus all barriers; for a failing one, prints
the leak path. Usage: tools/cutlab.py [--rebuild] [portal name ...]"""
import pickle
import sys
from collections import deque
from pathlib import Path

import numpy as np
import yaml
from scipy import ndimage

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import convert  # noqa: E402
from dungeon.build import Build  # noqa: E402
from dungeon.geometry import drop_unshared_collinear, merge_coplanar  # noqa: E402
from dungeon.rooms import archway_portals, build_voxels, door_portals, portal_barrier  # noqa: E402
from dungeon.rotation import rectangle_portals  # noqa: E402
from dungeon.source import Project  # noqa: E402

CACHE = PROJECT / "work/cutlab.pkl"
project = Project.load(PROJECT, install=False)
build = Build(project, convert.InventaStorca())
if CACHE.exists() and "--rebuild" not in sys.argv:
    grid, air, door = pickle.loads(CACHE.read_bytes())
else:
    polygons = []
    for name in build.plan["static"]:
        polygons += build.source.polygons(name)
    polygons = merge_coplanar(polygons)
    drop_unshared_collinear(polygons)
    polygons = build.hooks.edit_polygons(build, polygons)
    grid, solid, air, _ = build_voxels(polygons, build.source, build.hooks.extra_seeds(build))
    door = door_portals(build.source, build.plan)
    CACHE.write_bytes(pickle.dumps((grid, air, door)))
portals = list(door)
for extra in project.overrides.get("portals") or []:
    portals.extend(archway_portals(grid, air, extra))
portals.extend(rectangle_portals(project.overrides.get("rect_portals")))
barrier = np.zeros(grid.shape, bool)
for portal in portals:
    cells = portal["cells"] if "cells" in portal else portal_barrier(grid, portal)
    barrier[cells[:, 0], cells[:, 1], cells[:, 2]] = True
free = air & ~barrier
labels, count = ndimage.label(free)
print("components", count)
names = [a for a in sys.argv[1:] if not a.startswith("--")]
for portal in portals:
    a = tuple(grid.index((portal["centre"] + portal["normal"] * 24)[None])[0])
    b = tuple(grid.index((portal["centre"] - portal["normal"] * 24)[None])[0])
    la, lb = labels[a], labels[b]
    ok = la != lb and la and lb
    if not ok or portal["name"] in names:
        print(("OK  " if ok else "FAIL"), portal["name"], portal["kind"], portal["centre"].round().tolist(),
              round(portal["half_a"]), round(portal["half_b"]), la, lb)
    if la == lb and la and (portal["name"] in names or "--paths" in sys.argv):
        came = {a: None}
        queue = deque([a])
        while queue and b not in came:
            cell = queue.popleft()
            for axis in range(3):
                for sign in (-1, 1):
                    other = list(cell); other[axis] += sign; other = tuple(other)
                    if all(0 <= other[i] < grid.shape[i] for i in range(3)) and free[other] and other not in came:
                        came[other] = cell
                        queue.append(other)
        path = [b]
        while came[path[-1]] is not None:
            path.append(came[path[-1]])
        pts = grid.centre(np.array(path[::-1]))
        print("   path", [tuple(int(v) for v in pts[i]) for i in range(0, len(pts), max(1, len(pts) // 24))])

if "--probe" in sys.argv:
    for text in sys.argv[sys.argv.index("--probe") + 1:]:
        x, y, z = (float(v) for v in text.split(","))
        cell = tuple(grid.index(np.array([[x, y, z]]))[0])
        print("probe", (x, y, z), "air", bool(air[cell]), "label", labels[cell], "size", int((labels == labels[cell]).sum()) if labels[cell] else 0)
