#!/usr/bin/env python3
"""Floors under LithTech points: python3 tools/floors.py x z [x z ...] -> each floor height (static models)."""
import sys
from pathlib import Path
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import Project, Source, classify_models, floor_below  # noqa: E402

project = Project.load(PROJECT, install=False)
source = Source(project)
plan = classify_models(source)
polygons = [p for m in plan["static"] for p in source.polygons(m)]


def floors(x, z):
    out, y = [], 2000.0
    while True:
        f = floor_below(polygons, (x, y, z))
        if f is None:
            return out
        out.append(round(f, 1))
        y = f - 2


if __name__ == "__main__":
    a = [float(v) for v in sys.argv[1:]]
    for i in range(0, len(a), 2):
        print(a[i], a[i + 1], floors(a[i], a[i + 1]))
