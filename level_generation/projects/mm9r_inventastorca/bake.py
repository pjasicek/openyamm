#!/usr/bin/env python3
"""
The map's bake: the shared ../mm9r_common/dungeon/lighting.py, with the cave shaft's bake-only lights
(work/cave_lights.json from cave_lights.py) added to its extra lights. Run through the bake slots:

    level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_inventastorca/bake.py [--recompose]

(--recompose reuses the light passes: after a change to the cave lights, bake in full.)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import lighting  # noqa: E402

CAVE_LIGHTS = PROJECT / "work/cave_lights.json"
_dirlights = lighting.write_dirlights


def write_dirlights(directory: Path) -> list[dict]:
    """The DirLights, then the cave's lights (the shared bake appends both to its extra lights)."""
    cave = [{k: v for k, v in light.items() if k != "mm9_lightmap_mean"}
            for light in json.loads(CAVE_LIGHTS.read_text())]
    print("cave lights", len(cave))
    return _dirlights(directory) + cave


lighting.write_dirlights = write_dirlights

if __name__ == "__main__":
    sys.exit(lighting.main(PROJECT, sys.argv[1:]))
