#!/usr/bin/env python3
"""
Beethoven's bake: the shared ../mm9r_common/dungeon/lighting.py with MM9's 21 DirLights as the spots MM9 baked them
with (the profile's `dirlights: true`: aim from Rotation, FOV 210, the preprocessor's cone term) instead of the plain
point lights convert.py lists among work/lights.json's capped lights. Run through the bake slots:

    level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_beethoven/bake.py [--recompose]

The capture-matched alternative (work/profile_capture_matched.yml) was baked by lighting.py itself, DirLights as point
lights: copy that profile over tools/lighting/baked_indoors/profiles/mm9_beethoven.yml and run lighting.py (full bake).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import lighting  # noqa: E402

_extra = lighting.write_extra_lights


def write_extra_lights(directory: Path, path: Path) -> int:
    """The capped lights without the DirLights (write_dirlights adds them as spots)."""
    _extra(directory, path)
    lights = [light for light in json.loads(path.read_text()) if not light["name"].startswith("DirLight")]
    path.write_text(json.dumps(lights, indent=1) + "\n")
    print("capped lights without the DirLights", len(lights))
    return len(lights)


lighting.write_extra_lights = write_extra_lights

if __name__ == "__main__":
    sys.exit(lighting.main(PROJECT, sys.argv[1:]))
