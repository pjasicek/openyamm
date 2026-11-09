#!/usr/bin/env python3
"""
The Temple of Honk's review tour: eye-level views through its halls, corridors, doorways and scripted objects, in
MM9 (LithTech) coordinates, converted with the map's frame (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_templeofhonk/make_tour.py v01               # the new BLV
    python3 level_generation/projects/mm9r_templeofhonk/make_tour.py v01 --original    # same views, old map

The BLV keeps the old bmodel_world map's frame, so the --original tour uses the same positions; it runs against
output/mm9_rework/assets_original (README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

LOW, MAIN, UPPER = -100, 100, 330      # floor query heights (LT y) of the three storeys
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees])
VIEWS = {
    "entrance": (-1176, 2990, -1176, 2400, LOW),
    "pool_buttons": (-1176, 2700, -1176, 2270, LOW),
    "amphitheatre_west": (-1176, 2450, -1480, 2450, LOW),
    "hall_to_exit": (-1176, 2350, -1176, 3060, LOW),
    "entrance_skylight": (-1176, 2780, -1176, 2632, LOW, 35),
    "vault_door": (-1176, 2030, -1176, 2140, LOW),
    "vault_chests": (-1100, 2100, -1300, 2050, LOW),
    "balcony": (-1176, 2150, -1176, 2800, MAIN),
    "door13_corridor": (-1176, 1890, -1176, 2080, MAIN),
    "northwest_corridor": (-1820, 1930, -400, 1930, MAIN),
    "northwest_corridor_south": (-1790, 1960, -1790, 1480, MAIN),
    "west_wing_hall": (-1220, 950, -1220, 1420, MAIN),
    "west_wing_column": (-2180, 520, -2180, 1420, MAIN),
    "west_room": (-1100, 700, -1250, 330, MAIN),
    "room_door14": (-500, 380, -760, 720, MAIN),
    "south_corridor": (-255, 120, -255, 760, MAIN),
    "south_hall": (-1500, -100, -700, -100, MAIN),
    "south_long_corridor": (-640, -90, 260, -90, MAIN),
    "east_corridor": (685, 290, 685, 810, MAIN),
    "main_hall_length": (-560, 1330, 980, 1330, MAIN),
    "main_hall_pews": (628, 960, 628, 1720, MAIN),
    "main_hall_skylight": (-242, 1130, -242, 1326, MAIN, 40),
    "hall_basement": (150, 300, 150, 720, LOW),
    "altar_hall": (1300, 1328, 2224, 1328, UPPER),
    "altar_hall_across": (1700, 860, 1700, 1820, UPPER),
    "northeast_room": (615, 1860, 615, 2360, MAIN),
    "accountant": (350, 2520, 320, 2840, MAIN),
    "upper_east_corridor": (1424, 380, 1424, 640, UPPER),
    "upper_room_south": (1100, 300, 1100, 620, UPPER),
    "upper_room_north": (1100, 2040, 1100, 2320, UPPER),
}


def main() -> int:
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    project = Project.load(PROJECT)
    tour.write(project, VIEWS, arguments[0] if arguments else "tour", "--original" in sys.argv, settle=1.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
