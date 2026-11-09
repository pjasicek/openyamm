#!/usr/bin/env python3
"""The party's route through the built map: the walkability graph at the party's step (50) with every mover in both
poses, each key object's floor region, and which regions each reaches (walking, drops). tools/route.py [names...]"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "level_generation/projects/hesper_stage"))
sys.path.insert(0, str(HERE.parent / "mm9r_common"))
import check_walkability as walk
from dungeon.source import Project
walk.MONSTER_STEP = 50
walk.MONSTER_DROP = 400 if "--drop" not in sys.argv else float(sys.argv[sys.argv.index("--drop") + 1])
p = Project.load(HERE, install=False)
level = walk.load(p.work / "runtime" / p.map)
g = walk.Graph(level)
objs = json.loads((HERE / "work/dat_objects.json").read_text())
KEYS = ["StartPoint", "Ladder5", "SwitchCreature0", "SwitchCreature5", "TeleportDoor0", "LakeTeleporter", "LakeArrival",
        "Specter3", "ElevatorObj", "SwitchCreature4", "CanyonDoorL0", "MountainTeleporter", "MountainArrival",
        "MountainForestDoor", "TriggerDoor0", "ForestDoor0", "TriggerAttack0", "Painting", "TreasureChest0",
        "TeleportDoor1", "ForestTeleporter", "ForestArrival", "Specter5", "SeaMonsterMale0", "Teleporter0",
        "Teleporter1", "DesertRoomDoor1", "Trigger1", "Mirror0", "Mirror1", "Gemstone", "TreasureChest3",
        "DesertDoor0", "SpikeTrigger1", "Spikes1", "Ladder0", "DesertTeleporter", "DesertArrival", "ExitTrigger2",
        "ExitRiser", "ExitRamp", "ExitRoomTempleDoor0", "WyrdeoftheUnknown0", "ExitPoint"]
names = [a for a in sys.argv[1:] if not a.startswith("--") and not a.replace(".", "").isdigit()] or KEYS
by = {o["name"]: o for o in objs}
regions = {}
for name in names:
    o = by[name]; pos = o["properties"]["Pos"]
    x, y, z = p.native(pos)
    best = None
    for dz in range(0, 1200, 8):
        n = g.node_near(x, y, z - dz, tolerance=12)
        if n is not None:
            best = n; break
    if best is None:
        print(f"{name:22s} no floor node near {[int(v) for v in (x, y, z)]}"); continue
    r = g.region[best]
    regions[name] = r
    print(f"{name:22s} region {r:7d} floor {g.z[best]:7.0f} area {g.area(r)/1e6:7.2f}M  ({int(x)}, {int(y)}, {int(z)})")
print()
seen_regions = sorted(set(regions.values()))
for name, r in regions.items():
    reach = g.reachable(r)
    print(f"{name:22s} reaches: " + ", ".join(n for n, s in regions.items() if s in reach and s != r))
