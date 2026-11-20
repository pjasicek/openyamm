#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Dungeon of Secrets: eye-level views through every section of Chadwick's
course, in MM9 (LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_dungeonofsecrets/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_dungeonofsecrets/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_dungeonofsecrets/make_tour.py lighting<n> [--original]   # lighting subset

The BLV keeps the old bmodel_world map's frame (no offset): the --original tour uses the same positions against
output/mm9_rework/assets_original.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import tour  # noqa: E402
from dungeon.source import Project  # noqa: E402

G, U = 100, 420         # floor query heights: ground floor, upper storey
# name: (eye x, eye z, target x, target z, floor query y[, pitch degrees]) in LithTech units.
VIEWS = {
    "h01_arrival": (2100, -416, 1700, -416, G),
    "h02_entrance_stairs": (2800, -416, 2200, -416, U),
    "h03_hub_chadwick": (1850, -600, 1592, -416, G),
    "h04_hub_south": (1800, -300, 1300, -700, G),
    "h05_entrance_gate": (1800, -300, 1674, -140, G),
    "s10_lever_corner": (1650, -200, 1560, -140, G),
    "s10_room": (1520, -150, 1340, -150, G),
    "s09_door": (1350, -380, 1248, -384, G),
    "s09_room": (1150, -350, 700, -200, G),
    "s08_room": (900, -100, 600, -104, G),
    "s08_corridor": (600, -60, 600, 450, G),
    "p01_pool_room": (480, 300, -400, 600, G),
    "p02_pool_corridor": (500, 480, -500, 480, G),
    "p03_pool_room_north": (0, 680, 0, 300, G),
    "s01_corridor_west": (-560, 480, -900, 480, G),
    "s01_plate_room_south": (-930, 820, -930, 1500, G),
    "s01_plate_room_mid": (-860, 900, -930, 1700, G, -12),
    "s01_lever": (-850, 900, -742, 844, G),
    "s01_plate_room_north": (-930, 1650, -930, 1100, G),
    "s02_corridor": (-900, 1880, -200, 1880, G),
    "s02_lever_corner": (-200, 1880, -110, 1876, G),
    "s02_stair_foot": (-290, 960, -290, 1500, G),
    "s02_stairs": (-290, 1000, -290, 1550, G, 15),
    "s02_bus": (-180, 1300, -290, 1500, G, -10),
    "s03_upper_corridor": (-200, 1620, 600, 1620, U),
    "s03_lever_room": (600, 1500, 300, 1100, U),
    "s03_fake_levers": (420, 1200, 304, 1108, U),
    "s03_twin_window": (450, 1350, 684, 1192, U, 8),
    "s03_door": (600, 1000, 600, 824, U),
    "s04_corridor": (600, 700, 600, 520, U),
    "s04_lever": (500, 490, 300, 514, U),
    "s04_double_axe": (400, 490, -100, 490, U),
    "s04_corridor_west": (-450, 490, 0, 490, U),
    "s04_channel": (450, 472, -300, 472, G),
    "s05_octagon": (-560, 400, -688, -192, U),
    "s05_elevator": (-500, -100, -688, -192, U),
    "s05_shaft_foot": (-690, -450, -690, -150, G),
    "s06_gauntlet_west": (-650, -680, 0, -680, G),
    "s06_gauntlet_mid": (-100, -680, 500, -680, G),
    "s06_gauntlet_saws": (400, -680, 900, -680, G),
    "s06_door": (900, -680, 1032, -680, G),
    "e01_exit_gate": (1100, -690, 1444, -690, G),
    "e02_hub_back": (1500, -650, 1900, -416, G),
}
# Decorations up close (the model-lighting comparison: README, Prop lighting).
PROP_VIEWS = {
    "m01_clawtorch_hub": (1616, -200, 1616, -116, 30, 5),
    "m02_clawtorch_hub_s": (1616, -600, 1616, -715, G, 5),
    "m03_sconces_plate_room": (-900, 1100, -1112, 1250, G, 5),
    "m04_clawlamp_gauntlet": (-60, -672, 96, -672, G, 10),
    "m05_clawtorch_pool": (560, 472, 652, 472, G, 5),
    "m06_clawtorch_upper": (500, 1192, 324, 1192, U, 5),
}
LIGHTING_VIEWS = ["h01_arrival", "h03_hub_chadwick", "s10_room", "s09_room", "p01_pool_room", "s01_plate_room_mid",
                  "s02_corridor", "s02_stairs", "s03_lever_room", "s04_double_axe", "s05_octagon", "s06_gauntlet_mid",
                  "e01_exit_gate"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    if name.startswith("props"):
        views = PROP_VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
