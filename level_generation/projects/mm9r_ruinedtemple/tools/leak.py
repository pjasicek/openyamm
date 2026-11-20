#!/usr/bin/env python3
"""Which seeds flood the outside: label the static air (no barriers) and list each component's seeds, size, bounds
and whether it touches the grid border."""
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import convert  # noqa: E402
from dungeon.build import Build  # noqa: E402
from dungeon.geometry import merge_coplanar  # noqa: E402
from dungeon.rooms import build_voxels, SIX  # noqa: E402
from dungeon.source import Project, classify_models  # noqa: E402

project = Project.load(PROJECT, install=False)
b = Build(project, convert.RuinedTemple())
polygons = []
for name in b.plan["static"]:
    polygons += b.source.polygons(name)
polygons = merge_coplanar(polygons)
grid, solid, air, stats = build_voxels(polygons, b.source)
labels, n = ndimage.label(~solid, structure=SIX)
classes = project.seed_classes | project.monster_classes
border = set(np.unique(np.concatenate([labels[0].ravel(), labels[-1].ravel(), labels[:, 0].ravel(), labels[:, -1].ravel(),
                                       labels[:, :, 0].ravel(), labels[:, :, -1].ravel()])))
comp = {}
for o in b.source.objects:
    if o["class"] not in classes:
        continue
    idx = grid.index(np.array([o["properties"]["Pos"]], float))[0]
    lab = int(labels[tuple(idx)])
    comp.setdefault(lab, []).append(o["name"])
for lab, names in sorted(comp.items(), key=lambda kv: -len(kv[1])):
    print(lab, "border" if lab in border else "", int((labels == lab).sum()) if lab else 0, names[:12], len(names))
print("grid", grid.shape, getattr(grid, "origin", None))
