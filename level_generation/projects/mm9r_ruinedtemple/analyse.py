#!/usr/bin/env python3
"""
Ruined Temple, phase-A survey of the DAT: every object with its properties (AI rails left out) into
work/dat_objects.json and the summary (classes, scripts, world models with extents) into work/analysis.json.

    python3 level_generation/projects/mm9r_ruinedtemple/analyse.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import ROOT  # noqa: E402

sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402

DAT = ROOT / "mm9/extracted/WORLDS/WORLDS/RUINEDTEMPLE.dat"
SKIP_CLASSES = {"AIRail"}


def plain(value):
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, (bytes, bytearray)):
        return value.decode("latin-1")
    if isinstance(value, float):
        return round(value, 3)
    return value


def main() -> int:
    world = read_dat_world(DAT)
    objects = []
    for index, o in enumerate(world.objects):
        properties = {p.name: plain(p.value) for p in o.properties}
        if o.name in SKIP_CLASSES:
            continue
        objects.append({"index": index, "class": o.name, "name": str(properties.get("Name", "")),
                        "properties": properties})
    (PROJECT / "work/dat_objects.json").write_text(json.dumps(objects, indent=0) + "\n")
    models = []
    for model in world.world_models:
        points = np.array(model.points, float) if len(model.points) else np.zeros((1, 3))
        textures = Counter()
        for poly in model.polies:
            textures[model.textures[model.surfaces[poly.surface_index].texture_index].split("\\")[-1]] += 1
        models.append({"name": model.name, "polies": len(model.polies), "low": points.min(0).round(1).tolist(),
                       "high": points.max(0).round(1).tolist(), "textures": dict(textures.most_common(6))})
    scripts = Counter()
    for o in objects:
        script = o["properties"].get("ScriptName")
        if script:
            scripts[str(script)] += 1
    summary = {"classes": dict(Counter(o.name for o in world.objects).most_common()), "scripts": dict(scripts),
               "models": models}
    (PROJECT / "work/analysis.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({"classes": summary["classes"], "scripts": summary["scripts"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
