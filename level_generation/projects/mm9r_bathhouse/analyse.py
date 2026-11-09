#!/usr/bin/env python3
"""Bathhouse DAT survey helpers: water volumes, world model boxes (LT)."""
import sys
from pathlib import Path
import numpy as np
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon.source import Project, Source  # noqa

project = Project.load(PROJECT)
source = Source(project)
if sys.argv[1:2] == ["--obj"]:
    skip = {"Visible", "Solid", "RayHit", "BoxPhysics", "SoundRadius", "Mass", "LockJiggleCount", "SoundPos",
            "FogFarZ", "FogNearZ", "FogColor", "XScaleMin", "XScaleMax", "YScaleMin", "YScaleMax", "XScaleDuration",
            "YScaleDuration", "SurfaceColor1", "SurfaceColor2", "NumSurfacePolies", "Volume", "Waveform"}
    for name in sys.argv[2:]:
        o = source.by_name[name.lower()]
        print(o["index"], o["class"], name, {k: v for k, v in o["properties"].items()
                                             if k not in skip and v not in ("", None, 0, 0.0, [0.0, 0.0, 0.0])})
    sys.exit(0)
names = sys.argv[1:] or sorted(source.models)
for name in names:
    m = source.models[name]
    pts = np.array(m.points, float)
    o = source.by_name.get(name.lower())
    extra = ""
    if o:
        p = o["properties"]
        extra = {k: p[k] for k in ("SurfaceHeight", "SpriteSurfaceName", "ShowSurface", "Damage", "Viscosity", "StartOn",
                                   "ScriptName", "ScriptParams") if k in p}
    print(f"{name:20s} {o['class'] if o else '?':16s} lo {pts.min(0).round().astype(int)} hi {pts.max(0).round().astype(int)} "
          f"polys {len(m.polies)} {extra}")
