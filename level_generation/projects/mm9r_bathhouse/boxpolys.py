#!/usr/bin/env python3
"""Static polygons intersecting an LT box: boxpolys.py x0 y0 z0 x1 y1 z1"""
import sys
from pathlib import Path
import numpy as np
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import Project, Source, classify_models  # noqa
project = Project.load(PROJECT, install=False)
source = Source(project)
plan = classify_models(source)
lo = np.array(sys.argv[1:4], float); hi = np.array(sys.argv[4:7], float)
for name in plan["static"] + sorted(plan["movers"]):
    for p in source.polygons(name):
        a, b = p.points.min(0), p.points.max(0)
        if np.all(b >= lo) and np.all(a <= hi):
            n = np.round(p.normal, 2)
            print(f"{name:14s} {p.texture.split(chr(92))[-1]:28s} n={n} lo={a.round().astype(int)} hi={b.round().astype(int)} {p.role}")
