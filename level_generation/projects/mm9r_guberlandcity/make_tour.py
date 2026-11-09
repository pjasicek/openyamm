#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Guberland City: eye-level views of the gate, the north and south
avenues, the palace plaza, the four walled quarters and their gates, and inside the walk-in shops, the tavern and its
stage, the temple, the palace and its throne room, in MM9 (LithTech) coordinates, converted by the shared tour helper
(../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_guberlandcity/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_guberlandcity/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_guberlandcity/make_tour.py sky01 --sky           # one view, four times

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

STREET = 100                        # floor query height (LT y): one storey everywhere
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # streets, plazas and gates (most picked from the street air: work/city/street_views.py)
    "s01_gate_start": (-256, -150, -256, -1200, STREET),
    "s02_north_avenue": (-248, -408, -248, -1208, STREET),
    "s03_north_avenue_south": (-256, -1400, -256, -2600, STREET),
    "s04_plaza_east": (900, -2900, -300, -3584, STREET),
    "s05_well": (650, -3300, 256, -3584, STREET),
    "s06_palace_front": (100, -3584, -264, -3584, STREET, 5),
    "s07_east_arm_gates": (1200, -3584, 2600, -3584, STREET),
    "s08_west_arm": (-1800, -3584, -3000, -3584, STREET),
    "s09_west_gates": (-2744, -3608, -1944, -3608, STREET),
    "s10_south_avenue": (-248, -4504, -248, -5304, STREET),
    "s11_south_square": (-248, -6000, -248, -7200, STREET),
    "s12_south_square_east": (296, -7096, -397, -6696, STREET),
    "s13_nw_quarter": (-1688, -2056, -1688, -1256, STREET),
    "s14_nw_quarter_north": (-1672, -824, -1672, -1624, STREET),
    "s15_nw_quarter_west": (-2920, -2056, -2120, -2056, STREET),
    "s16_ne_quarter": (1000, -1272, 1000, -2072, STREET),
    "s17_ne_quarter_north": (632, -616, 632, -1416, STREET),
    "s18_ne_quarter_south": (728, -2312, 1528, -2312, STREET),
    "s19_se_quarter": (520, -5672, 520, -4872, STREET),
    "s20_se_quarter_east": (1928, -3900, 1928, -4700, STREET),
    "s21_sw_quarter": (-1912, -5864, -1112, -5864, STREET),
    "s22_sw_quarter_north": (-1512, -4472, -712, -4472, STREET),
    "s23_sw_quarter_west": (-2632, -4408, -3405, -4201, STREET),
    "s24_roofs_from_street": (1000, -1272, 1600, -1900, STREET, 25),
    # interiors (the tavern and its stage, the temple, the palace, the shops)
    "i01_tavern_audience": (-1150, -1900, -1024, -1400, STREET),
    "i02_tavern_bar": (-950, -1900, -640, -1760, STREET),
    "i03_temple": (-2304, -3000, -2304, -2400, STREET),
    "i04_palace_hall": (-350, -3584, -760, -3584, STREET),
    "i05_throne_room": (-850, -3584, -1200, -3584, STREET),
    "i06_bank": (350, -1728, 700, -1728, STREET),
    "i07_magic_shop": (1024, -950, 1024, -650, STREET),
    "i08_smithy": (-1000, -5050, -1500, -5250, STREET),
    "i09_weapon_shop": (-1150, -5050, -850, -5250, STREET),
    "i10_apothecary_hall": (800, -4800, 900, -5500, STREET),
    "i11_book_shop": (750, -5000, 900, -4900, STREET),
    "i12_portal_house": (2150, -5000, 2200, -5300, STREET),
    "i13_stage": (-1200, -1430, -800, -1430, STREET),
    "i14_tavern_side_room": (-1420, -2120, -1330, -1900, STREET),
}
# The sky sheet: three views, each at four times of day (dawn, noon, dusk, night)
SKY_VIEWS = {"s24_roofs_from_street": (1000, -1272, 1600, -1900, STREET, 25),
             "s11_south_square": (-248, -6000, -248, -7200, STREET, 15),
             "s07_east_arm_gates": (1200, -3584, 2600, -3584, STREET, 20)}
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
