#!/usr/bin/env python3
"""
The map's bake: the shared ../mm9r_common/dungeon/lighting.py plus MM9's sun. The arena's DAT lightmaps come from
`DirLight0`, a StaticSunLight (InnerColor 255/255/244, BrightScale 1, Rotation x = pi/2: straight down), which only fed
MM9's own lightmap bake; the shared bake reads only `DirLight` objects. Here it is one bake-only point light SUN_HEIGHT
over the arena's centre with a radius far beyond it: the runtime window (1 - d^2/r^2)^2 is then within 4 % over the
whole bowl and there is no inverse-square falloff (bake_indoor.py), so it lights like a directional sun from above with
the pillars' shadows straight down. The sky box's faces are IndoorSky at run time (scene overrides), which the bake
takes out of casters and emitters, so the light comes in through the open top. Strength: SUN_STRENGTH of a map light
(fitted to MM9's arena floor lightmaps, README "Baked lighting"). Run through the bake slots:

    level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_dragonstadium/bake.py [--samples N] [--recompose]
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import lighting  # noqa: E402
from dungeon.source import SCALE, Project, Source  # noqa: E402

SUN = "DirLight0"
SUN_HEIGHT = 25000                  # native units over the sky box's top (LT y 2 432)
SUN_RADIUS = 250000
SUN_STRENGTH = 1.0
_dirlights = lighting.write_dirlights


def sun_light() -> dict:
    project = Project.load(PROJECT, install=False)
    p = Source(project).properties(SUN)
    x, y, _ = project.native(p["Pos"])
    colour = [int(round(c * float(p.get("BrightScale", 1.0)))) for c in p["InnerColor"]]
    return {"name": f"sun:{SUN}", "position": [int(round(x)), int(round(y)), int(round(2432 * SCALE + SUN_HEIGHT))],
            "radius": SUN_RADIUS, "color": colour, "alpha": lighting.LIGHT_ALPHA * SUN_STRENGTH}


def write_dirlights(directory: Path) -> list[dict]:
    sun = sun_light()
    print("sun", sun)
    return _dirlights(directory) + [sun]


lighting.write_dirlights = write_dirlights

if __name__ == "__main__":
    sys.exit(lighting.main(PROJECT, sys.argv[1:]))
