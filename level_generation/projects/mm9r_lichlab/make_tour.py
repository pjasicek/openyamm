#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Lich Lab: eye-level views through every room type of its four storeys,
in MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_lichlab/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_lichlab/make_tour.py <name> --original    # same views, old map

The BLV keeps the old bmodel_world map's frame (no offset), so the --original tour uses the same positions and runs
against output/mm9_rework/assets_original.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
UPPER, TOP, GROUND, BASEMENT = 700, 1100, 300, -100
VIEWS = {
    # upper storey (floor 512): the entrance from Yorwick, its hall and grand stair, the lobby, the ring round the atrium
    "u01_entrance": (-512, -1690, -512, -900, UPPER),
    "u02_grand_stair": (-512, -1450, -512, -350, UPPER, 8),
    "u03_entrance_west": (-1611, -1700, -1611, -500, UPPER),
    "u04_lobby_corridor": (-1700, -80, 600, -80, UPPER),
    "u05_east_office": (900, -1700, 900, -1100, UPPER),
    "u06_storeroom_b": (-150, 720, -150, 944, UPPER),
    "u07_library": (-400, 280, -400, 900, UPPER),
    "u08_ring_west": (-1990, 1150, -1990, 3650, UPPER),
    "u09_ring_north": (-1900, 3760, 700, 3760, UPPER),
    "u10_atrium_windows": (-1990, 2432, -672, 2432, UPPER, -12),
    "u11_shooting_range": (900, 4130, 100, 4130, UPPER),
    "u12_west_wing": (-2450, 3000, -2450, 4200, UPPER),
    "u13_east_wing": (1700, 2900, 1700, 4100, UPPER),
    "u14_transformer_room": (1700, 1650, 1150, 1800, UPPER),
    "u15_west_stair_tower": (-2700, 560, -3500, 560, UPPER),
    "u16_ring_atrium": (-1990, 1600, -900, 1600, UPPER),
    # top storey (floor 928): the kitchen, the transformer, offices, the engine's crown
    "t01_kitchen": (60, 1300, 400, 1750, TOP),
    "t02_engine_crown": (-1700, 2432, -672, 2432, TOP),
    "t03_transformer_top": (700, 950, 950, 768, TOP),
    "t04_offices_west": (-1450, 1380, -1450, 1850, TOP),
    "t05_logs_room": (-1550, -600, -1550, -1200, TOP),
    "t06_stair_top": (-512, -250, -512, 250, TOP),
    # ground storey (floor 0; north corridor 128): the cross hall over the engine pit, the ring, labs and cages
    "g01_cross_hall": (-672, 1450, -672, 2200, GROUND),
    "g02_cross_hall_east": (300, 2432, -400, 2432, GROUND),
    "g03_west_corridor": (-2560, 1200, -2560, 3400, GROUND),
    "g04_north_corridor": (-2600, 4100, 1500, 4100, GROUND),
    "g05_north_rooms": (-400, 4440, -400, 4800, GROUND),
    "g06_east_lab": (2500, 1250, 2500, 3400, GROUND),
    "g07_throne_room": (1000, 2900, 1000, 3300, GROUND),
    "g08_east_room": (900, 1100, 900, 2200, GROUND),
    "g09_explosion_lab": (-3300, 2700, -3300, 2200, GROUND),
    "g10_west_room": (-3200, 1100, -3200, 1500, GROUND),
    "g11_southwest_hall": (-2000, -150, -2000, 900, GROUND),
    "g12_southeast_stair": (2100, -120, 2900, -120, GROUND),
    "g13_ramp": (1400, -120, 300, -120, GROUND),
    "g14_east_lab_case": (2550, 2368, 2816, 2368, GROUND),
    # basement (floor -256): the engine hall and its pods, the summoner's ghost pools, the column room
    "b01_engine_hall": (-1500, 1400, -672, 2432, BASEMENT),
    "b02_engine_pods": (-1100, 2000, -672, 2432, BASEMENT),
    "b03_ghost_pools": (-256, -560, -256, -1500, BASEMENT),
    "b04_column_room": (-650, 300, -650, 1100, BASEMENT),
}


# The lighting compare (MM9 original | native unbaked | native baked): one view per storey and room kind.
LIGHTING_VIEWS = ["u01_entrance", "u04_lobby_corridor", "u08_ring_west", "u16_ring_atrium", "t01_kitchen",
                  "t02_engine_crown", "g01_cross_hall", "g04_north_corridor", "g06_east_lab", "g09_explosion_lab",
                  "b01_engine_hall", "b03_ghost_pools"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
