#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Arena: eye-level views of the hall, the counter, the arena floor, the pens,
the stands and Sven's box, in MM9 (LithTech) coordinates, converted by the shared tour helper
(../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_thearena/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_thearena/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_thearena/make_tour.py lighting<n> [--original]   # the lighting subset

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
FLOOR, STAND, BOX = 60, 420, 260        # the hall and the arena floor (0 LT), the stands' top tiers, Sven's box (192)
VIEWS = {
    "h01_start": (0, -1440, 0, -600, FLOOR),
    "h02_hall_to_front_door": (0, -1100, 0, -1530, FLOOR),
    "h03_counter_master": (60, -1344, -200, -1344, FLOOR),
    "h04_counter_bars": (-20, -1260, -150, -1400, FLOOR),
    "h05_corridor_to_arena_door": (0, -1000, 0, -600, FLOOR),
    "h06_hall_west_side": (-40, -1420, -40, -1100, FLOOR),
    "h07_west_strip": (-190, -1470, -190, -700, FLOOR),
    "h08_stair_up": (184, -1240, 184, -1000, 100, 18),
    "s01_stair_down": (184, -1000, 184, -1300, 250, -20),
    "s02_south_stand": (0, -930, 0, 300, STAND, -12),
    "a01_arena_north": (0, -350, 0, 700, FLOOR),
    "a02_arena_east_pen": (250, 0, 700, 0, FLOOR),
    "a03_arena_west_pen": (-250, 0, -700, 0, FLOOR),
    "a04_arena_door": (0, 100, 0, -700, FLOOR),
    "a05_arena_diagonal": (320, 320, -300, -300, FLOOR),
    "a06_arena_sky": (0, -200, 0, 400, FLOOR, 35),
    "p01_east_pen": (740, 0, 300, 0, FLOOR),
    "p02_west_pen": (-740, 0, -300, 0, FLOOR),
    "b01_box_over_arena": (0, 700, 0, 0, BOX, -15),
    "b02_box_throne": (-80, 650, 144, 830, BOX),
    "t01_east_stand": (850, -150, 0, 0, STAND, -12),
    "t02_west_stand": (-850, 150, 0, 0, STAND, -12),
    "t03_north_stand": (350, 950, 0, 0, STAND, -12),
    "t04_ne_stand": (540, 540, 0, 0, 300, -10),
    "t05_sw_stand": (-540, -540, 0, 0, 300, -10),
    "t06_se_stand_along": (750, -600, 1000, 0, STAND),
}
LIGHTING_VIEWS = ["h01_start", "h03_counter_master", "h05_corridor_to_arena_door", "h08_stair_up",
                  "s02_south_stand", "a01_arena_north", "a02_arena_east_pen", "a04_arena_door", "p01_east_pen",
                  "b01_box_over_arena", "t01_east_stand", "t04_ne_stand"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
