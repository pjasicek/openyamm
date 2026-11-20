#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Sturmford City: eye-level views of the docks, the palace ring, the
temple square, the north streets and the market, and inside the walk-in shops and houses, in MM9 (LithTech)
coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_sturmfordcity/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_sturmfordcity/make_tour.py <name> --original    # same views, old map

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original. The same views measure the performance counts (README, "Performance").
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

STREET = 7800                       # floor query height (LT y) at street level; upper floors pass their own
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # streets and plazas
    "s01_docks_start": (816, -380, 816, 600, STREET),
    "s02_docks_plaza_west": (1300, 100, 100, 100, STREET),
    "s03_docks_lane_north": (2400, 600, 2400, 1500, STREET),
    "s04_palace_ring_south": (1800, 1420, 3200, 1420, STREET),
    "s05_palace_ring_west": (400, 2300, 400, 4000, STREET),
    "s06_palace_front": (1900, 2400, 1900, 2850, STREET, 8),
    "s07_palace_ring_east": (3300, 2000, 3300, 4000, STREET),
    "s08_palace_ring_north": (2600, 4000, 600, 4000, STREET),
    "s09_town_gate": (1700, 4400, 1700, 5200, STREET),
    "s10_temple_square": (-200, 4700, -1700, 5300, STREET),
    "s11_temple_front": (-400, 5250, -900, 5250, STREET, 10),
    "s12_north_street": (1600, 5500, 1600, 6500, STREET),
    "s13_well_square": (2600, 6200, 2200, 6500, STREET),
    "s14_north_lane_west": (1400, 6900, -1000, 6900, STREET),
    "s15_northwest_corner": (-900, 7000, -900, 6200, STREET),
    "s16_shops_row": (1000, 7250, 1900, 7350, STREET),
    "s17_east_street": (3200, 7100, 4400, 7100, STREET),
    "s18_market": (4700, 7100, 5700, 6800, STREET),
    "s19_north_gate_plaza": (3600, 5600, 4400, 5650, STREET),
    "s20_roofs_from_ring": (1200, 2300, 2400, 3200, STREET, 25),
    # interiors (walk-in shops and houses)
    "i01_tavern": (-150, 100, -450, 300, STREET),
    "i02_tavern_bar": (-250, -200, -344, 405, STREET),
    "i03_general_store": (3700, 1700, 3810, 1350, STREET),
    "i04_town_hall": (1850, 1800, 2300, 1800, STREET),
    "i05_library": (3800, 2600, 3800, 2000, STREET),
    "i06_bank": (3750, 3400, 3700, 2950, STREET),
    "i07_palace_hall": (1300, 3200, 2800, 3200, STREET),
    "i08_church": (-800, 5250, -1700, 5250, STREET),
    "i09_armorer": (300, 7180, 24, 7168, STREET),
    "i10_blacksmith": (560, 7400, 592, 7700, STREET),
    "i11_magic_shop": (1800, 7300, 1792, 7600, STREET),
    "i12_house_ludwig": (1850, 1050, 1682, 938, STREET),
}


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    tour.write(Project.load(PROJECT, install=False), VIEWS, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
