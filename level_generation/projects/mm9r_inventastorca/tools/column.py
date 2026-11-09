#!/usr/bin/env python3
"""Horizontal-ish static polygons over/under LT points: tools/column.py x z [x z ...] -> y, normal sign, texture."""
import sys
from pathlib import Path
import numpy as np
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import Project, Source, classify_models  # noqa: E402

project = Project.load(PROJECT, install=False)
source = Source(project)
plan = classify_models(source)
polys = [p for name in plan["static"] for p in source.polygons(name)
         if abs(p.normal[1]) > 0.5]


def inside(poly, x, z):
    pts = poly.points[:, [0, 2]]
    n = len(pts)
    sign = None
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        c = (b[0] - a[0]) * (z - a[1]) - (b[1] - a[1]) * (x - a[0])
        if abs(c) < 1e-6:
            continue
        s = c > 0
        if sign is None:
            sign = s
        elif s != sign:
            return False
    return True


args = [float(a) for a in sys.argv[1:]]
for x, z in zip(args[::2], args[1::2]):
    hits = []
    for p in polys:
        if inside(p, x, z):
            n = p.normal
            y = p.points[0][1] - (n[0] * (x - p.points[0][0]) + n[2] * (z - p.points[0][2])) / n[1]
            hits.append((round(y, 1), "up" if n[1] > 0 else "down", p.texture.split("\\")[-1], p.model))
    print((x, z), sorted(set(hits)))
