#!/usr/bin/env python3
"""Which seed objects sit in air that reaches the map's border (the outside), and which air components are small."""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa
from dungeon.build import Build  # noqa
from dungeon.source import Project  # noqa
from dungeon.geometry import merge_coplanar, VoxelGrid, mark, sample_polygon  # noqa
sys.path.insert(0, str(PROJECT))
from convert import Bathhouse  # noqa

project = Project.load(PROJECT, work=PROJECT / "work" / "diag", install=False)
build = Build(project, Bathhouse())
polygons = []
for name in build.plan["static"]:
    polygons += build.source.polygons(name)
polygons = build.hooks.edit_polygons(build, merge_coplanar(polygons))
points = np.concatenate([p.points for p in polygons])
grid = VoxelGrid(points.min(0), points.max(0), project.voxel)
solid = np.zeros(grid.shape, bool)
for polygon in polygons:
    if polygon.role == "static":
        mark(grid, solid, sample_polygon(polygon.points, project.voxel / 4))
labels, count = ndimage.label(~solid)
border = set(np.unique(np.concatenate([labels[0].ravel(), labels[-1].ravel(), labels[:, 0].ravel(), labels[:, -1].ravel(),
                                        labels[:, :, 0].ravel(), labels[:, :, -1].ravel()])))
sizes = np.bincount(labels.ravel())
classes = project.seed_classes | project.monster_classes
excluded = {n.lower() for n in project.overrides.get("seed_exclude") or []}
for o in build.source.objects:
    if o["class"] not in classes or o["name"].lower() in excluded:
        continue
    cell = grid.index(np.array(o["properties"]["Pos"], float)[None])[0]
    lab = labels[tuple(cell)]
    if lab in border or sizes[lab] < 20000:
        print(f"{o['name']:24s} {o['class']:14s} {np.round(o['properties']['Pos']).astype(int)} component {lab} "
              f"size {sizes[lab]} {'BORDER' if lab in border else ''} solid={solid[tuple(cell)]}")
