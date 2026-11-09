#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Thronheim City: eye-level views of the east gate, the prison street, the
docks, the centre's squares and lanes, the west town with the temples and Kira's hall, and inside the walk-in shops,
temples and halls, in MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_thronheimcity/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_thronheimcity/make_tour.py <name> --original    # same views, old map

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions. The same
views measure the performance counts (README, "Performance").
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

STREET = 1300                       # floor query height (LT y) at street level
INSIDE = 1340                       # floor query height inside the ground-floor rooms
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # streets and plazas (s02-s19 picked by work/city/street_views.py: far from walls, along the longest clear line)
    "s01_east_gate_start": (5616, 64, 4600, 64, STREET),
    "s02_east_gate_square": (5592, 40, 4819, 247, STREET),
    "s03_prison_street": (4136, 136, 3363, -71, STREET),
    "s04_docks_square": (3032, -72, 3805, 135, STREET),
    "s05_east_lane": (4920, 648, 4227, 248, STREET),
    "s06_bank_street": (5720, 1464, 5027, 1064, STREET),
    "s07_central_square": (3736, 1976, 2936, 1976, STREET),
    "s08_central_square_east": (2440, 1912, 3240, 1912, STREET),
    "s09_centre_south_street": (1256, 1992, 2056, 1992, STREET),
    "s10_northeast_plaza": (3720, 3512, 3720, 2712, STREET),
    "s11_east_street": (4808, 2808, 5501, 2408, STREET),
    "s12_centre_west_lane": (504, 2488, 1197, 2088, STREET),
    "s13_centre_north": (504, 4904, 711, 5677, STREET),
    "s14_docks_exit": (800, 5600, 800, 4700, STREET),
    "s15_west_lane": (-536, 2344, -936, 3037, STREET),
    "s16_west_market": (-1160, 3000, -953, 3773, STREET),
    "s17_west_square": (-1000, 4696, -1773, 4903, STREET),
    "s18_temple_square": (-1912, 4712, -2478, 5278, STREET),
    "s19_northwest_street": (-3352, 5256, -2579, 5049, STREET),
    "s20_roofs_from_square": (3736, 1976, 2936, 2600, STREET, 25),
    # interiors
    "i01_weapons_shop": (780, 1900, 300, 1930, INSIDE),
    "i02_armour_shop": (-430, 4260, -250, 4000, INSIDE),
    "i03_magic_shop": (1290, 4850, 1600, 4864, INSIDE),
    "i04_tavern": (4560, 760, 4504, 1100, INSIDE),
    "i05_apothecary": (5340, 1980, 5504, 1880, INSIDE),
    "i06_town_hall": (3250, 2450, 3072, 2588, INSIDE),
    "i07_library": (4170, 4104, 4420, 4172, INSIDE),
    "i08_the_hall": (-2050, 3450, -1920, 3264, INSIDE),
    "i09_bank": (6260, 1490, 6420, 1488, INSIDE),
    "i10_kira_council": (-4400, 6150, -4400, 6550, INSIDE),
    "i11_temple_rata": (-3232, 4760, -3232, 4400, INSIDE),
    "i12_temple_fre": (-2150, 5520, -1700, 5520, INSIDE),
}


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    tour.write(Project.load(PROJECT, install=False), VIEWS, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
