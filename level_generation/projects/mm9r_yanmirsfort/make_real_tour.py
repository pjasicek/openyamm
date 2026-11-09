#!/usr/bin/env python3
"""The views of the user's real MM9 screenshots of Yanmir's Fort (devdocs/mm9_rework/overnight/real_mm9/
yanmirsfort_real_1..2.png), found by compass (MM9's N is +z LT) and the great hall's pillars, doors and benches, as a
tour in LT units (make_tour.py's format); the _alt views are neighbouring poses for the spread of the numbers.

    python3 level_generation/projects/mm9r_yanmirsfort/make_real_tour.py <name>
"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

VIEWS = {
    # 1: the great hall facing S at the trap hall's door, a square pillar right of it, Yanmir in front (not placed)
    "y1_great_hall_south": (250, -500, 250, -1500, 300, 8),
    "y1_alt_west": (-300, -500, -300, -1500, 300, 8),
    "y1_alt_east": (700, -500, 700, -1500, 300, 8),
    # 2: the great hall facing SW over the floor to the pillars, a bench on the right
    "y2_great_hall_southwest": (900, 0, 100, -800, 300, -10),
    "y2_alt_northeast": (1400, -300, 600, -1100, 300, -10),
    "y2_alt_east": (1400, -1000, 600, -1800, 300, -10),
}

if __name__ == "__main__":
    tour.write(Project.load(PROJECT, install=False), VIEWS, sys.argv[1] if len(sys.argv) > 1 else "real01")
