#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Dook's Castle: eye-level views through the castle and the caves under it, in
MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_dookscastle/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_dookscastle/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_dookscastle/make_tour.py lighting<n> [--original]   # the lighting subset

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original. Views over the lake stand on the bridges, the island or the rim (the tour's
floor query reads MM9's own polygons, which have no water surface).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

CASTLE = 300
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    "c01_gate": (0, 560, 0, 1100, 100),
    "c02_entrance_stair": (0, 650, 0, 1100, 100, 8),
    "c03_entrance_hall_side": (320, 1150, -300, 800, CASTLE),
    "c04_neck": (0, 1250, 0, 1700, 200),
    "c05_corridor_north": (0, 1600, 0, 3000, CASTLE),
    "c06_corridor_south": (0, 3550, 0, 2400, CASTLE),
    "c07_cross_corridor_west": (-150, 2700, -900, 2700, CASTLE),
    "c08_throne_doors": (-992, 2700, -992, 3150, CASTLE),
    "c09_throne_room": (-992, 3300, -992, 4050, CASTLE),
    "c10_throne_side": (-1400, 3450, -700, 3950, CASTLE),
    "c11_armory": (-230, 2050, -650, 2000, CASTLE),
    "c12_office": (-1100, 2200, -992, 1600, CASTLE),
    "c13_bedroom": (-1500, 1920, -2300, 1920, CASTLE),
    "c14_barracks": (230, 2400, 900, 2400, CASTLE),
    "c15_barracks_far": (950, 2450, 250, 2300, CASTLE),
    "c16_shield_room": (450, 3000, 1100, 3550, CASTLE),
    "c17_shield_button": (1024, 3400, 1024, 3648, CASTLE, 5),
    "c18_secret_door": (650, 2960, 300, 2960, CASTLE),
    "c19_stair_down": (200, 2960, 200, 3450, CASTLE, -15),
    "k01_tunnel_west": (200, 3400, 600, 3900, 0),
    "k02_tunnel_mid": (1000, 3300, 1800, 3400, 0),
    "k03_junction": (2200, 3500, 2600, 3100, -300),
    "k04_south_branch": (2400, 2900, 2000, 2500, -300),
    "k05_south_c": (1400, 1900, 1600, 1300, -500),
    "k06_lake_west_tunnel": (2400, 1700, 2900, 1700, -900),
    "k07_lake_from_west": (2600, 1700, 3600, 1600, -1000),
    "k08_island": (3800, 1500, 4600, 1900, -1100),
    "k09_ladder_top": (3620, 1150, 3300, 1500, -1100),
    "k10_north_landing": (3800, 2500, 3900, 1700, -1000, -10),
    "k11_east_bridge": (4800, 1900, 4000, 1700, -900),
    "k12_north_tunnel": (3800, 2850, 3800, 2400, -900),
    "k13_trellborg_cave": (4800, 3500, 5400, 3500, -1200),
    "k14_north_caves_west": (3600, 4100, 3200, 3700, -1100),
    "k15_east_tunnel": (4400, 3700, 4600, 3300, -700),
    "k16_scurry_slope": (4600, 3300, 4400, 3700, -800),
    "k17_far_east": (5000, 4500, 5500, 4300, -900),
    "k18_lake_water": (3800, 1500, 4200, 1300, -1100, -35),
}
LIGHTING_VIEWS = ["c02_entrance_stair", "c05_corridor_north", "c09_throne_room", "c11_armory", "c12_office",
                  "c13_bedroom", "c14_barracks", "c16_shield_room", "k02_tunnel_mid", "k03_junction",
                  "k07_lake_from_west", "k08_island", "k13_trellborg_cave", "k16_scurry_slope", "k18_lake_water"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
