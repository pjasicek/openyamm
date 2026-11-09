#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Thousand Terrors: eye-level views through every part of the map, in MM9
(LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_1000terrors/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_1000terrors/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_1000terrors/make_tour.py lighting<n> [--original]
    level_generation/projects/mm9r_1000terrors/work/run_tour.sh <name> [original] [--set video.lightmaps=false]

The BLV keeps the old map's frame (no offset), so the --original tour runs against output/mm9_rework/assets_original.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

M, L, U = 200, -600, 1500     # floor queries: the entrance level (about 0), the crypts (-1270 .. -750), upper (900 ..)
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    "m01_start": (2032, -6420, 2032, -5600, M),
    "m02_exit": (2032, -6250, 2032, -6800, M),
    "m03_entry_diagonal": (2150, -5450, 2900, -4600, M),
    "m04_central_north": (3100, -4500, 3100, -3000, M),
    "m05_sorc_west": (2450, -3632, 1800, -3632, M),
    "m06_sorc_east": (3700, -3632, 4250, -3632, M),
    "m07_spiral_stair": (3150, -2950, 3150, -2450, M, 15),
    "m08_water_hall_east": (4450, -4764, 6100, -4764, M),
    "m09_water_hall_north": (5540, -5400, 5540, -3700, M),
    "m10_lightning_hall": (6650, -4768, 7150, -4768, M),
    "m11_east_tomb": (6900, -4500, 7300, -4000, M),
    "m12_south_corridor": (5540, -6700, 5540, -8500, M),
    "m13_coffin_octagon": (6000, -6600, 6550, -7100, M),
    "m14_south_hall_west": (5300, -8900, 4300, -8900, M),
    "m15_shooter_plates": (4400, -8894, 5261, -8894, M),
    "m16_puzzle_wall": (3600, -8890, 3900, -8890, M),
    "m17_treasure_room": (3400, -8900, 2700, -8900, M),
    "l01_lever_room": (250, -4650, 700, -4650, L),
    "l02_chess_board": (2560, -6050, 3300, -6050, L),
    "l03_key_chests": (3550, -6040, 3900, -6040, L),
    "l04_skull_head": (3248, -3650, 3248, -4176, L),
    "l05_west_coffins": (-3600, -7136, -2700, -7136, L),
    "l06_genie": (-700, -5120, -960, -5120, L, -10),
    "l07_maze_gate": (-276, -1450, -276, -500, L),
    "l08_lower_hall_west": (-900, -3400, -2500, -3400, L),
    "l09_lower_north_west": (-2600, -2700, -2600, -1700, L),
    "l10_lower_doors": (1100, -3594, 1500, -3594, L),
    "l11_lower_tomb": (-276, -1300, -276, -500, L),
    "l12_lower_south": (-1800, -6000, -1000, -5400, L),
    "u01_foyer": (1404, -6600, 1404, -5300, U),
    "u02_foyer_south_doors": (300, -6550, 252, -6950, U),
    "u03_demon_statues": (1408, -5000, 1408, -4200, U),
    "u04_njam_hall": (2700, -4600, 3700, -4600, U),
    "u05_win_switch": (3488, -4000, 3488, -3650, U),
    "u06_end_hall_south": (3488, -5300, 3488, -4600, U),
    "u07_upper_corridor": (1400, -7160, 1900, -7160, U),
    "u08_lift_top": (1884, -5600, 1884, -5000, U),
}
LIGHTING_VIEWS = ["m01_start", "m04_central_north", "m05_sorc_west", "m08_water_hall_east", "m12_south_corridor",
                  "m17_treasure_room", "l02_chess_board", "l05_west_coffins", "l08_lower_hall_west", "l11_lower_tomb",
                  "u01_foyer", "u03_demon_statues", "u04_njam_hall"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
