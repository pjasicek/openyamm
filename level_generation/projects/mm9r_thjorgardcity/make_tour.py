#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Thjorgard City: eye-level views of the docks, the town's streets and
plazas, the north gate, the hillside and Sven's palace terrace, and inside the walk-in shops, halls and the palace,
in MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_thjorgardcity/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_thjorgardcity/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_thjorgardcity/make_tour.py sky01 --sky           # one view, four times

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

STREET = 100                        # floor query height (LT y) at street level; upper floors and the hill pass their own
HILL = 2000
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # streets and plazas
    "s01_docks_start": (256, 0, 256, 1000, STREET),
    "s02_main_street_north": (200, 700, 200, 1700, STREET),
    "s03_town_hall_plaza": (-600, 1300, 900, 1300, STREET),
    "s04_southwest_diagonal": (-1400, 1100, -2600, 0, STREET),
    "s05_southeast_diagonal": (1500, 1200, 2700, 100, STREET),
    "s06_west_gate_start": (-3136, 1280, -2000, 1280, STREET),
    "s07_east_west_street": (-2400, 2350, 2400, 2350, STREET),
    "s08_magic_shop_front": (0, 2850, 0, 2552, STREET, 5),
    "s09_market_street": (-600, 3000, 600, 3000, STREET),
    "s10_store_front": (768, 3850, 768, 3576, STREET, 5),
    "s11_bank_street": (-1920, 4000, -1920, 4300, STREET, 5),
    "s12_forge_street": (-1500, 4100, 2500, 4100, STREET),
    "s13_east_side": (3300, 1800, 3300, 4800, STREET),
    "s14_arena_exit": (3600, 4352, 2600, 4352, STREET),
    "s15_west_side": (-3300, 3000, -3300, 5000, STREET),
    "s16_training_hall_square": (-1000, 5200, 500, 5600, STREET),
    "s17_university_gate": (1100, 4864, 1600, 4864, STREET),
    "s18_north_gate": (-1024, 5600, -1024, 6300, STREET),
    "s19_hill_path": (-900, 6300, -300, 7100, HILL),
    "s20_palace_terrace": (32, 7300, 32, 8800, HILL),
    "s21_hill_from_terrace": (32, 7300, -1500, 6400, HILL, -8),
    "s22_roofs_from_street": (200, 1000, 1200, 2000, STREET, 25),
    # interiors (walk-in shops, halls, the palace)
    "i01_tavern": (-400, 200, -800, 100, STREET),
    "i02_temple": (-2304, -700, -2304, -1100, STREET),
    "i03_town_hall": (256, 1520, 256, 1750, STREET),
    "i04_magic_shop": (0, 2450, 0, 2100, STREET),
    "i05_general_store": (768, 3450, 656, 3280, STREET),
    "i06_apothecary": (-420, 3456, -576, 3520, STREET),
    "i07_library": (-2688, 3600, -2688, 4000, STREET),
    "i08_bank": (-1920, 4400, -1984, 4640, STREET),
    "i09_forge": (-64, 4400, -64, 4700, STREET),
    "i10_armor_shop": (-640, 4350, -800, 4480, STREET),
    "i11_weapon_shop": (512, 4350, 672, 4480, STREET),
    "i12_training_hall": (-520, 5568, -100, 5568, STREET),
    "i13_university": (1700, 4864, 1984, 4864, STREET),
    "i14_palace_hall": (32, 8400, 32, 7900, 1500),
}
# The sky sheet: three views, each at four times of day (dawn, noon, dusk, night)
SKY_VIEWS = {"s22_roofs_from_street": (200, 1000, 1200, 2000, STREET, 25),
             "s21_hill_from_terrace": (32, 7300, -1500, 6400, HILL, 10),
             "s07_east_west_street": (-2400, 2350, 2400, 2350, STREET, 20)}
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
