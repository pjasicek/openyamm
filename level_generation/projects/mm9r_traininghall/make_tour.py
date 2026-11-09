#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Training Hall: eye-level views through every room, in MM9 (LithTech)
coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_traininghall/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_traininghall/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_traininghall/make_tour.py lighting<n> [--original]   # the lighting subset

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
ROOF, HALL, LOWER = 700, 100, -200
VIEWS = {
    "r01_roof_start": (0, 150, 0, -300, ROOF),
    "r02_roof_exit_hut": (-120, 0, 200, 0, ROOF),
    "r03_roof_hole": (0, 130, 0, 0, ROOF, -50),
    "l01_lobby_south": (0, -400, 0, 300, HALL),
    "l02_lobby_northwest": (-350, 300, 300, -300, HALL),
    "l03_lobby_east_door": (-300, 0, 500, 0, HALL),
    "l04_lobby_chandelier": (-200, -380, 0, 0, HALL, 25),
    "l05_crows_nest": (-250, -250, 200, 200, 500, -15),
    "p01_dragon_door": (0, 420, 0, 800, 300, 10),
    "p02_pole_room": (0, 690, 0, 1300, 300, 15),
    "p03_pole_room_up": (0, 690, 100, 1200, 300, 45),
    "p04_platform_736": (100, 1100, -200, 800, 800),
    "p05_ledge_1344": (232, 1000, 0, 900, 1400, -30),
    "p06_beam_480": (230, 984, 0, 1200, 520),
    "c01_east_corridor": (550, 0, 1100, 0, HALL),
    "c02_east_leg": (1088, 0, 1088, -600, HALL),
    "c03_west_corridor": (-550, 0, -1100, 0, HALL),
    "c04_east_stair": (736, -100, 736, -600, HALL, -20),
    "j01_lower_cross": (-600, -700, 600, -700, LOWER),
    "j02_joust_hall_west": (-750, -1100, 700, -1900, LOWER),
    "j03_joust_lane2": (-550, -1500, 800, -1380, LOWER),
    "j04_joust_lane4": (-550, -1700, 800, -1830, LOWER),
    "j05_joust_from_east": (700, -1600, -700, -1200, LOWER),
    "t01_training_room": (0, -700, 0, -1400, HALL),
    "t02_end_door": (0, -1250, 0, -1420, HALL),
    "t03_training_room_west": (250, -900, -300, -1100, HALL),
    "a01_range_north": (1072, -700, 1072, -1900, HALL),
    "a02_range_targets": (1072, -1150, 1000, -1800, HALL),
    "a03_range_counters": (700, -1000, 1300, -1150, HALL),
    "x01_crate_room": (-1100, -700, -1400, -1200, HALL),
    "x02_crate": (-1250, -1150, -1400, -1150, HALL),
    "d01_debris_room": (905, -1824, 1060, -1950, LOWER),
    "s01_cave_south": (1040, -2000, 1030, -2450, -250),
    "s02_cave_middle": (540, -2448, 136, -2352, -450),
    "s03_cave_bottom": (150, -2900, 230, -3300, -650),
    "e01_cave_east": (1104, -1464, 1592, -1464, LOWER),
    "e02_cave_chest": (1896, -2544, 2048, -2160, -550),
}
LIGHTING_VIEWS = ["r01_roof_start", "l01_lobby_south", "l03_lobby_east_door", "p02_pole_room", "c01_east_corridor",
                  "j02_joust_hall_west", "j03_joust_lane2", "t01_training_room", "a01_range_north", "x01_crate_room",
                  "s01_cave_south", "e01_cave_east", "s03_cave_bottom", "j04_joust_lane4"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
