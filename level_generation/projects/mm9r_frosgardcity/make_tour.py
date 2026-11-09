#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Frosgard City: eye-level views of the snow square, the streets round the
free-standing houses, the docks and the frozen harbour, the north gate, and inside the walk-in houses, in MM9
(LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_frosgardcity/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_frosgardcity/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_frosgardcity/make_tour.py sky01 --sky          # the sky sheet

The BLV keeps the old map's frame (no offset), so the --original tour uses the same positions. The same views measure
the performance counts (README, "Performance").
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

STREET = 200                        # floor query height (LT y) in the town (its ground 0-64); the piers and ice their own
PIER = 0                            # the pier deck (-32) under the ice-level floes
INSIDE = 60                         # ground floors (1-17): under the roofs and upper floors (137-151)
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # streets, the square, the docks, the harbour, the gate
    "s01_docks_start": (1664, -4000, 1664, -3000, PIER),
    "s02_pier_harbour_west": (1664, -3500, 400, -3500, PIER),
    "s03_viking_ship": (1700, -3850, 2304, -4128, PIER, -5),
    "s04_square_south": (1700, -1500, 1700, 0, STREET),
    "s05_north_gate_start": (4096, 2700, 4800, 3300, STREET),
    "s06_north_edge": (3500, 2300, 2400, 800, STREET),
    "s07_town_portal_square": (4700, 1250, 3700, 700, STREET),
    "s08_well_square": (450, -320, 1800, -320, STREET),
    "s09_maypole": (1250, -650, 1664, -512, STREET),
    "s10_temple_front": (1664, 250, 1664, 700, STREET, 8),
    "s11_hall_front": (-350, -640, -700, -640, STREET, 5),
    "s12_west_street": (-1200, -100, -1200, 1500, STREET),
    "s13_south_shore": (1000, -2300, 2600, -2200, STREET),
    "s14_east_street": (5300, -1100, 4000, -500, STREET),
    "s15_north_street": (1300, 1900, 3200, 1900, STREET),
    "s16_cannon_hill": (5800, -700, 6400, -900, STREET),
    "s17_town_from_pier": (1664, -3000, 1664, -500, PIER, 10),
    "s18_bank_hatch": (1056, 1950, 1056, 2150, STREET, 3),
    # interiors (walk-in houses)
    "i01_tryggva_hall": (-760, -640, -1472, -620, INSIDE),
    "i02_tavern": (632, -1140, 330, -1500, INSIDE),
    "i03_temple": (1664, 760, 1664, 1344, INSIDE),
    "i04_training_hall": (3300, 832, 3650, 900, INSIDE),
    "i05_shop_203": (2720, 64, 2400, 64, INSIDE),
    "i06_weapons_armour": (3328, -880, 3328, -1150, INSIDE),
    "i07_magic_shop": (4800, 1300, 4800, 1700, INSIDE),
    "i08_house_door7": (-384, 1240, -100, 1600, INSIDE),
    "i09_house_door13": (3904, -1960, 3870, -1750, INSIDE),
    "i10_house_rdoor0": (-192, -2340, -300, -2100, INSIDE),
}
# The sky sheet: three views, each at four times of day (dawn, noon, dusk, night)
SKY_VIEWS = {"s17_town_from_pier": (1664, -3000, 1664, -500, PIER, 20),
             "s02_pier_harbour_west": (1664, -3500, 400, -3500, PIER, 10),
             "s05_north_gate_start": (4096, 2700, 4800, 3300, STREET, 15)}
SKY_TIMES = ("06:30", "12:00", "19:30", "23:30")


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    project = Project.load(PROJECT, install=False)
    if "--sky" not in sys.argv:
        tour.write(project, VIEWS, name, original="--original" in sys.argv)
        return 0
    import yaml
    written = tour.write(project, SKY_VIEWS, name)
    written["settle_seconds"] = 2.0
    written["shots"] = [dict(shot, name=f"{shot['name']}_{time.replace(':', '')}", time=time)
                        for shot in written["shots"] for time in SKY_TIMES]
    (PROJECT / f"review_tour_{name}.yml").write_text(yaml.safe_dump(written, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
