#!/usr/bin/env python3
"""
The Arena's bake: the shared ../mm9r_common/dungeon/lighting.py plus MM9's sun, its two ObjectLights and fills under
the stands' roofs (each below). The stadium is open to the sky and MM9
lit it with `StaticSunLight0` (Rotation pitch 60, yaw 60 degrees, BrightScale 1, white), which only fed MM9's own
lightmap bake: its lightmaps show it (the pens, out of the sun, at the world's AmbientLight 60 / 255 = 0.22; the sunny
stands and Sven's box at 0.62-0.78; the arena floor 0.57). The runtime has no sun, so the sun is a bake-only point light
far away along MM9's sun direction (SUN_DISTANCE native, its window radius RADIUS_FACTOR times that: the bake's quartic
window is then flat over the stadium and the light is parallel, a sun), at SUN_STRENGTH of a map light, white. README
"Baked lighting and brightness". Run through the bake slots:

    level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_thearena/bake.py [--samples N]
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import lighting  # noqa: E402
from dungeon.source import SCALE, Project, Source, lt_vector_to_native  # noqa: E402

SUN_DISTANCE = 20000.0          # native units from the arena's centre
RADIUS_FACTOR = 10.0
SUN_STRENGTH = 0.7
# MM9's two ObjectLights (ObjectLight0 over the arena's middle, 424 LT up, radius 1000, BrightScale 0.8; ObjectLight1
# in the hall at the counter, radius 500, 0.5) as bake-only lights at OBJECT_STRENGTH x BrightScale: the hall's and
# the stands' lightmaps hold more light than their torches and the sun give (README).
OBJECT_STRENGTH = 0.7
# Fills under the stands' gallery roofs and in Sven's box (LT): MM9's lightmaps there are 0.6-0.78 of full, white, where
# the sun cannot reach under the roofs in our bake (README).
FILL_POINTS_LT = [(980 * c, 260, 980 * s) for c, s in ((1, 0), (0.7071, 0.7071), (0, 1), (-0.7071, 0.7071), (-1, 0),
                                                        (-0.7071, -0.7071), (0, -1), (0.7071, -0.7071))] + [(0, 270, 720)]
FILL_RADIUS_LT = 520.0
FILL_STRENGTH = 1.6
_dirlights = lighting.write_dirlights


def sun() -> dict:
    source = Source(Project.load(PROJECT, install=False))
    p = next(o["properties"] for o in source.objects if o["class"] == "StaticSunLight")
    forward = lt_vector_to_native(lighting.lt_forward(p["Rotation"]))      # the way the sunlight travels
    forward = forward / math.sqrt(sum(v * v for v in forward))
    position = [round(-SUN_DISTANCE * v) for v in forward]
    return {"name": "sun:StaticSunLight0", "position": position, "radius": round(SUN_DISTANCE * RADIUS_FACTOR),
            "color": [255, 255, 255], "alpha": lighting.LIGHT_ALPHA * SUN_STRENGTH * float(p.get("BrightScale", 1.0))}


def object_lights() -> list[dict]:
    project = Project.load(PROJECT, install=False)
    out = []
    for o in Source(project).objects:
        if o["class"] != "ObjectLight":
            continue
        p = o["properties"]
        out.append({"name": f"objectlight:{o['name']}", "position": [int(round(v)) for v in project.native(p["Pos"])],
                     "radius": int(round(float(p["LightRadius"]) * SCALE)),
                     "color": [int(round(c)) for c in p["LightColor"]],
                     "alpha": lighting.LIGHT_ALPHA * OBJECT_STRENGTH * float(p.get("BrightScale", 1.0))})
    return out


def fills() -> list[dict]:
    return [{"name": f"stand_fill{k}", "position": [round(x * SCALE), round(z * SCALE), round(y * SCALE)],
             "radius": round(FILL_RADIUS_LT * SCALE), "color": [255, 255, 255],
             "alpha": lighting.LIGHT_ALPHA * FILL_STRENGTH} for k, (x, y, z) in enumerate(FILL_POINTS_LT)]


def write_dirlights(directory: Path) -> list[dict]:
    light = sun()
    print("sun", light["position"], round(light["alpha"], 3))
    return _dirlights(directory) + [light] + object_lights() + fills()


lighting.write_dirlights = write_dirlights

if __name__ == "__main__":
    sys.exit(lighting.main(PROJECT, sys.argv[1:]))
