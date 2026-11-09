#!/usr/bin/env python3
"""The view of the user's real MM9 screenshot of Dragon Stadium (devdocs/mm9_rework/overnight/real_mm9/
dragonstadium_real_1_floor.png): facing SW (MM9's N is +z LT) over the bowl's floor with BonePile Prop1 and Prop0 left
of centre (solved from their screen positions at a 90 degree view), pitched down to the shot's horizon. As a tour in LT
units (make_tour.py's format); the _alt views are neighbouring poses.

    python3 level_generation/projects/mm9r_dragonstadium/make_real_tour.py <name>
"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

VIEWS = {
    "s1_floor_southwest": (1470, 380, 470, -620, 300, -8),
    "s1_alt_closer": (1200, 150, 200, -850, 300, -8),
    "s1_alt_north": (1300, 800, 300, -200, 300, -8),
}

if __name__ == "__main__":
    tour.write(Project.load(PROJECT, install=False), VIEWS, sys.argv[1] if len(sys.argv) > 1 else "real01")
