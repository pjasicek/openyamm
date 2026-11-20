#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Klusos House: eye-level views through every room of both storeys, in MM9
(LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_klusoshouse/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_klusoshouse/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_klusoshouse/make_tour.py lighting<n> [--original]   # the lighting subset

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
LOWER, UPPER = 60, 230              # the ground floor (0-16 LT, the front hall), the upper floor (176 LT)
VIEWS = {
    # the ground floor
    "l01_front_door": (340, 329, 0, 329, LOWER),
    "l02_front_hall_south": (300, 520, 150, -400, LOWER),
    "l03_front_hall_north": (150, 100, 200, 1000, LOWER),
    "l04_stair_foot": (300, 640, 340, 1000, LOWER),
    "l05_central_room": (-40, 330, -440, 330, LOWER),
    "l06_great_hall_door_south": (-328, 330, -328, 640, LOWER),
    "l07_dining_door": (120, -224, -300, -224, LOWER),
    "l08_dining_room": (-230, -60, -600, -380, LOWER),
    "l09_fireplace_blackheart": (-368, -250, -368, -464, LOWER, 8),
    "l10_kitchen": (-590, 440, -600, 100, LOWER),
    "l11_kitchen_fireplace": (-500, 330, -720, 330, LOWER),
    "l12_great_hall": (-80, 900, -650, 900, LOWER),
    "l13_great_hall_fireplace": (-368, 720, -368, 1180, LOWER),
    "l14_great_hall_gallery": (-560, 1080, -100, 700, LOWER, 18),
    # the upper floor
    "u01_window_start": (-624, -296, -400, -100, UPPER),
    "u02_window": (-520, -300, -720, -300, UPPER),
    "u03_corridor_ew": (-80, -64, -620, -64, UPPER),
    "u04_corridor_ns": (-64, -40, -64, 520, UPPER),
    "u05_gallery_west": (160, 560, -600, 560, UPPER),
    "u06_great_hall_from_gallery": (-350, 580, -350, 1100, UPPER, -25),
    "u07_landing": (256, 700, 256, 1100, UPPER),
    "u08_stair_down": (256, 880, 256, 1060, UPPER, -20),
    "u09_bedroom_east": (200, 300, 40, 120, UPPER),
    "u10_bedroom_middle": (-230, 420, -420, 40, UPPER),
    "u11_bedroom_northwest": (-480, 420, -680, 220, UPPER),
    "u12_bedroom_west": (-480, 30, -690, 160, UPPER),
    "u13_bedroom_south": (-250, -300, -420, -440, UPPER),
    "u14_upper_east": (330, -420, 60, -60, UPPER),
}
LIGHTING_VIEWS = ["l01_front_door", "l03_front_hall_north", "l05_central_room", "l08_dining_room",
                  "l10_kitchen", "l12_great_hall", "u03_corridor_ew", "u04_corridor_ns", "u05_gallery_west",
                  "u09_bedroom_east", "u10_bedroom_middle", "u13_bedroom_south"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
