#!/usr/bin/env python3
"""Which air seeds flood the map's outside: labels the air from every seed object separately (no portals) and lists
the seeds whose component touches the voxel grid's border, or is small. Usage: tools/leak_seeds.py"""
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.geometry import drop_unshared_collinear, merge_coplanar  # noqa: E402
from dungeon.rooms import build_voxels  # noqa: E402
from dungeon.source import Project, Source, classify_models  # noqa: E402

project = Project.load(PROJECT, install=False)
source = Source(project)
plan = classify_models(source)
polygons = []
for name in plan["static"]:
    polygons += source.polygons(name)
polygons = merge_coplanar(polygons)
grid, solid, air, stats = build_voxels(polygons, source, project.overrides.get("seeds") or [])
labels, count = ndimage.label(~solid)
border = set(np.unique(np.concatenate([labels[0].ravel(), labels[-1].ravel(), labels[:, 0].ravel(),
                                       labels[:, -1].ravel(), labels[:, :, 0].ravel(), labels[:, :, -1].ravel()])))
sizes = np.bincount(labels.ravel())
classes = project.seed_classes | project.monster_classes
for o in source.objects:
    if o["class"] not in classes:
        continue

    p = np.array(o["properties"]["Pos"], float)
    ijk = tuple(grid.index(p[None])[0])
    label = labels[ijk]
    if label == 0 or label in border or sizes[label] < 2000:
        print(o["class"], o["name"], p.tolist(), "label", label, "size", sizes[label], "BORDER" if label in border else "")
