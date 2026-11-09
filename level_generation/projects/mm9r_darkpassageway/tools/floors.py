#!/usr/bin/env python3
"""Floor heights (LT) under given x,z points: tools/floors.py x,z [x,z ...] [--from Y]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mm9r_common"))
from dungeon.source import Project, Source, floor_below
p = Project.load(Path(__file__).resolve().parents[1], install=False)
s = Source(p)
polys = []
for name in ["PhysicsBSP"] + [m for m in s.models if m.startswith(("Terrain", "WorldObject"))]:
    polys += s.polygons(name)
top = 2000
args = sys.argv[1:]
if "--from" in args:
    top = float(args[args.index("--from") + 1]); args = args[:args.index("--from")]
for a in args:
    x, z = map(float, a.split(","))
    f = floor_below(polys, [x, top, z])
    # ceiling: lowest downward face above floor
    import numpy as np
    ceil = None
    for poly in polys:
        if poly.normal[1] > -0.7: continue
        pts = poly.points
        if not (pts[:,0].min() <= x <= pts[:,0].max() and pts[:,2].min() <= z <= pts[:,2].max()): continue
        n = poly.normal; h = (n @ pts[0] - n[0]*x - n[2]*z)/n[1]
        if f is not None and h > f and (ceil is None or h < ceil): ceil = h
    print(a, "floor", None if f is None else round(f,1), "ceiling", None if ceil is None else round(ceil,1))
