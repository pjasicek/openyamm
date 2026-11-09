#!/usr/bin/env python3
"""The views of the user's real MM9 screenshots of the Dungeon of Secrets (devdocs/mm9_rework/overnight/real_mm9/
dungeonofsecrets_real_1..4_*.png), found by compass (MM9's N is +z LT), lamps and doorways, as a tour in LT units
(make_tour.py's format). Shot 3 looks through an open door; our tour cannot open it, so 3a is the near wall with the
door shut and 3b the room beyond from its threshold.

    python3 level_generation/projects/mm9r_dungeonofsecrets/make_real_tour.py <name>
"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

G, U = 100, 420
VIEWS = {
    # 1: the west corridor (plate room approach) facing W: the lamp on the left wall near the end, the opening north
    # (to the plate room) on the right; section 8's corridor as the alternative
    "d1_west_corridor": (-520, 455, -1000, 455, G),
    "d1_alt_back": (-420, 455, -1000, 455, G),
    # 2: the flooded pool room facing W at the banner wall and the passage to the west corridor
    "d2_pool_room_w": (0, 520, -500, 520, G),
    "d2_alt_south": (250, 455, -500, 455, G),
    # 3: between the entrance gate (open in the shot, x 1678) and axe door 10 (x 1560) facing W: in ours both are shut,
    # so 3a shows the near wall and the shut door leaf, and 3b the section 10 room from its threshold (what the open
    # door shows: the lamp on the far wall, the lit left wall)
    "d3a_hub_door_s10": (1655, -160, 1300, -160, G),
    "d3b_s10_room": (1540, -150, 1200, -150, G),
    # 4: the upper corridor of section 4 facing W over the double axe's plate into the purple room
    "d4_s04_corridor_w": (230, 490, -300, 490, U),
    "d4_alt_back": (300, 490, -300, 490, U),
}


if __name__ == "__main__":
    tour.write(Project.load(PROJECT, install=False), VIEWS, sys.argv[1] if len(sys.argv) > 1 else "real01")
