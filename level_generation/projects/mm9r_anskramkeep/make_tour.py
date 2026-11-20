#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Anskram Keep: eye-level views through its halls, corridors and doorways.
Views are given in MM9 (LithTech) coordinates and converted with the conversion's transform; positions are the
party's feet on the floor below the view point (the game adds the eye height).

    python3 level_generation/projects/mm9r_anskramkeep/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_anskramkeep/make_tour.py <name> --original    # same views, old map

The frame of the BLV is the old bmodel_world map's frame (work/transform.json: no offset), so the --original tour
uses the same positions; it runs against output/mm9_rework/assets_original (see README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[0] / "mm9r_common"))
from dungeon import Project, tour  # noqa: E402

# name: (eye x, eye z, target x, target z) in LithTech units; the target's height is eye level.
VIEWS = {
    "entrance": (0, 40, 0, 600),
    "south_hall": (0, 330, 0, 1300),
    "south_hall_west": (400, 900, -800, 900),
    "south_passage": (0, 1350, 0, 2400),
    "central_hall": (0, 1760, 0, 3300),
    "central_hall_back": (0, 3300, 0, 1800),
    "central_west_door": (-500, 2496, -1100, 2496),
    "north_gates": (0, 3420, 0, 4400),
    "north_hall": (0, 4300, 0, 5900),
    "north_hall_top": (-480, 5950, 500, 5750),
    "north_wing": (-900, 4760, -900, 5500),
    "west_corridor": (-1730, 900, -1730, 2400),
    "west_diagonal": (-1620, 900, -700, 1830),
    "south_corridor": (-1000, 704, -1700, 704),
    "east_hall": (2048, 1650, 2048, 2400),
    "east_corridor": (1728, 1250, 1728, 2200),
    "west_room": (-2200, 900, -2200, 1500),
    # Population views (v03): barracks, officers' rooms, store rooms, the gate, the treasure panel and the cages.
    "barracks_west": (-2130, 820, -2130, 1650),
    "barracks_east": (2120, 1580, 2120, 2420),
    "store_east": (2100, 700, 2120, 1400),
    "officer_east": (700, 2960, 1440, 2960),
    "officer_west": (-700, 2950, -1450, 2950),
    "store_west": (-2120, 3100, -2140, 3560),
    "gate_levers": (0, 3420, 0, 3900),
    "gate_switch": (-80, 3600, -270, 3656),
    "treasure_panel": (1344, 600, 1344, 480),
    "nagate_cage": (1740, 1800, 1650, 1880),
    "icky_cage": (-1280, 1420, -1110, 1300),
    "imp_gate_north": (880, 4420, 1060, 4420),
    "stairs_exit": (0, -60, 0, -200),          # last: it stands in the south exit volume, whose question stays open
}


def main() -> int:
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    # view element 5: the floor query height, the main floor's storey (the shafts and pits lie below it).
    views = {name: (*view, -150) for name, view in VIEWS.items()}
    tour.write(Project.load(PROJECT), views, arguments[0] if arguments else "tour", "--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
