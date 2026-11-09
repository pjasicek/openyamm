#!/usr/bin/env python3
"""The four views of the user's real MM9 screenshots of Klusos House (devdocs/mm9_rework/overnight/real_mm9/
klusoshouse_real_1..4_*.png), found by compass and furniture, as a tour in LT units (make_tour.py's format):

    python3 level_generation/projects/mm9r_klusoshouse/make_real_tour.py <name>
"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

LOWER, UPPER = 60, 230
VIEWS = {
    # 1: the west bedroom (room 4) facing NE: its north door (doorportal8) on the left, the low cabinet (Cabinet40) and
    # wall candle (WallTorch68) on the east wall, the guard UpperSleep3 standing by the corner
    "r1_corridor_guard": (-670, 20, -470, 220, UPPER, -4),
    # 2: the west bedroom (room 4) facing S through its door, across the corridor, to the window room's door
    "r2_doorway": (-560, 150, -600, -200, UPPER, -4),
    # 3: the master bedroom (upper south-east) facing SE: low cabinet on the east wall, chair, round table, tall cabinet
    "r3_dark_room_props": (60, -140, 260, -340, UPPER, -6),
    # 4: the great hall facing SE toward Count Kluso, the south door, the low cabinet and the east door
    "r4_count_room": (-390, 970, -190, 770, LOWER, -4),
}

if __name__ == "__main__":
    tour.write(Project.load(PROJECT, install=False), VIEWS, sys.argv[1] if len(sys.argv) > 1 else "real01")
