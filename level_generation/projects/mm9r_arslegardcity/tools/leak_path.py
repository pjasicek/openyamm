#!/usr/bin/env python3
"""The shortest voxel path from a seed inside the city to the grid border through non-solid voxels: where the air
leaks out (the Lich Lab lesson: a breadth-first path shows the leak). Usage: leak_path.py [x y z LT]"""
import sys
from collections import deque
from pathlib import Path
import numpy as np
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon.build import Build  # noqa
from dungeon.source import Project  # noqa
from dungeon.geometry import merge_coplanar, drop_unshared_collinear, VoxelGrid, mark, sample_polygon  # noqa
import convert  # noqa

project = Project.load(PROJECT, install=False)
b = Build(project, convert.ArslegardCity())
polygons = []
for name in b.plan["static"]:
    polygons += b.source.polygons(name)
polygons = merge_coplanar(polygons)
drop_unshared_collinear(polygons)
voxel = project.voxel
points = np.concatenate([p.points for p in polygons])
grid = VoxelGrid(points.min(0), points.max(0), voxel)
solid = np.zeros(grid.shape, bool)
for polygon in polygons:
    if polygon.role == "static":
        mark(grid, solid, sample_polygon(polygon.points, voxel / 4))
start = [float(v) for v in sys.argv[1:4]] if len(sys.argv) > 3 else [4000.0, -100.0, -9500.0]
s = tuple(grid.index(np.array([start]))[0])
shape = solid.shape
prev = -np.ones(shape, np.int64)
q = deque([s]); prev[s] = np.ravel_multi_index(s, shape)
end = None
while q:
    c = q.popleft()
    if 0 in c or any(c[i] == shape[i] - 1 for i in range(3)):
        end = c
        break
    for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
        n = (c[0]+d[0], c[1]+d[1], c[2]+d[2])
        if not solid[n] and prev[n] < 0:
            prev[n] = np.ravel_multi_index(c, shape); q.append(n)
if end is None:
    raise SystemExit("no path to the border")
path = [end]
while path[-1] != s:
    path.append(tuple(np.unravel_index(prev[path[-1]], shape)))
path = path[::-1]
lt = [grid.origin + (np.array(c) + 0.5) * voxel for c in path]
print("path length", len(path))
for k in range(0, len(lt), max(1, len(lt) // 60)):
    print(k, np.round(lt[k]).astype(int).tolist())
print("end", np.round(lt[-1]).astype(int).tolist())
