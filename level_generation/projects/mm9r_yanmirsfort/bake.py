#!/usr/bin/env python3
"""
The map's bake: the shared ../mm9r_common/dungeon/lighting.py plus bake-only fill lights in the basement corridor and
the spiral stair under the trap hall (README "Baked lighting"): MM9's lightmaps there average 0.49 of full, cyan, while
its three Lights at BrightScale 0.3 (one of them, Light63, in the rock) leave our bake at 0.23. The lights stand on the
corridor's axis, MM9's cyan (91, 173, 255), at STRENGTH of a map light. Run through the bake slots:

    level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_yanmirsfort/bake.py [--samples N]
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import lighting  # noqa: E402
from dungeon.source import SCALE  # noqa: E402

# (x, y, z) LT on the corridor's axis: the corridor's north end, middle, south end (under its 128 LT ceiling at -256) and
# the spiral stair's well, at its foot and its top.
POINTS_LT = [(128, -300, -4450), (128, -300, -4950), (128, -300, -5450), (128, -300, -5760), (128, -60, -5760)]
RADIUS_LT = 420.0
COLOUR = [91, 173, 255]
STRENGTH = 0.8
_dirlights = lighting.write_dirlights


def corridor_lights() -> list[dict]:
    return [{"name": f"corridor_fill{k}", "position": [round(x * SCALE), round(z * SCALE), round(y * SCALE)],
             "radius": round(RADIUS_LT * SCALE), "color": COLOUR, "alpha": lighting.LIGHT_ALPHA * STRENGTH}
            for k, (x, y, z) in enumerate(POINTS_LT)]


def write_dirlights(directory: Path) -> list[dict]:
    lights = corridor_lights()
    print("corridor lights", len(lights))
    return _dirlights(directory) + lights


lighting.write_dirlights = write_dirlights

if __name__ == "__main__":
    sys.exit(lighting.main(PROJECT, sys.argv[1:]))
