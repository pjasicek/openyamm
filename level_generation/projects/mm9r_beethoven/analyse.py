#!/usr/bin/env python3
"""
Phase A survey of MM9's Beethoven (the Sturmford sewers), BEETHOVEN.dat: every DAT object by class with the properties
the conversion reads, the textures of every model with their surface flags, and plans of the storeys.

    python3 level_generation/projects/mm9r_beethoven/analyse.py     # work/analysis.json, work/analysis_models.json

The conversion itself is convert.py on the shared converter (../mm9r_common/DUNGEON_PLAYBOOK.md).
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import ROOT, read_dat_world  # noqa: E402

DAT = ROOT / "mm9/extracted/WORLDS/WORLDS/BEETHOVEN.dat"
SKIP_CLASSES = {"AIRail", "AmbientSound"}


def clean(value):
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, bytes):
        return value.decode("latin-1")
    if isinstance(value, (int, str)) or value is None:
        return value
    if hasattr(value, "tolist"):
        return clean(value.tolist())
    return str(value)


def main() -> int:
    world = read_dat_world(DAT)
    by_class = defaultdict(list)
    for index, o in enumerate(world.objects):
        properties = {p.name: clean(p.value) for p in o.properties}
        if o.name in SKIP_CLASSES:
            by_class[o.name].append({"index": index, "name": properties.get("Name"), "Pos": properties.get("Pos")})
        else:
            by_class[o.name].append(dict(properties, index=index))
    (PROJECT / "work/analysis.json").write_text(json.dumps(by_class, indent=0) + "\n")
    models = {}
    for model in world.world_models:
        textures = Counter()
        flags = Counter()
        for poly in model.polies:
            surface = model.surfaces[poly.surface_index]
            textures[model.textures[surface.texture_index].lower()] += 1
            flags[hex(surface.flags)] += 1
        points = np.array(model.points, float) if len(model.points) else np.zeros((1, 3))
        models[model.name] = {"polys": len(model.polies), "low": points.min(0).round(1).tolist(),
                              "high": points.max(0).round(1).tolist(), "textures": dict(textures), "flags": dict(flags)}
    (PROJECT / "work/analysis_models.json").write_text(json.dumps(models, indent=0) + "\n")
    print({k: len(v) for k, v in by_class.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
