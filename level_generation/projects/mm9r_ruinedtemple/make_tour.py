#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Ruined Temple: eye-level views from the entrance from Frosgard down
through the skylight hole into the hall, the main temple and its gallery, the side rooms, the pew hall and the
elevator, the crypt, the shaft and the spiral ramps, in MM9 (LithTech) coordinates, converted by the shared tour helper
(../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_ruinedtemple/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_ruinedtemple/make_tour.py <name> --original    # same views, old map
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
    # the entrance hall: the upper floor by the exit, the skylight box over the hole, the hall below
    "e01_start": (0, -335, 0, -800, -500),
    "e02_skylight_box": (70, -420, 0, -700, -500, -15),
    "e03_lower_hall": (0, -900, 0, -400, -750),
    "e04_hole_from_below": (60, -480, 0, -700, -750, 40),
    "e05_updoor": (-120, -700, -400, -690, -750),
    "e06_south_stairs": (0, -820, 0, -1300, -750),
    "e07_south_corridor": (-600, -1360, 600, -1360, -700),
    "e08_altar_stair": (0, -560, 0, -100, -750),
    # the main temple: the sunken floor, the lamp, the gallery and LeftDoor
    "t01_temple": (0, -40, 0, 500, -750),
    "t02_temple_diagonal": (230, 40, -250, 480, -750),
    "t03_lamp": (0, 120, 0, 256, -750, -20),
    "t04_gallery_leftdoor": (300, 480, 420, 480, -600),
    "t05_west_ramp": (-544, -170, -544, 400, -700),
    "t06_temple_north": (0, 520, 0, 900, -750),
    # the side rooms east: room 3, HiddenDoor2, the spiral stair, cave-in B
    "s01_room3": (620, 300, 820, 480, -600),
    "s02_hiddendoor2": (704, 450, 704, 660, -600),
    "s03_spiral": (800, 760, 620, 900, -700),
    "s04_cavein_b": (840, 760, 560, 1010, -850),
    "s05_chest_room": (450, 1420, 450, 1660, -750),
    "s06_hiddendoor3": (592, 1040, 592, 1240, -850),
    # north: the diagonal corridor, cave-in A, the pew hall, the elevator room
    "n01_diagonal_corridor": (0, 650, 0, 1050, -750),
    "n02_cavein_a": (-50, 1300, -350, 1300, -750),
    "n03_pews": (-450, 1300, -1000, 1300, -750),
    "n04_podium": (-780, 1450, -1000, 1350, -750),
    "n05_hiddendoor": (-864, 1450, -864, 1660, -750),
    "n06_buttons": (-880, 1700, -880, 1860, -750),
    # below: the prison corridor, the crypt hall, the cell, the ladder
    "c01_lift_foot": (-620, 1810, -900, 1810, -1000),
    "c02_prison_corridor": (-760, 1810, -250, 1810, -1000),
    "c03_crypt_hall": (250, 1850, 100, 2150, -1000),
    "c04_cell": (96, 2150, 96, 2320, -1000),
    "c05_ladder": (390, 1900, 390, 1760, -1050, 20),
    # the shaft bottom, the spiral ramps, the tunnel
    "d01_shaft_bottom": (100, 2250, 180, 2470, -1700),
    "d02_ramps": (-60, 2620, 340, 2620, -1600, 10),
    "d03_tunnel": (100, 2470, 0, 2360, -1100),
}
LIGHTING_VIEWS = ["e01_start", "e03_lower_hall", "t01_temple", "t04_gallery_leftdoor", "s01_room3", "s05_chest_room",
                  "n01_diagonal_corridor", "n03_pews", "c02_prison_corridor", "c03_crypt_hall", "d02_ramps"]


# The views with props (banners, pews, chests, the crate, the lamp, the sarcophagus) for the prop-lighting comparison.
PROP_VIEWS = ["e03_lower_hall", "t03_lamp", "s05_chest_room", "s06_hiddendoor3", "n03_pews", "n04_podium",
              "c03_crypt_hall"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    if name.startswith("props"):
        views = {k: VIEWS[k] for k in PROP_VIEWS}
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
