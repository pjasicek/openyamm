#!/usr/bin/env python3
"""A horizontal slice of the solid voxels (static faces) at LT height y: work/slice_<name>.png, 2 px per 16-LT voxel,
grid every 128 LT labelled. slice.py <name> <y> [x0 x1 z0 z1]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.build import Build  # noqa
from dungeon.source import Project  # noqa
from dungeon.geometry import merge_coplanar, VoxelGrid, mark, sample_polygon  # noqa
sys.path.insert(0, str(PROJECT))
from convert import Bathhouse  # noqa

name, y = sys.argv[1], float(sys.argv[2])
project = Project.load(PROJECT, work=PROJECT / "work" / "diag", install=False)
build = Build(project, Bathhouse())
polygons = []
for m in build.plan["static"]:
    polygons += build.source.polygons(m)
mover_polys = [p for m in build.plan["movers"] for p in build.source.polygons(m)]
points = np.concatenate([p.points for p in polygons])
grid = VoxelGrid(points.min(0), points.max(0), 16)
solid = np.zeros(grid.shape, bool)
mover = np.zeros(grid.shape, bool)
for p in polygons:
    if p.role == "static":
        mark(grid, solid, sample_polygon(p.points, 4))
for p in mover_polys:
    mark(grid, mover, sample_polygon(p.points, 4))
j = grid.index(np.array([[0, y, 0]]))[0][1]
x0, x1, z0, z1 = [float(v) for v in sys.argv[3:7]] if len(sys.argv) > 6 else (points[:, 0].min(), points[:, 0].max(),
                                                                                 points[:, 2].min(), points[:, 2].max())
S = int(__import__("os").environ.get("S", "4"))
cells_x = np.arange(grid.index(np.array([[x0, 0, 0]]))[0][0], grid.index(np.array([[x1, 0, 0]]))[0][0] + 1)
cells_z = np.arange(grid.index(np.array([[0, 0, z0]]))[0][2], grid.index(np.array([[0, 0, z1]]))[0][2] + 1)
img = Image.new("RGB", (len(cells_x) * S, len(cells_z) * S), (240, 240, 230))
px = img.load()
for a, i in enumerate(cells_x):
    for b, k in enumerate(cells_z[::-1]):
        c = (30, 30, 40) if solid[i, j, k] else ((220, 60, 60) if mover[i, j, k] else None)
        if c:
            for dx in range(S):
                for dy in range(S):
                    px[a * S + dx, b * S + dy] = c
d = ImageDraw.Draw(img)
ox, oz = grid.origin[0] + cells_x[0] * 16, grid.origin[2] + cells_z[-1] * 16 + 16
for gx in range(int(np.ceil(x0 / 128) * 128), int(x1), 128):
    u = (gx - ox) / 16 * S
    d.line([(u, 0), (u, img.height)], fill=(150, 170, 230) if gx % 512 else (60, 90, 220))
    if gx % 256 == 0:
        d.text((u + 2, 2), str(gx), fill=(0, 0, 160))
for gz in range(int(np.ceil(z0 / 128) * 128), int(z1), 128):
    v = (oz - gz) / 16 * S
    d.line([(0, v), (img.width, v)], fill=(150, 170, 230) if gz % 512 else (60, 90, 220))
    if gz % 256 == 0:
        d.text((2, v + 2), str(gz), fill=(0, 0, 160))
img.save(PROJECT / f"work/slice_{name}.png")
print(PROJECT / f"work/slice_{name}.png", img.size)
