#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Lindisfarne Monastery: eye-level views through every room, in MM9
(LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_lindisfarnemonastery/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_lindisfarnemonastery/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_lindisfarnemonastery/make_tour.py lighting<n> [--original]

The BLV keeps the old map's frame (no offset), so the --original tour runs against output/mm9_rework/assets_original.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

G, U, L, T = 100, 420, 930, 1300     # floor queries: ground (0), galleries (384), loft (896), bell tower (1264)
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    "g01_narthex_start": (-128, -365, -128, 400, G),
    "g02_front_door_out": (-128, -250, -128, -1200, G),
    "g03_nave_north": (-128, 600, -128, 2200, G),
    "g04_nave_south": (-128, 2200, -128, 600, G),
    "g05_crossing_east": (-128, 2600, 800, 2600, G),
    "g06_crossing_west": (-128, 2600, -1100, 2600, G),
    "g07_choir_north": (-128, 3000, -128, 4600, G),
    "g08_altar": (-128, 4250, -128, 4800, G, 10),
    "g09_choir_south": (-128, 4300, -128, 3000, G),
    "g10_courtyard_ne": (600, 1000, 1500, 1800, G),
    "g11_fountain": (1500, 700, 1000, 1400, G),
    "g12_cloister_east": (2200, 600, 2200, 2200, G),
    "g13_cloister_south": (1700, 300, 600, 300, G),
    "g14_thjorad": (2450, 2400, 2800, 2350, G),
    "g15_ne_hall": (2200, 2700, 1200, 2700, G),
    "g15b_ne_upper": (2200, 2700, 2700, 2400, 200),
    "g20_washing": (1236, 640, 1236, 900, G, -10),
    "g21_courtyard_west": (420, 700, 420, 2200, G),
    "g22_porch": (0, -480, -128, -560, G),
    "g23_hillside": (0, -600, 0, -3000, G, 5),
    "g24_abbot": (-128, 4100, -166, 4440, G),
    "g16_tower_west": (-640, 330, -900, 160, G),
    "g17_tower_east": (420, 330, 640, 160, G),
    "g18_west_transept": (-700, 2700, -1150, 2700, G),
    "g19_east_transept": (500, 2700, 900, 2600, G),
    "u01_library_west": (-650, 2700, -650, 3000, U),
    "u02_scriptorium_east": (400, 2700, 330, 2950, U),
    "u03_gallery_west": (-400, 3300, -400, 4000, U),
    "u04_gallery_east": (200, 3300, 200, 4000, U),
    "l01_organ_loft": (-128, 3600, -128, 4060, L),
    "l02_loft_south": (-128, 3900, -128, 3000, L),
    "t01_bell_tower": (-144, 2420, -144, 2900, T),
    "t02_bells": (-128, 2380, -128, 2700, T, 35),
    # a nave torch (WallTorch30, LT (56, 184, 956), facing west) from its side and from the front: the flame card
    "f01_torch_side": (-10, 1130, 56, 956, G, 38),
    "f02_torch_front": (-230, 956, 56, 956, G, 30),
}
LIGHTING_VIEWS = ["g01_narthex_start", "g03_nave_north", "g05_crossing_east", "g07_choir_north", "g08_altar",
                  "g10_courtyard_ne", "g12_cloister_east", "g14_thjorad", "g16_tower_west", "u01_library_west",
                  "u02_scriptorium_east", "l01_organ_loft", "t01_bell_tower"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
