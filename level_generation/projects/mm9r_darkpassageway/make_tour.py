#!/usr/bin/env python3
"""
Write the screenshot tour of the converted Dark Passageway: eye-level views through every part of the passage, in MM9
(LithTech) coordinates, converted by the shared tour helper (../mm9r_common/dungeon/tour.py).

    python3 level_generation/projects/mm9r_darkpassageway/make_tour.py <name>               # the new BLV
    python3 level_generation/projects/mm9r_darkpassageway/make_tour.py <name> --original    # same views, old map
    python3 level_generation/projects/mm9r_darkpassageway/make_tour.py lighting<n> [--original]   # lighting subset

The BLV keeps the old bmodel_world map's frame (no offset): the --original tour uses the same positions against
output/mm9_rework/assets_original. Views stand on static floors (the tour's floor query does not see movers or the
water surfaces), so the lake and the ocean are seen from their shores.
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
    "s01_start_room": (-7420, 760, -7420, 200, 300),
    "s02_start_corridor": (-7420, 150, -7420, -600, 300),
    "s03_scroll": (-7300, 120, -7160, 2, 300, -15),
    "b01_lake_from_ladder": (-7420, -440, -7350, -2000, 300, -20),
    "b02_lake_east": (-7420, -440, -6700, -1800, 300, -15),
    "b03_lake_end": (-7548, -4060, -7548, -3700, -400),
    "b04_lake_teleporter": (-7548, -4200, -7548, -3800, -400),
    "c01_canyon_corridor": (-7646, -4305, -8363, -4974, -400),
    "c02_canyon_corridor_south": (-8243, -5948, -8243, -6600, -400),
    "c03_canyon_plateau": (-8243, -6450, -8100, -7600, -400),
    "c04_statue_ledge": (-7600, -6600, -8300, -7600, 100, -10),
    "c05_canyon_door_ledge": (-7900, -8400, -8100, -7000, 0),
    "c06_pit_bottom": (-8000, -7600, -8400, -6900, -2400, 15),
    "c07_mountain_teleporter": (-7200, -8600, -6400, -8300, 0),
    "m01_mountain_room": (-6600, -8300, -6272, -7700, 0),
    "m02_forest_corridor": (-6272, -7700, -6272, -6900, 0),
    "f01_forest_south": (-6016, -6550, -6016, -5800, 0),
    "f02_forest_middle": (-6016, -5900, -6016, -4900, 0),
    "f03_painting": (-5700, -5850, -5632, -5760, 0),
    "f04_hidden_room": (-5500, -5640, -5424, -5800, 0),
    "f05_forest_north": (-6016, -4900, -6016, -4420, 0),
    "p01_forest_arrival": (-6016, -3700, -6016, -3300, 300),
    "p02_path_north": (-5600, -3300, -4700, -3000, 300),
    "p03_path_east": (-4500, -3700, -4400, -4800, 300),
    "p04_path_south": (-4800, -6200, -5150, -7400, 300),
    "t01_tube_room": (-5250, -8300, -4300, -8400, -200, -15),
    "o01_ocean_island": (-2944, -8380, -2944, -9100, -1200),
    "o02_ocean_cage": (-3150, -8500, -2944, -8500, -1200),
    "r01_pillar_room": (-3072, -7250, -3072, -6400, -200),
    "r02_pillar_room_south": (-3000, -6450, -3072, -7400, -200),
    "d01_desert_entry": (-3072, -6050, -2000, -5000, 200),
    "d02_mirror0": (-2300, -5120, -2558, -5120, 200),
    "d03_gemstone": (-1550, -5050, -1280, -5120, 200),
    "d04_cages_west": (-3400, -4096, -3904, -4096, 200),
    "d05_cages_east": (-500, -4096, -64, -4096, 200),
    "d06_desert_wide": (-700, -2900, -3000, -5200, 200),
    "d07_desert_door": (-2176, -2600, -2176, -2064, 200),
    "k01_trap_corridor": (-2050, -1850, -2176, -1450, 200),
    "k02_spike_room": (-2180, -1550, -2180, -1000, 200),
    "k03_desert_teleporter": (-1950, -1300, -1840, -1104, 200),
    "e01_desert_arrival": (-2048, -500, -2048, 100, -100),
    "e02_exit_room": (-2048, 330, -2048, 800, -300),
    "e03_riser": (-1880, 480, -2160, 600, -300),
    "w01_upper_corridor": (-2048, 1100, -1750, 1800, 0),
    "w02_curve": (-1400, 2300, -700, 2470, 0),
    "w03_wyrde_room": (-450, 2470, 192, 2480, 0),
    "w04_flame_cage": (-136, 2300, 148, 2484, 0),
}
LIGHTING_VIEWS = ["s01_start_room", "b01_lake_from_ladder", "b03_lake_end", "c01_canyon_corridor",
                  "c03_canyon_plateau", "c05_canyon_door_ledge", "m01_mountain_room", "f02_forest_middle",
                  "p02_path_north", "t01_tube_room", "o01_ocean_island", "r01_pillar_room", "d01_desert_entry",
                  "d06_desert_wide", "k02_spike_room", "e02_exit_room", "w02_curve", "w03_wyrde_room"]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "v01"
    views = {k: VIEWS[k] for k in LIGHTING_VIEWS} if name.startswith("lighting") else VIEWS
    tour.write(Project.load(PROJECT, install=False), views, name, original="--original" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
