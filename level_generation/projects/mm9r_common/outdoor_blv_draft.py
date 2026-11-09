#!/usr/bin/env python3
"""
Draft facts for a new MM9 outdoor-as-BLV project (devdocs/mm9_rework/OUTDOOR_BLV_ALL.md): the terrain models' LT extent
and the `offset` that centres it (native = LT * 2.56 - offset, inside +-25 600), the monster classes the runtime tables
resolve, the terrain models and the movable models (doors) with their suggested rules.

    python3 level_generation/projects/mm9r_common/outdoor_blv_draft.py THJORGARD
    python3 level_generation/projects/mm9r_common/outdoor_blv_draft.py THJORGARD --overrides "Thjorgard" \
        --exclude Magreeb,HalfOrcSoldier > level_generation/projects/mm9r_thjorgard_blv/overrides.yml

--overrides writes a first overrides.yml (Sturmford's settings for a big region, swim on, MM9's monsters minus the
--exclude classes (scripted NPCs that resolve to monster rows), the old map's start order, a rule for every model).
Review it before building.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))

import numpy as np  # noqa: E402

from dungeon.content import monster_replacements  # noqa: E402
from dungeon.source import read_dat_world  # noqa: E402
from dungeon.survey import suggestion  # noqa: E402
from transcode_mm9_dat_to_odm import resolve_mm9_monster_replacement  # noqa: E402

SCALE = 2.56


def model_points(model) -> np.ndarray:
    points = []
    for attribute in ("vertices", "points"):
        values = getattr(model, attribute, None)
        if values:
            for v in values:
                points.append([float(c) for c in (v if isinstance(v, (list, tuple)) else (v.x, v.y, v.z))])
            break
    return np.array(points)


PATTERNS = {"InvisibleBrush": "static", "WorldObject": "static", "DestructableBrush": "static",
            "BlueWater": "skip", "PerceptionBrush": "skip", "Rain": "skip", "Snow": "skip"}


def old_starts(stem: str) -> list[str]:
    """The old import's party_start_points order (transitions arrive by index)."""
    import re

    import yaml
    path = ROOT / f"output/mm9_rework/isleofashes_blv_root/worlds/mm9/maps/{stem}.scene.yml"
    match = re.search(r"^party_start_points:\n((?:[ -].*\n)*)", path.read_text(), re.M)
    return [s["source_name"] for s in yaml.safe_load("x:\n" + match.group(1))["x"]] if match else []


def write_overrides(world, name: str, display_name: str, exclude: set, offset, classes: dict) -> None:
    stem = name.lower()
    replacements = monster_replacements()
    monsters = Counter(o.name for o in world.objects if resolve_mm9_monster_replacement(o, replacements) is not None)
    lines = [f"# {display_name} as a BLV open to the sky (devdocs/mm9_rework/OUTDOOR_BLV_ALL.md; template: Sturmford).",
             "# First draft by ../mm9r_common/outdoor_blv_draft.py --overrides; read by the shared converter.",
             "map:", f"  stem: {stem}", f"  display_name: {display_name}",
             f"  starts: [{', '.join(old_starts(stem))}]   # the old map's party_start_points order",
             f"  monster_classes: [{', '.join(c for c, _ in monsters.most_common() if c not in exclude)}]",
             "  swim: true                          # the sea is swum, as on the Isle of Ashes",
             "  painted_minimap: true", "  generate_bsp: false", f"  offset: {offset}", "  voxel: 32",
             "  ambient: 20", "  model_lighting: false", "  split_minor_rooms: true", "  split_retry: true",
             "  thin_walls: true", "  fog: false                          # the outdoor view's haze",
             "skip_lights: []", "model_patterns:"]
    lines += [f"  {pattern}: {rule}" for pattern, rule in PATTERNS.items()]
    lines.append("models:")
    pairs = {}
    for model in world.world_models:
        cls, properties = classes.get(model.name, (None, {}))
        if cls == "AIBarrier" or model.name.startswith(tuple(PATTERNS)) or model.name in ("PhysicsBSP",):
            continue
        if model.name.startswith(("AITrk", "VisBSP", "PerceptionBrush", "Ladder")) \
                and not model.name.startswith("LadderBlocker"):
            continue
        if cls in ("RotatingDoor", "Door"):
            # a DoubleDoorName pair (both classes: Bootcamp's sliding Door0/Door1) shares a group, so a click moves both
            other = str(properties.get("DoubleDoorName") or "")
            group = pairs.get(model.name) or model.name.replace(" ", "_")
            if other:
                pairs[other] = group
            rule = "{group: %s, motion: %s}" % (group, "rotate" if cls == "RotatingDoor" else "dat")
        elif cls in ("TOD_Sky", "DemoSkyWorldModel", "BlueWater", "PortalZone"):   # PortalZone: helper volumes
            rule = "skip"
        else:
            rule = "static"
        key = f"'{model.name}'" if " " in model.name or ":" in model.name else model.name
        lines.append(f"  {key}: {rule}   # {cls}")
    lines += ["textures:", "  'textures\\skybox\\skymarker.dtx': {alias: sky04, width: 512, height: 512}",
              "  'textures\\leveltextures\\misc\\soundonly.dtx': {alias: INVIZVJN7N, width: 32, height: 32}",
              "  'textures\\leveltextures\\misc\\invisible.dtx': {alias: INVIZVJN7N, width: 64, height: 64}",
              "city:", "  daylight: true", "  sky_preset: cloudy", "  half_steps: false", "outdoor: {}"]
    print("\n".join(lines))


