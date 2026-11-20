#!/usr/bin/env python3
"""
Every rotating mover and ladder of the MM9 DAT worlds, one record per object, for planning conversions
(devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md, "Inventory"):

    python3 level_generation/projects/mm9r_common/rotating_inventory.py          # writes rotating_inventory.json
    python3 level_generation/projects/mm9r_common/rotating_inventory.py ANSKRAMKEEP.dat --related   # prints one map

Units are LithTech (Y up). --related also lists the map's triggers, spike pits and ladder blockers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dungeon.source import ROOT, read_dat_world  # noqa: E402

WORLDS = ROOT / "mm9/extracted/WORLDS/WORLDS"
ROTATING_CLASSES = {"RotatingDoor", "Switch", "RotatingBrush"}
KEYS = ("RotationPoint", "RotationAngles", "Speed", "ClosingSpeed", "CloseWaitTime", "Waveform", "OpenAway", "PushOpen",
        "Sticky", "StartOpen", "TouchToOpen", "Locked", "ReopenOnContact", "AITriggerable", "DoubleDoorName",
        "PortalName", "AttachTo", "XAxisRevTime", "YAxisRevTime", "ZAxisRevTime", "Pos", "Rotation", "Dims",
        "Damage", "DamagePerSecond")


def plain(value):
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def records(path: Path, related: bool) -> list[dict]:
    world = read_dat_world(path)
    models = {model.name.lower(): model for model in world.world_models}
    result = []
    for world_object in world.objects:
        properties = {p.name: p.value for p in world_object.properties}
        name = str(properties.get("Name", ""))
        rotating = world_object.name in ROTATING_CLASSES
        ladder = world_object.name == "Ladder"
        extra = related and (world_object.name in ("Trigger", "PropDamager", "SpikePit") or "spikepit" in name.lower()
                             or "ladderblocker" in name.lower() or "pivot" in name.lower()
                             or "trapexit" in name.lower())
        if not (rotating or ladder or extra):
            continue
        record = {"map": path.stem, "class": world_object.name, "name": name}
        record.update({key: plain(properties[key]) for key in KEYS if key in properties})
        for key, value in properties.items():
            if key.startswith(("OpenTrigger", "CloseTrigger", "TriggerTarget", "Message", "Target")) and value:
                record[key] = plain(value)
        model = models.get(name.lower())
        if model is not None and len(model.points):
            points = np.array(model.points, float)
            record["bbox_min"] = points.min(0).round(2).tolist()
            record["bbox_max"] = points.max(0).round(2).tolist()
        result.append(record)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dat", nargs="?")
    parser.add_argument("--related", action="store_true")
    args = parser.parse_args()
    if args.dat:
        print(json.dumps(records(WORLDS / args.dat, args.related), indent=0))
        return 0
    everything = []
    for path in sorted(WORLDS.glob("*.dat")):
        everything += records(path, False)
    output = Path(__file__).resolve().parent / "rotating_inventory.json"
    output.write_text(json.dumps(everything, indent=0) + "\n")
    print(len(everything), "records:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
