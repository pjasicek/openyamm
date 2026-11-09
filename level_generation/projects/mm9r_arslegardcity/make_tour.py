#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Arslegard City: eye-level views of the Great Gate, the streets and
squares, the park, the fountain court by the Hall of the Gods' gate, and inside the walk-in shops and houses, in MM9
(LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_arslegardcity/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_arslegardcity/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_arslegardcity/make_tour.py sky<n>               # four times of day

The BLV's frame is shifted by overrides.yml `offset` (y -20 000); the old map keeps MM9's frame, so the --original tour
adds the offset back to every position. The first shot of a BLV tour sets key 98 (`qbit set 90098`): FateMan.scr's
outcome (the move to the Dark Passageway, about 3 s after a first arrival) would end the tour otherwise.
The same views measure the performance counts (README, "Performance").
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

STREET = -100                       # floor query height (LT y) at street level; raised places pass their own
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # the gate, the streets and squares
    "s01_gate_start": (5625, -6880, 5625, -7800, STREET),
    "s02_great_gate": (5625, -7150, 5625, -6450, STREET, 12),
    "s03_north_street_west": (2700, -7400, 800, -7400, STREET),
    "s04_north_street_east": (5600, -7100, 4000, -7100, STREET),
    "s05_bank_square": (2500, -8300, 3300, -7300, STREET),
    "s06_main_street_south": (4400, -7400, 4400, -9000, STREET),
    "s07_tavern_street": (5000, -8000, 6000, -8000, STREET),
    "s08_temple_square": (2000, -7950, 1100, -7950, STREET, 8),
    "s09_temple_front": (2300, -8500, 1120, -7968, STREET, 8),
    "s10_west_street": (2000, -8900, 2000, -10400, STREET),
    "s11_park": (1500, -9300, 300, -11500, 400),
    "s12_park_cliffs": (500, -12300, 1500, -10000, 400),
    "s13_fountain_well": (4700, -9852, 5146, -9852, STREET),
    "s14_east_street": (6300, -9200, 6300, -7500, STREET),
    "s15_library_street": (1500, -10600, 2600, -10100, STREET),
    "s16_south_street": (5000, -12400, 5000, -11000, STREET),
    "s17_south_west": (2000, -12700, 2000, -11500, STREET),
    "s18_hall_court": (6800, -12400, 7700, -12400, 400),
    "s19_njam_lane": (2300, -11300, 3300, -11700, STREET),
    "s20_gate_path": (5632, -5900, 5632, -4800, 400),
    # interiors (walk-in shops and houses)
    "i01_tavern": (6000, -8300, 6400, -8500, STREET),
    "i02_bank": (3000, -7550, 3000, -7300, STREET),
    "i03_magic_shop": (3040, -8350, 3040, -8550, STREET),
    "i04_temple": (900, -7968, 0, -7968, 300),
    "i05_library": (2000, -10112, 2300, -10112, STREET),
    "i06_weapons": (4530, -9690, 4352, -9920, STREET),
    "i07_armour": (3860, -10820, 3680, -10640, STREET),
    "i08_general_store": (5552, -10450, 5552, -11500, STREET),
    "i09_general_store_south": (4528, -11500, 4528, -10500, STREET),
    "i10_training_hall": (6600, -10112, 7100, -10112, STREET),
    "i11_njam_house": (3000, -11650, 3000, -11300, STREET),
    "i12_sven_court": (6100, -12160, 5888, -12163, 100),
}
SKY_VIEWS = {"temple_square": VIEWS["s03_north_street_west"][:5] + (15,), "park": VIEWS["s17_south_west"][:5] + (15,)}
SKY_TIMES = ["06:30", "12:00", "19:30", "23:30"]
FATE_KEY = "qbit set 90098"


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    original = "--original" in sys.argv
    project = Project.load(PROJECT, install=False)
    views = VIEWS
    if name.startswith("sky"):
        views = {f"{time.replace(':', '')}_{label}": view for time in SKY_TIMES for label, view in SKY_VIEWS.items()}
    result = tour.write(project, views, name, original=original)
    path = PROJECT / f"review_tour_{name}{'_original' if original else ''}.yml"
    if name.startswith("sky"):
        for shot in result["shots"]:
            shot["time"] = shot["name"][:2] + ":" + shot["name"][2:4]
    if original:                      # the old map's frame: native + offset
        for shot in result["shots"]:
            shot["position"] = [int(round(v + o)) for v, o in zip(shot["position"], project.offset)]
    else:
        result["shots"][0]["commands"] = [FATE_KEY]
    path.write_text(yaml.safe_dump(result, sort_keys=False))
    print("first shot", result["shots"][0]["position"], result["shots"][0].get("commands"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
