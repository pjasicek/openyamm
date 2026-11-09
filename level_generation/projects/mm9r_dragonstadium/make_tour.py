#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Dragon Stadium: eye-level views by hand (the map is one bowl and two tunnels),
in MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py). The BLV keeps the
old map's frame (no offset), so --original writes the same shots for the old map.

    python3 level_generation/projects/mm9r_dragonstadium/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_dragonstadium/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_dragonstadium/make_tour.py lighting<n> [--original]   # lighting subset
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units. Arena floor y -64; pillar
# plinths p1 (LT x -128..512, z -992..-128), p2 (-384..512, 896..1760), p3 (1472..2400, 0..864); the Dragon King at
# (728, 288); the chests at (576, 1216) and (1568, 736).
VIEWS = {
    "a01_start": (704, -2240, 704, -1800, 200),
    "a02_tunnel": (740, -2000, 760, -1500, 200),
    "a03_arena_mouth": (760, -1650, 760, 0, 300),
    "a04_exit": (704, -2300, 916, -2592, 200),
    "a05_side_tunnel": (1100, -2640, 1600, -2480, 600),
    "a06_side_tunnel_up": (1800, -2560, 2400, -2850, 900),
    "a07_back_to_start": (760, -1500, 704, -2240, 300),
    "b01_arena_south": (1300, -1100, 800, 800, 300),
    "b02_arena_centre_north": (800, -300, 800, 2000, 300),
    "b03_arena_west": (-900, 300, 1500, 300, 300),
    "b04_arena_east": (2800, 300, 0, 300, 400),
    "b05_arena_north": (800, 2000, 800, -1200, 400),
    "b06_arena_northeast": (2400, 1700, 200, -500, 400),
    "b07_arena_northwest": (-700, 1900, 1800, -500, 400),
    "b08_arena_southwest": (-800, -800, 1800, 1500, 400),
    "b09_arena_southeast": (2300, -700, 0, 1500, 400),
    "c01_p1_south": (192, -1350, 192, -560, 300, 18),
    "c02_p1_east": (950, -560, 192, -560, 300, 15),
    "c03_p2_south": (100, 550, 64, 1328, 300, 18),
    "c04_p2_east": (950, 1328, 64, 1328, 300, 15),
    "c05_p3_west": (1050, 432, 1936, 432, 300, 15),
    "c06_p3_south": (1936, -450, 1936, 432, 300, 18),
    "d01_chest0": (576, 950, 576, 1216, 300, -12),
    "d02_chest1": (1300, 600, 1568, 736, 300, -12),
    "d03_bones": (830, -720, 830, -400, 300, -15),
    "d04_dragon_place": (728, -700, 728, 288, 300, 12),
}
LIGHTING_VIEWS = ["a01_start", "a02_tunnel", "a03_arena_mouth", "a04_exit", "a05_side_tunnel", "b01_arena_south",
                  "b03_arena_west", "b05_arena_north", "b06_arena_northeast", "c01_p1_south", "c05_p3_west",
                  "d01_chest0"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    original = "--original" in sys.argv
    views = dict(VIEWS)
    if name.startswith("lighting"):
        views = {k: views[k] for k in LIGHTING_VIEWS}
    tour.write(Project.load(PROJECT, install=False), views, name, original=original)
    return 0


if __name__ == "__main__":
    sys.exit(main())
