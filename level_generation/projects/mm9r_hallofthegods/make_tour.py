#!/usr/bin/env python3
"""
Write the screenshot tours of the converted Hall of the Gods: eye-level views through the porch, the west hall, the
stair and the throne hall, in MM9 (LithTech) coordinates, converted by the shared tour helper
(../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_hallofthegods/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_hallofthegods/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_hallofthegods/make_tour.py lighting<n> [--original]   # the lighting subset

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
LOW, HIGH = 100, 400                # the porch and the west hall (0-8 LT), the throne hall (264-268 LT)
VIEWS = {
    "p01_start": (-2844, 1153, -1500, 1153, LOW),
    "p02_gate_back": (-2700, 1153, -3200, 1153, LOW),
    "p03_porch_north": (-2750, 900, -2950, 1700, LOW),
    "w01_west_hall_entry": (-2450, 1153, -300, 1153, LOW),
    "w02_pool": (-1800, 1350, -1300, 1150, LOW),
    "w03_west_hall_north": (-2400, 1900, -400, 1900, LOW),
    "w04_west_hall_south": (-2400, 400, -400, 400, LOW),
    "w05_lion_north": (-1600, 1500, -1928, 1760, LOW),
    "w06_benches_south": (-700, 500, -2200, 100, LOW),
    "w07_back_to_gate": (-400, 1153, -2900, 1153, LOW),
    "w08_window_north": (-1300, 1500, -1300, 2400, LOW, 25),
    "s01_stair_foot": (-700, 1153, 600, 1153, LOW),
    "s02_stair_mid": (0, 1153, 600, 1153, 300, 10),
    "t01_throne_hall_entry": (550, 1153, 2600, 1153, HIGH),
    "t02_throne": (1900, 1153, 2600, 1153, HIGH),
    "t03_gods": (1300, 1000, 1800, 1250, HIGH),
    "t04_hall_north": (700, 2200, 2700, 2200, HIGH),
    "t05_hall_south": (700, 0, 2700, 0, HIGH),
    "t06_north_statues": (1650, 1700, 1650, 2400, HIGH, 20),
    "t07_south_statues": (1650, 600, 1650, -300, HIGH, 20),
    "t08_back_from_throne": (2300, 1153, 0, 1153, HIGH),
    "t09_dragon_south": (1800, 700, 2112, 448, HIGH),
    "t10_west_corner": (2700, 2400, 300, -200, HIGH),
    "t11_stair_top_down": (500, 1153, -800, 1153, HIGH, -12),
    "t12_ceiling": (1500, 1153, 2200, 1153, HIGH, 45),
}
LIGHTING_VIEWS = ["p01_start", "w01_west_hall_entry", "w03_west_hall_north", "w04_west_hall_south", "w07_back_to_gate",
                  "s01_stair_foot", "t01_throne_hall_entry", "t02_throne", "t04_hall_north", "t05_hall_south",
                  "t08_back_from_throne", "t10_west_corner"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
