#!/usr/bin/env python3
"""Which seeds flood air that touches the grid border (leaked_to_border), and component sizes per seed (Yanmir's Fort's tools/leak.py, copied)."""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon.build import Build  # noqa
from dungeon.source import Project  # noqa
from dungeon.geometry import merge_coplanar, drop_unshared_collinear, VoxelGrid, mark, sample_polygon, SIX  # noqa
import convert  # noqa

project = Project.load(PROJECT, install=False)
b = Build(project, convert.ArslegardCity())
polygons = []
for name in b.plan["static"]:
    polygons += b.source.polygons(name)
polygons = merge_coplanar(polygons)
drop_unshared_collinear(polygons)
polygons = b.hooks.edit_polygons(b, polygons)
voxel = project.voxel
points = np.concatenate([p.points for p in polygons])
grid = VoxelGrid(points.min(0), points.max(0), voxel)
solid = np.zeros(grid.shape, bool)
for polygon in polygons:
    if polygon.role == "static":
        mark(grid, solid, sample_polygon(polygon.points, voxel / 4))
labels, count = ndimage.label(~solid, structure=SIX)
border = set(np.unique(np.concatenate([labels[[0, -1]].ravel(), labels[:, [0, -1]].ravel(), labels[:, :, [0, -1]].ravel()])))
sizes = np.bincount(labels.ravel())
classes = project.seed_classes | project.monster_classes
rows = []
for o in b.source.objects:
    if o["class"] in classes:
        pos = o["properties"]["Pos"]
        c = grid.index(np.array([pos], float))[0]
        lab = int(labels[c[0], c[1], c[2]])
        rows.append((lab in border, lab, sizes[lab] if lab else 0, o["class"], o["name"], pos))
for r in sorted(rows, key=lambda r: (not r[0], -r[2])):
    if r[0] or r[2] < 20000:
        print(("LEAK " if r[0] else "small") , r[1:])
print("components seeded:", sorted({(r[1], r[2]) for r in rows}, key=lambda t: -t[1])[:20])
