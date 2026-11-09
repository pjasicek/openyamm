#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Drangheim Prison: eye-level views through every room type of its storeys,
in MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_drangheimprison/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_drangheimprison/make_tour.py <name> --original    # same views, old map

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
GATE, MAIN, MIDDLE, FORGE, TOP, LOWER, BOTTOM, CAVE = -800, -700, -560, -120, 40, -1360, -1480, -1740
VIEWS = {
    # the gate storey (floor -872): entrance hall, the corridor, the interrogation block
    "g01_front_door": (-848, -2800, -848, -2400, GATE),
    "g02_entrance_hall": (-1000, -2500, -700, -2640, GATE),
    "g03_entry_door": (-848, -2440, -848, -2200, GATE),
    "g04_corridor_diagonal": (-848, -2200, -520, -1700, GATE),
    "g05_cell_block": (-300, -1700, 460, -1700, GATE),
    "g06_cell": (120, -1880, 120, -1600, GATE),
    "g07_warden_booth": (580, -1700, 480, -1700, GATE),
    "g08_interrogation_room": (-1100, -2144, -1600, -2144, GATE),
    "g09_octagon_hall": (-1000, -1200, -1000, -1500, GATE),
    "g10_east_corridor": (-800, -1450, -300, -1450, GATE),
    # the main storey (floor -744): great hall, kitchen, mess hall, barracks, pens, west cells
    "m01_corridor_744": (-1600, -590, -500, -590, MAIN),
    "m02_great_hall": (-300, -560, 150, -600, MAIN),
    "m03_guard_hall": (560, -800, 900, -500, MAIN),
    "m04_north_arm": (720, -300, 720, 100, MAIN),
    "m05_kitchen": (200, 500, 300, 100, MAIN),
    "m06_coops": (150, 120, 150, 40, MAIN, -5),
    "m07_cow_pen": (340, -120, 200, -120, MAIN),
    "m08_mess_hall": (820, 300, 820, 620, MAIN),
    "m09_barracks": (1000, 300, 1500, 500, MAIN),
    "m10_barracks_north": (1100, 700, 1100, 100, MAIN),
    "m11_south_room": (900, -900, 700, -600, MAIN),
    "m12_west_block": (-2300, -500, -2300, -1500, MAIN),
    "m13_west_cell": (-2500, -1000, -2300, -1000, MAIN),
    "m14_ladder_room": (-120, -170, -210, -170, MAIN),
    # the middle cell block (floor -616), the top cell block (floor -32), the stairs, the smithy
    "c01_middle_block": (-1300, 70, -600, 70, MIDDLE),
    "c02_middle_cell": (-900, 250, -900, 70, MIDDLE),
    "c03_well_head": (-450, 80, -150, 80, MIDDLE),
    "c04_well_shaft": (-240, 82, -150, 82, MIDDLE, -30),
    "t01_top_block": (-1250, 50, -300, 50, TOP),
    "t02_ivsar_cell": (-448, -200, -448, 0, TOP),
    "t03_lever_booth": (-1270, 40, -1320, 40, TOP),
    "t04_top_rotunda": (-120, 40, 150, 100, TOP),
    "t05_stairs_landing": (-1900, -300, -1700, -100, TOP),
    "t06_elevator_doors": (-1450, 300, -1630, 300, TOP),
    "f01_smithy": (-500, -760, -150, -760, FORGE),
    "f02_forge": (-320, -800, -320, -660, FORGE),
    "f03_smithy_corridor": (-1300, -660, -700, -660, FORGE),
    "f04_nw_stairs": (-1700, 470, -1300, 470, -200),
    # the lower storey (floor -1400): the Nagate level
    "l01_stairs": (500, 60, 100, 60, LOWER),
    "l02_cross_corridor": (420, -870, 1700, -870, LOWER),
    "l03_lower_cell": (760, -860, 760, -1100, LOWER),
    "l04_storeroom": (500, -640, 700, -640, LOWER),
    "l05_south_corridor": (410, -1200, 410, -2000, LOWER),
    "l06_south_hall": (700, -2500, 700, -2250, LOWER),
    "l07_ne_hall": (1400, 600, 1400, 100, LOWER),
    "l08_east_hall": (3200, -1600, 3200, -2300, LOWER),
    "l09_east_room": (1250, -1800, 1250, -1400, LOWER),
    "l10_bottom_hall": (-400, -2800, -700, -2800, BOTTOM),
    "l11_crypt": (-420, -3350, -420, -3600, BOTTOM),
    # the cave of the secret way in (floor -1768)
    "v01_secret_start": (208, -240, 300, -500, CAVE),
    "v02_cave_ladder": (500, -620, 570, -620, CAVE),
    "v03_cave_east": (900, -800, 1150, -1150, CAVE),
}
LIGHTING_VIEWS = ["g01_front_door", "g05_cell_block", "g09_octagon_hall", "m02_great_hall", "m05_kitchen",
                  "m09_barracks", "c01_middle_block", "t01_top_block", "f01_smithy", "l02_cross_corridor",
                  "l08_east_hall", "v01_secret_start"]


# The six PerceptionBrushes (shown with hints_input.yml, which gives the party Perception 12).
HINT_VIEWS = {
    "h0_frame": (-446, -200, -446, -51, 40),
    "h1_grate": (-328, -700, -328, -584, -300, 50),
    "h2_panel": (-232, -168, -32, -168, -700),
    "h3_panel": (347, -168, 147, -168, -700),
    "h4_panel": (-184, 338, -184, 138, -760),
    "h5_small": (-1100, -36, -1309, -36, 20),
    "h6_frame_again": (-446, -200, -446, -51, 40),
}


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    views = HINT_VIEWS if name.startswith("hints") else views
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
