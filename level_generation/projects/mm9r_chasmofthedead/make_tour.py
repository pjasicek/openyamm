#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Chasm of the Dead: eye-level views through every room type, from the
entrance from Drangheim down the upper tombs, the canyon and its ledges to the deep halls and the Crona Kiga's crypt, in
MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_chasmofthedead/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_chasmofthedead/make_tour.py <name> --original    # same views, old map
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    # the top tombs (floors 672 / 544)
    "t01_entrance_stair": (-5152, 10900, -5152, 9900, 900),
    "t02_entry_tomb": (-5560, 9960, -4760, 9440, 900),
    "t03_door0_corridor": (-5152, 9150, -5152, 8350, 900),
    "t04_pillar_hall": (-5600, 8250, -4600, 7950, 900),
    "t05_diagonal_chamber_w": (-5880, 8460, -6150, 8640, 900),
    "t06_diagonal_chamber_e": (-4420, 8460, -4150, 8640, 900),
    "t07_closing_walls": (-4960, 7680, -4960, 7230, 900),
    "t08_south_hall": (-5450, 7150, -4800, 6850, 900),
    "t09_west_vault": (-6300, 6950, -6520, 7160, 900),
    "t10_stair_top": (-5216, 6640, -5216, 6200, 900),
    "t11_curved_passage": (-5888, 5960, -5888, 5560, 800),
    # the upper halls (floors 288 / 192)
    "m01_hall1": (-5450, 5200, -4950, 5000, 600),
    "m02_long_stair": (-4780, 5150, -4100, 5000, 600),
    "m03_plate_passage": (-3950, 4930, -3620, 4930, 500),
    "m04_hall2": (-3720, 4950, -3000, 4720, 500),
    "m05_corridor": (-2930, 4440, -2930, 3950, 300),
    "m06_spike_stair": (-2790, 3900, -2180, 3900, 500),
    "m07_hall3": (-2020, 3950, -1560, 3640, 500),
    "m08_south_room": (-1840, 3150, -1840, 2650, 500),
    "m09_tunnel": (-1000, 2950, -300, 3220, 500),
    "m10_tunnel_east": (120, 3900, 360, 4400, 700),
    # the chasm: the ledge path, then the floor
    "c01_ledge_north": (520, 4820, 1600, 5350, 900),
    "c02_ledge_east": (2860, 5450, 2700, 4750, 600),
    "c03_ledge_mid": (1950, 3800, 1880, 2700, 300),
    "c04_ledge_south": (1560, 900, 1050, -350, 100),
    "c05_floor_north": (1500, 5250, 1450, 3900, -1400),
    "c06_floor_mid": (1200, 3450, 1120, 1900, -1400),
    "c07_bridge": (880, 1760, 880, 1000, -1400),
    "c08_canal": (800, 800, 1024, -300, -1400),
    "c09_gate_south": (1008, -150, 1008, -470, -1400),
    "c10_sky": (1250, 3000, 1500, 4500, -1400, 38),
    # the deep halls east of the chasm
    "d01_gate": (3020, 5456, 3560, 5456, -1400),
    "d02_pool_hall": (3300, 4680, 3300, 5950, -1650),
    "d03_octagon": (3900, 4750, 4350, 5250, -1950),
    "d04_north_corridor": (2300, 6448, 3550, 6448, -1900),
    "d05_north_east_vault": (3620, 6680, 4050, 7000, -1900),
    "d06_north_vault": (2260, 6620, 2260, 7050, -1900),
    "d07_acid_grate": (2784, 6250, 2784, 6500, -1900),
    "d08_ring_south": (3560, 4064, 3800, 4200, -1600),
    # the lower tombs
    "l01_stair_down": (-2500, 1424, -3100, 1424, -600),
    "l02_mummy_hall": (-3180, 1424, -3900, 1424, -900),
    "l03_dais": (-3712, 1080, -3712, 1424, -900),
    "l04_diagonal_arm": (-2920, 2500, -2740, 3050, -1000),
    "l05_chest_chamber": (-3080, 3120, -3350, 3250, -1100),
    "l06_tomb_two": (-1520, 2720, -800, 2950, -800),
    "l07_pendulums": (-2130, 1530, -1700, 1880, -600),
    "l08_crusher": (-900, 1800, -520, 1620, -600),
    "l09_south_room": (-2000, 800, -1700, 600, -600),
    "l10_south_hall": (-1540, -160, -1000, -320, -600),
    # south of the chasm
    "s01_corridor": (1008, -920, 1008, -3050, -1500),
    "s02_pivot_trap": (1008, -1480, 1008, -1880, -1500),
    "s03_gallery": (1984, -1400, 1984, -2900, -1500),
    "s04_gallery_hall": (2200, -3300, 2200, -3800, -1500),
    "s05_west_room": (120, -2700, -280, -2700, -1500),
    "s06_tomb_hall": (1008, -4300, 1008, -5300, -1700),
    "s07_crypt": (1008, -6380, 1008, -7200, -1900),
}
LIGHTING_VIEWS = ["t02_entry_tomb", "t04_pillar_hall", "m04_hall2", "c01_ledge_north", "c05_floor_north", "c07_bridge",
                  "d02_pool_hall", "d03_octagon", "l02_mummy_hall", "s01_corridor", "s07_crypt"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
