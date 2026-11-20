#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Drangheim City: eye-level views of the low town round the
temple, the inn and the town hall, the hill district by the west gate and Klusos House, and inside the walk-in shops
and houses, in MM9 (LithTech)
coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_drangheimcity/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_drangheimcity/make_tour.py <name> --original    # same views, old map

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

LOW, HILL = 400, 900                # floor query heights (LT y): the low town (streets 144-250), the hill (576-760)
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # streets and plazas
    "s01_west_gate_start": (4000, -1632, 4600, -1632, HILL),
    "s02_hill_road": (4400, -1900, 5000, -2200, HILL),
    "s03_hill_to_low_town": (5300, -1800, 6200, -1700, HILL),
    "s04_temple_front": (6016, -1650, 6016, -2050, LOW, 6),
    "s05_inn_front": (6950, -1416, 6584, -1416, LOW),
    "s06_well_square": (6600, -700, 6908, -1016, LOW),
    "s07_north_plaza": (6300, -300, 7600, -300, LOW),
    "s08_northeast": (7400, 300, 8200, -100, LOW),
    "s09_east_street": (8150, -1400, 8150, -3000, LOW),
    "s10_town_hall_front": (7584, -1250, 7584, -1750, LOW, 6),
    "s11_tower": (7250, -2800, 7657, -2466, LOW, 8),
    "s12_south_yard": (7000, -3400, 7700, -3900, LOW),
    "s13_training_yard": (8150, -3600, 7700, -3900, LOW),
    "s14_temple_side": (6500, -2600, 6100, -2200, LOW),
    "s15_klusos_front": (5676, -3050, 5676, -3328, HILL, 6),
    "s16_hill_houses": (4450, -3250, 4168, -3496, HILL),
    "s17_hill_south": (5000, -3850, 4300, -3500, HILL),
    "s18_town_from_hill": (5200, -1500, 7000, -1000, HILL, -4),
    "s19_north_wall_walk": (5992, -4010, 6700, -3300, 1000),
    "s20_warehouse_yard": (4750, -1950, 4300, -2500, HILL),
    # interiors (walk-in shops and houses)
    "i01_inn": (6420, -1300, 6300, -900, LOW),
    "i02_temple": (6016, -2200, 6016, -2900, LOW),
    "i03_town_hall": (7584, -1900, 7584, -2400, LOW),
    "i04_blacksmith": (7450, -890, 7230, -890, 250),
    "i05_bank": (8440, -1150, 8100, -900, 250),
    "i06_training_hall": (7650, -4000, 7850, -4050, 250),
    "i07_warehouse": (4300, -2400, 4100, -2700, HILL),
    "i08_spell_shop": (5300, -2500, 5472, -2688, HILL),
    "i09_settlers_house_north": (7150, -50, 7400, 50, LOW),
    "i10_settlers_house_hill": (5350, -1250, 5450, -1000, 600),
    "i11_small_house": (4100, -3400, 4000, -3600, HILL),
    "i12_mayor_upstairs": (7550, -2250, 7424, -2160, 700),
}


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    tour.write(Project.load(PROJECT, install=False), VIEWS, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
