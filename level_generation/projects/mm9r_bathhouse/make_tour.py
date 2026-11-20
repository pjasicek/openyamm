#!/usr/bin/env python3
"""
The Bathhouse's review tour: eye-level views in MM9 (LithTech) coordinates, converted with the map's frame
(../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_bathhouse/make_tour.py v01               # the new BLV
    python3 level_generation/projects/mm9r_bathhouse/make_tour.py v01 --original    # same views, old map
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

UP, MID, LOW = 100, -100, -400       # floor query heights (LT y): halls, the drain room's ledge, the channels
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees])
PROBE = {
    "entrance": (-300, -350, 400, -350, UP),
    "hall_pool": (100, 300, 1500, -300, UP),
    "hall_north": (300, 650, 300, 830, UP),
    "sw_pool": (200, -1400, 450, -1700, UP),
    "boil_b": (850, -1300, 950, -1700, UP),
    "boil_a": (1750, -1300, 1900, -1800, UP),
    "furnace": (1440, -1700, 1440, -2100, UP),
    "tub": (2500, -1450, 2300, -1750, UP),
    "vents": (2500, -2120, 2900, -2120, UP),
    "east_rooms": (2700, -1000, 3200, -1500, UP),
    "diag": (3300, -950, 3550, -550, UP),
    "stairs_top": (3976, -650, 3976, 100, UP),
    "flood_ledge": (4350, 100, 5200, 100, MID),
    "flood_floor": (4900, -100, 4300, -100, MID - 300, -10),
    "alcove": (3640, -100, 3640, 100, -390),
    "channel14": (2500, -480, 3200, -480, -500),
    "east_corr": (5900, -300, 5900, 600, MID),
    "chests": (6100, -1500, 6300, -1800, MID),
}
VIEWS = {
    "entrance": (-300, -350, 400, -350, UP),
    "hall_pool": (100, 300, 1500, -300, UP),
    "hall_east": (2400, 0, 0, 0, UP),
    "hall_colonnade": (1300, -950, -100, -950, UP),
    "hall_north_doors": (1200, 300, 1200, 700, UP),
    "room_a": (250, 800, 600, 800, UP),
    "room_b": (1550, 800, 1900, 650, UP),
    "room_c": (2300, 800, 2500, 700, UP),
    "ne_corridor": (2650, 800, 2650, -400, UP),
    "ne_room": (2950, 250, 3150, 150, UP),
    "corridor2": (1300, -1200, 2500, -1200, UP),
    "sw_room": (0, -1300, 0, -1800, UP),
    "sw_pool": (200, -1400, 450, -1700, UP),
    "pool_b": (720, -1350, 950, -1750, UP),
    "furnace": (1440, -1700, 1440, -2100, UP),
    "pool_a": (1700, -1950, 1900, -1500, UP),
    "tub": (2500, -1450, 2300, -1750, UP),
    "vents": (2500, -2120, 2900, -2120, UP),
    "east_room": (2700, -1000, 3100, -1500, UP),
    "diagonal": (3250, -950, 3550, -550, UP),
    "stairs_top": (3976, -650, 3976, 100, UP),
    "flood_ledge": (4350, 100, 5200, 100, MID),
    "flood_floor": (4900, -100, 4300, -100, MID - 300),
    "flood_doors": (5550, -100, 5770, -100, -200),
    "east_corridor": (5900, -300, 5900, 600, MID),
    "chests_south": (6100, -1500, 6300, -1800, MID),
    "switch_room": (3600, -450, 3500, 100, LOW),
    "switch_shelf": (3620, -100, 3700, 74, -390),
    "chamber": (1100, -300, 1700, -300, LOW),
    "chamber_channel": (1700, -100, 1846, -600, LOW),
    "door0_hall": (32, -850, 32, -1110, UP),
    "valve": (1436, -2150, 1436, -2040, UP),
    "tub_ebora": (2030, -1660, 2330, -1720, UP),
    "door5": (2700, -1240, 2550, -1240, UP),
    "ladder": (3530, 40, 3580, 116, LOW),
    "chamber_scroll": (1350, -250, 1100, -441, LOW),
    "flood_stairs_foot": (3976, -100, 4600, 50, -300),
    "east_corridor_south": (5950, -1000, 5950, -1700, MID),
}


def main() -> int:
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    project = Project.load(PROJECT)
    name = arguments[0] if arguments else "tour"
    views = PROBE if name == "probe" else VIEWS
    tour.write(project, views, name, "--original" in sys.argv, settle=1.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
