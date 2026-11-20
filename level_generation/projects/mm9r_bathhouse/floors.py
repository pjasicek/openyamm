#!/usr/bin/env python3
"""Floor heights (LT) under points: floors.py x z [query_y] ..."""
import sys
from pathlib import Path
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import Project, Source, classify_models, floor_below  # noqa
project = Project.load(PROJECT, install=False)
source = Source(project)
plan = classify_models(source)
polys = [p for m in plan["static"] for p in source.polygons(m)]
args = [float(a) for a in sys.argv[1:]]
for i in range(0, len(args), 3):
    x, z, q = args[i:i + 3]
    print(x, z, q, "->", floor_below(polys, (x, q, z)))