def main() -> int:
    name = sys.argv[1].upper()
    if "--overrides" in sys.argv:
        display_name = sys.argv[sys.argv.index("--overrides") + 1]
        exclude = set(sys.argv[sys.argv.index("--exclude") + 1].split(",")) if "--exclude" in sys.argv else set()
        world = read_dat_world(ROOT / f"mm9/extracted/WORLDS/WORLDS/{name}.dat")
        classes = {str({p.name: p.value for p in o.properties}.get("Name", "")):
                   (o.name, {p.name: p.value for p in o.properties}) for o in world.objects}
        points = [model_points(m) for m in world.world_models if m.name.lower().startswith(("terrain", "earthquake"))
                  or classes.get(m.name, (None,))[0] == "Terrain"]
        points = np.concatenate([p for p in points if len(p)])
        centre = (points.min(axis=0) + points.max(axis=0)) / 2
        write_overrides(world, name, display_name, exclude,
                        [int(round(centre[0] * SCALE)), int(round(centre[2] * SCALE)), 0], classes)
        return 0
    world = read_dat_world(ROOT / f"mm9/extracted/WORLDS/WORLDS/{name}.dat")
    classes = {}
    for o in world.objects:
        properties = {p.name: p.value for p in o.properties}
        classes[str(properties.get("Name", ""))] = (o.name, properties)
    terrain = [m for m in world.world_models if m.name.lower().startswith(("terrain", "earthquake"))
               or classes.get(m.name, (None,))[0] == "Terrain"]
    extent = None
    for model in terrain:
        points = model_points(model)
        if len(points):
            low, high = points.min(axis=0), points.max(axis=0)
            extent = (low, high) if extent is None else (np.minimum(extent[0], low), np.maximum(extent[1], high))
    print(f"{name}: terrain models {[m.name for m in terrain]}")
    if extent is not None:
        low, high = extent
        centre = (low + high) / 2
        offset = [int(round(centre[0] * SCALE)), int(round(centre[2] * SCALE)), 0]
        span = (high - low) * SCALE
        print(f"  LT x {low[0]:.0f}..{high[0]:.0f}, z {low[2]:.0f}..{high[2]:.0f}, y {low[1]:.0f}..{high[1]:.0f}; "
              f"native span {span[0]:.0f} x {span[2]:.0f}, height {span[1]:.0f}")
        print(f"  offset: {offset}")
    else:
        print("  no terrain vertices read: check the world model's vertex attribute name")
    replacements = monster_replacements()
    monsters = Counter(o.name for o in world.objects if resolve_mm9_monster_replacement(o, replacements) is not None)
    print(f"  monster classes: {dict(monsters.most_common())}")
    print("  movable models:")
    for model in world.world_models:
        cls, properties = classes.get(model.name, (None, {}))
        if cls in ("RotatingDoor", "Door", "Switch"):
            print(f"    {model.name}: {suggestion(model.name, cls, properties)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
