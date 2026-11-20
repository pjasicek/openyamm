"""
Step 1 of a dungeon conversion: survey the DAT world before writing overrides.yml.

    python3 level_generation/projects/mm9r_common/dungeon/survey.py TEMPLEOFHONK.dat [--rules]

Prints the object classes, the world models with their object class and a suggested rule (the first draft of
overrides.yml `models`), the VisBSP UserPortals, the scripts the objects run, the trigger targets and the textures of
the PhysicsBSP with their counts. --rules prints only the YAML draft of the model rules.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dungeon.source import KEPT_PREFIXES, ROOT, SKIPPED_MODELS, read_dat_world  # noqa: E402

# Suggested rules by DAT class: what Anskram Keep and the Temple of Honk made of each (playbook, "Decisions").
SUGGESTED = {"WorldObject": "static", "InvisibleBrush": "static", "DestructableBrush": "static",
             "BlueWater": "skip", "DemoSkyWorldModel": "skip", "TOD_Sky": "skip"}


def suggestion(name: str, cls: str | None, properties: dict) -> str:
    if cls == "RotatingDoor":
        if properties.get("DoubleDoorName") or properties.get("PortalName"):
            return "{group: <pair>, motion: rotate, doorway: true, portal: %s}" % (properties.get("PortalName") or "?")
        return "{group: %s, motion: rotate}" % name
    if cls == "Door":
        return "{group: %s, motion: dat}" % name
    return SUGGESTED.get(cls or "", "static   # " + str(cls))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dat")
    parser.add_argument("--rules", action="store_true")
    args = parser.parse_args()
    path = Path(args.dat)
    if not path.exists():
        path = ROOT / "mm9/extracted/WORLDS/WORLDS" / args.dat
    world = read_dat_world(path)
    objects = []
    for index, o in enumerate(world.objects):
        properties = {p.name: p.value for p in o.properties}
        objects.append((index, o.name, str(properties.get("Name", "")), properties))
    by_name = {name.lower(): (cls, properties) for _, cls, name, properties in objects}
    rules = []
    for model in world.world_models:
        name = model.name
        if name == "PhysicsBSP" or (name.startswith(SKIPPED_MODELS) and not name.startswith(KEPT_PREFIXES)):
            continue
        cls, properties = by_name.get(name.lower(), (None, {}))
        rules.append(f"  {name}: {suggestion(name, cls, properties)}   # {cls}, {len(model.polies)} polys")
    if args.rules:
        print("models:\n" + "\n".join(rules))
        return 0
    print(f"{path.name}: {len(world.objects)} objects, {len(world.world_models)} world models")
    print("classes:", dict(Counter(cls for _, cls, _, _ in objects).most_common()))
    print("\nworld models (suggested rules):\n" + "\n".join(rules))
    vis = next((m for m in world.world_models if m.name == "VisBSP"), None)
    if vis is not None:
        print("\nUserPortals:")
        for portal in vis.user_portals:
            print(f"  {portal.name}: centre {[round(v) for v in portal.center]} dims {[round(v) for v in portal.dims]}")
    scripts = Counter()
    for _, cls, name, properties in objects:
        if properties.get("ScriptName"):
            scripts[(str(properties["ScriptName"]).lower(), cls)] += 1
    print("\nscripts:", *[f"  {count} x {script} ({cls})" for (script, cls), count in sorted(scripts.items())], sep="\n")
    print("\ntriggers and their targets:")
    for _, cls, name, properties in objects:
        if cls in ("Trigger", "ExitTrigger") or properties.get("OpenTriggerTarget0"):
            targets = [(properties.get(f"TargetName{k}"), properties.get(f"MessageName{k}")) for k in range(1, 11)]
            targets = [t for t in targets if t[0]]
            opens = [(properties.get(f"OpenTriggerTarget{k}"), properties.get(f"OpenTrigger{k}")) for k in range(4)]
            closes = [(properties.get(f"CloseTriggerTarget{k}"), properties.get(f"CloseTrigger{k}")) for k in range(4)]
            print(f"  {cls} {name}: targets {targets} open {[o for o in opens if o[0]]} close {[c for c in closes if c[0]]}"
                  f" dest {properties.get('DestinationWorld', '')}")
    physics = next(m for m in world.world_models if m.name == "PhysicsBSP")
    textures = Counter(physics.textures[physics.surfaces[poly.surface_index].texture_index].lower()
                       for poly in physics.polies)
    print("\nPhysicsBSP textures:", *[f"  {count} {texture}" for texture, count in textures.most_common()], sep="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
