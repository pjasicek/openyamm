#!/usr/bin/env python3
"""Static polygons (and mover models) overlapping an LT box: name, texture, y range, normal. Usage: probe.py x0 x1 y0 y1 z0 z1"""
import sys
from pathlib import Path
import numpy as np
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import Project, Source, classify_models  # noqa: E402
x0, x1, y0, y1, z0, z1 = map(float, sys.argv[1:7])
project = Project.load(PROJECT, install=False)
source = Source(project)
plan = classify_models(source)
names = list(plan["static"]) + list(plan["movers"])
for name in names:
    for p in source.polygons(name):
        lo, hi = p.points.min(0), p.points.max(0)
        if hi[0] < x0 or lo[0] > x1 or hi[1] < y0 or lo[1] > y1 or hi[2] < z0 or lo[2] > z1:
            continue
        n = np.cross(p.points[1] - p.points[0], p.points[2] - p.points[0]); n = n / (np.linalg.norm(n) or 1)
        print(f"{name:20s} {p.texture.split(chr(92))[-1]:18s} x {lo[0]:.0f}..{hi[0]:.0f} y {lo[1]:.0f}..{hi[1]:.0f} z {lo[2]:.0f}..{hi[2]:.0f} n {n.round(2)} {p.role}")
