#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Inventa Storca: eye-level views through every room type of its two storeys,
the cave shaft and the flooded cavern, in MM9 (LithTech) coordinates, converted by the shared tour helper
(../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_inventastorca/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_inventastorca/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_inventastorca/make_tour.py lighting_<x> [--original]   # the lighting subset

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
UPPER, LOWER = -250, -560
VIEWS = {
    # the upper storey (floor -336): the entrance, the dead adventurers' halls, the long halls, the reading rooms
    "u01_start": (144, 60, -500, 100, UPPER),
    "u02_exit_stair": (144, -110, 176, -300, UPPER),
    "u03_entrance_corridor": (-300, 100, -760, 100, UPPER),
    "u04_side_hall": (-900, 0, -900, 380, UPPER),
    "u05_green_party_hall": (-1200, 0, -1750, 150, UPPER),
    "u06_green_party_south": (-1450, -420, -1450, 300, UPPER),
    "u07_purple_hall": (-1850, 0, -2500, 50, UPPER),
    "u08_north_hall": (-2650, 300, -3500, 250, UPPER),
    "u09_long_hall_north": (-3328, -150, -3328, -1100, UPPER),
    "u10_long_hall_south": (-3328, -1900, -3328, -2950, UPPER),
    "u11_west_hall_north": (-4180, -120, -4180, -1100, UPPER),
    "u12_west_hall_south": (-4180, -1350, -4180, -2500, UPPER),
    "u13_dresser": (-4380, -790, -4560, -790, UPPER),
    "u14_cage_wall": (-3870, -220, -3870, 40, UPPER),
    "u15_reading_room": (-2300, -1380, -2230, -1950, UPPER),
    "u16_corridor_west": (-2960, -1360, -2620, -1360, UPPER),
    "u17_spiral_room": (-1680, -1330, -1900, -1620, UPPER),
    "u18_cavern_walkway": (-1820, -660, -2450, -820, UPPER),
    "u19_cavern_water": (-1950, -700, -2150, -950, UPPER, -35),
    "u20_lich_study": (-1350, -2700, -1900, -2850, UPPER),
    "u21_ladder_room": (-1050, -2850, -720, -2680, UPPER),
    "u22_south_corridor": (-2900, -2680, -2150, -2680, UPPER),
    "u23_cracked_wall2": (-2200, -1370, -1900, -1370, UPPER),
    "u24_dead_party": (-2100, 100, -2330, 60, UPPER, -10),
    "u25_dying_adventurer": (-2950, 180, -3200, 180, UPPER),
    # the lower storey (floor -640): the library halls, the bookcases, the cave shaft, the well
    "l01_ladder_hall": (-760, -2450, -720, -2740, LOWER),
    "l02_lower_west_hall": (-900, -2200, -900, -1300, LOWER),
    "l03_lower_north_hall": (-750, -1300, -60, -1300, LOWER),
    "l04_bookcases": (-80, -2240, -300, -1700, LOWER),
    "l05_east_reading_room": (90, -1100, 450, -1700, LOWER),
    "l06_lower_hall": (330, -600, -300, -900, LOWER),
    "l07_cave_floor": (-330, -450, -200, -100, LOWER),
    "l08_cave_shaft": (-330, -450, -200, -100, LOWER, 50),
    "l09_well": (-940, -1196, -1072, -1196, LOWER, -20),
    "l10_cave_wall_from_hall": (-172, -720, -172, -450, LOWER),
    "l11_bookcase_switch": (-80, -2000, -280, -1896, LOWER),
}
LIGHTING_VIEWS = ["u01_start", "u05_green_party_hall", "u08_north_hall", "u09_long_hall_north", "u11_west_hall_north",
                  "u15_reading_room", "u18_cavern_walkway", "u20_lich_study", "l02_lower_west_hall", "l04_bookcases",
                  "l06_lower_hall", "l07_cave_floor"]

# The scripted objects open: an input tour (write_input) runs their events at launch through the debug console, the
# screenshot tour waits for them (a first wait shot, settle 4 s).
OPEN_EVENTS = [170, 171, 172, 173, 180, 181, 182, 183, 190, 191, 133, 144, 145, 156]
OPEN_VIEWS = {
    "o00_wait": (144, 60, -500, 100, UPPER),
    "o01_bookcases_fallen": (-80, -2240, -300, -1700, LOWER),
    "o02_bookcases_aisle": (-430, -1650, -250, -2100, LOWER),
    "o03_secret_panel_niche": (380, -1400, 484, -1400, LOWER, -5),
    "o04_secret_panel0_niche": (-648, -2650, -648, -2790, LOWER, 10),
    "o05_floor_compartment": (-256, -1560, -256, -1640, LOWER, -55),
    "o06_broken_wall0": (-276, 150, -276, -100, UPPER),
    "o07_broken_wall2": (-2200, -1370, -1900, -1370, UPPER),
    "o08_broken_wall3": (-800, -1190, -1050, -1190, LOWER),
    "o09_cage_open": (-3870, -220, -3870, 60, UPPER),
    "o10_ceiling_hole": (-1450, -2768, -1632, -2768, UPPER, 35),
    "o11_dresser_open": (-4380, -790, -4560, -790, UPPER, -10),
    "o12_trapdoor_open": (-720, -2560, -720, -2680, UPPER, -40),
}
# The perception hints at Perception 10 (every brush's PerceptionValue).
HINT_VIEWS = {
    "h00_wait": (144, 60, -500, 100, UPPER),
    "h01_cracked_wall0": (-276, 150, -276, -100, UPPER),
    "h02_switch_panel": (380, -1500, 484, -1530, LOWER),
    "h03_switch0": (-760, -2650, -790, -2790, LOWER),
    "h04_trapdoor": (-720, -2560, -720, -2680, UPPER, -40),
    "h05_cracked_wall2": (-2200, -1370, -1900, -1370, UPPER),
    "h06_desk_drawer": (-2250, -1850, -2300, -1915, UPPER, -25),
    "h07_bookcase_switch": (-80, -2000, -280, -1896, LOWER),
}


def write_input(name: str, lines: list[str], wait: float) -> Path:
    """An input tour (debug.menu_input_tour_path) that runs console lines at launch and waits for the shots."""
    path = PROJECT / f"input_{name}.yml"
    steps = ["  - wait: 2"] + [f"  - console: {line}" for line in lines] + [f"  - wait: {wait}"]
    path.write_text(f"# Written by make_tour.py: console lines for the {name} review tour.\n"
                    f"output_dir: {PROJECT / 'review' / name}_input\nsteps:\n" + "\n".join(steps) + "\n")
    print(path)
    return path


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    settle = 1.5
    if name.startswith("open"):
        views, settle = OPEN_VIEWS, 4.0
        write_input(name, [f"event {e}" for e in OPEN_EVENTS], 120)
    elif name.startswith("hints"):
        views, settle = HINT_VIEWS, 4.0
        write_input(name, ["skill set Perception 10 B"], 90)
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv, settle=settle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
