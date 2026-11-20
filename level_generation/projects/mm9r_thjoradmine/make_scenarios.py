#!/usr/bin/env python3
"""
Write the Thjorad Mine scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json, the compiled scene):

    scenario_doors_exits.yml   the entrance exit raises its transition; the locked entrance door stays shut; the
                               refinery's handle opens its sliding door; a shut lift gate stops a walk, its lever
                               raises it by a real click and the party walks through; the other gate, the plain doors
                               and the slag hatch open on real clicks
    scenario_chests.yml        every chest (mine carts, bins, chests) opens from in front of its model (interact)
    scenario_scripted.yml      the letters and the NPCs' RUDE dialogues by real clicks; the six spikes of BarWall1
                               pulled open it; ten blocks of hard rock (one by a weapon's damage, nine by clicks: scene
                               destructibles) give key 36 and free Ebora; the cave-in gives
                               key 35; the gnolls bust out; the spawn triggers; the slag extractor (hatch, broken part,
                               the replacement installed: key 37)
    scenario_machinery.yml     the abandoned mine: the falling torch and the barrels break ABMineBoards2/3, the mine cart
                               ABMineBoards0 (and the second torch), the steam valve ABMineBoards1, the falling board;
                               the spiked boards ABDoorBoards0; the stalactite

    python3 level_generation/projects/mm9r_thjoradmine/make_scenarios.py
    for s in doors_exits chests scripted machinery; do ./build/game/openyamm \\
        --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_thjoradmine/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import SCALE, Project, Source, classify_models  # noqa: E402
import convert  # noqa: E402

MAP = "thjoradmine.blv"
EXIT_OBJECT = 84                    # ExitTrigger0 (DAT object 84), south of StartPoint0
EYE = 160


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.thjoradmine_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def var(name: str, value: int) -> dict:
    return {"assert": {"named_map_var_changed": {"name": name, "current": value}}}


class World:
    """The static polygons (LT) for line-of-sight tests and the floors."""
    def __init__(self, project: Project):
        self.project = project
        self.source = Source(project)
        plan = classify_models(self.source)
        self.polygons = [p for m in plan["static"] for p in self.source.polygons(m) if p.role == "static"]
        self.lows = np.array([p.points.min(0) for p in self.polygons])
        self.highs = np.array([p.points.max(0) for p in self.polygons])
        self.floors = scenarios.Floors(project)
        # the movers' shut boxes (native): a click pose must leave the party's body clear of a door it opens
        self.mover_boxes = {m["node"][5:]: m["box"] for m in json.loads((project.work / "doors.json").read_text())
                            if m.get("box")}

    def overlaps_mover(self, x, y, z, names, radius=40, height=160) -> bool:
        for name in names:
            (lx, ly, lz), (hx, hy, hz) = self.mover_boxes[name]
            if lx - radius < x < hx + radius and ly - radius < y < hy + radius and lz < z + height and z < hz:
                return True
        return False

    def blocked(self, a_native, b_native) -> bool:
        """Whether a static polygon crosses the segment between two native points (short of the far end)."""
        a = self.project.lt_from_native(a_native)
        b = self.project.lt_from_native(b_native)
        low, high = np.minimum(a, b) - 1, np.maximum(a, b) + 1
        near = np.nonzero((self.highs >= low).all(1) & (self.lows <= high).all(1))[0]
        d = b - a
        for i in near:
            p = self.polygons[i]
            n = p.normal
            denom = float(n @ d)
            if abs(denom) < 1e-9:
                continue
            t = float(n @ (p.points[0] - a)) / denom
            if not 0.02 < t < 0.9:
                continue
            hit = a + t * d
            ring = p.points
            ok = True
            for k in range(len(ring)):
                e = ring[(k + 1) % len(ring)] - ring[k]
                if float(np.cross(e, hit - ring[k]) @ n) < -1e-3:
                    ok = False
                    break
            if ok:
                return True
        return False

    def view(self, target, distances=(110, 150, 200), height=0.0, name="", avoid=(), drop=420, clear_of=()):
        """A pose on a floor with a clear line of sight to a native target point, looking at it, the body clear of
        the movers `clear_of` (a door rising beside a body sunk into it stops on it)."""
        cx, cy, cz = target
        for distance in distances:
            for k in range(16):
                angle = k * math.pi / 8
                x, y = cx + math.cos(angle) * distance, cy + math.sin(angle) * distance
                z = self.floors.z(x, y, cz + 120)
                if z is None or not (cz - drop < z < cz + 40):
                    continue
                if self.blocked((x, y, z + EYE), (cx, cy, cz + height)):
                    continue
                if self.overlaps_mover(x, y, z, clear_of):
                    continue
                beyond = (cx + (cx - x) / distance * 300, cy + (cy - y) / distance * 300)
                if any(scenarios._segment_distance((x, y), beyond, a) < 90 for a in avoid):
                    continue
                look = math.atan2(cy - y, cx - x)
                pitch = math.atan2(cz + height - (z + EYE), distance)
                return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                                     "yaw": round(look, 4), "pitch": round(pitch, 4)}}
        raise SystemExit(f"{name}: no clear view of {target}")

    def model_centre(self, name) -> tuple:
        points = np.array(self.source.models[name].points, float)
        return tuple(self.project.native((points.min(0) + points.max(0)) / 2))


def click(world: World, name: str, avoid=(), drop=420, clear_of=()) -> list:
    """Look at a mover model's centre and press interact."""
    return [world.view(world.model_centre(name), name=name, avoid=avoid, drop=drop, clear_of=clear_of),
            {"advance_runtime": {"seconds": 0.2}},
            {"press_interact": {}}]


def main() -> int:
    project = Project.load(PROJECT, install=False)
    world = World(project)
    floors = world.floors
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = yaml.load((PROJECT / "work/runtime/thjoradmine.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    actors = scene["initial_state"]["actors"]
    scripted = report["scripted"]
    index = scripted["actors"]
    door = {m["node"][5:]: m["door_id"] for m in movers}
    # the scene destructibles (the breakable brushes and the barrels: dungeon/destructibles.py)
    breakable = {d["name"]: d for d in scene.get("destructibles", [])}
    everyone = [(a["position"]["x"], a["position"]["y"]) for a in actors]

    def state(name, value):
        return {"assert": {"mechanism": {"id": door[name], "state": value}}}

    def at(name):
        a = actors[index[name]]["position"]
        return a["x"], a["y"], a["z"]

    # --- doors and the exit ---------------------------------------------------------------------------------------
    doc = header("doors_exits", "Thjorad Mine (native BLV) - the exit, the entrance door, the refinery door, the lift "
                                "gates by their levers, the plain doors")
    steps = doc["steps"]
    start = report["starts"][0]["position"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 84): the way out to Thjorgard, south of StartPoint0."}},
              scenarios.movement(MAP, start, 270, 0.8, (start[0], start[1] - 300, start[2]), 500, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}},
              {"note": {"text": "Door2 (Locked 1, no key in MM9): a click only jiggles it."}},
              *click(world, "Door2"), {"advance_runtime": {"seconds": 2}}, state("Door2", "closed")]
    steps += [{"note": {"text": "The refinery's handle (handletrigger05): the bolts draw and slidingdoor05 slides open."}},
              state("slidingdoor05", "closed"),
              *click(world, "handletrigger05"), {"advance_runtime": {"seconds": 2}},
              var("RefineryBusy", 1), state("slidingdoor05", "open"), state("deadbolttop05", "open"),
              {"note": {"text": "The door shuts after 2.75 s and the handle works again once switch05 closes (10 s): "
                                "the door opens again (a one-shot handle locked the party in, 2026-11-08)."}},
              {"set_pose": {"map": MAP, "x": 201, "y": 1801, "z": 1, "yaw": -1.5708, "pitch": 0}},   # clear of its swing
              {"advance_runtime": {"seconds": 10}}, var("RefineryBusy", 0), state("slidingdoor05", "closed"),
              *click(world, "handletrigger05"), {"advance_runtime": {"seconds": 2}},
              var("RefineryBusy", 1), state("slidingdoor05", "open")]
    # Door0 (Portal0): stopped shut, raised by Switch3 from the west, walked through.
    portals = {p["name"]: p for p in report["portals"]}
    cx, cy, cz = portals["Portal0"]["centre_native"]
    gate_floor = floors.z(cx, cy, cz + 40)
    west = (cx - 260, cy)
    wz = floors.z(west[0], west[1], gate_floor + 60)
    steps += [{"note": {"text": "Door0 (Portal0, MM9 Door MoveDir +y 128 LT): shut, it stops a walk from the west; "
                                "Switch3 raises it on a real click and the party walks through."}},
              state("Door0", "closed"),
              scenarios.movement(MAP, (west[0], west[1], wz + 1), 0, 0.8, (cx - 60, cy, gate_floor + 1), 60, 30),
              *click(world, "Switch3", clear_of=("Door0",)), {"advance_runtime": {"seconds": 4}}, state("Door0", "open"),
              scenarios.movement(MAP, (west[0], west[1], wz + 1), 0, 0.7, (cx + 280, cy, gate_floor + 1), 140, 40),
              {"note": {"text": "Door1 (Portal1): Switch4 raises it."}}, state("Door1", "closed"),
              *click(world, "Switch4"), {"advance_runtime": {"seconds": 4}}, state("Door1", "open")]
    for name in ("RotatingDoor61", "RotatingDoor62", "RotatingDoor63", "RotatingDoor0"):
        steps += [{"note": {"text": f"{name}: a click opens it (the party steps back from its swing)."}},
                  state(name, "closed"), *click(world, name),
                  world.view(world.model_centre(name), distances=(380, 450, 320), name=name + " back"),
                  {"advance_runtime": {"seconds": 3}}, state(name, "open")]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Thjorad Mine (native BLV) - every chest opens from in front of its model")
    doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Thjorad Mine (native BLV) - letters, NPC dialogues, spikes, the hard rock and Ebora, the "
                             "cave-in, the gnolls, the spawns, the slag extractor")
    steps = doc["steps"]
    for name, (event, number) in convert.EV_LETTERS.items():
        entry = props[name]
        steps += [{"note": {"text": f"{name}: the letter (BookLetter.scr DoLetter {number}) on a click."}},
                  world.view((entry["x"], entry["y"], entry["z"]), distances=(90, 120, 150), height=2, name=name,
                             avoid=everyone),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                  {"assert": {"dialog": {"active": True}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    for name, rude in (("CommonerDwarfMaleB2", 11), ("CommonerDwarfMaleB0", 9), ("CommonerDwarfMaleB1", 8),
                       ("DwarvenMiner1", 428)):
        x, y, z = at(name)
        steps += [{"note": {"text": f"{name}: a click opens MM9's dialogue {rude}."}},
                  world.view((x, y, z + 90), distances=(150, 200, 120), name=name,
                             avoid=[a for a in everyone if a != (x, y)]),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                  {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    spikes = [s for s, w in convert.SPIKES.items() if w == "BarWall1"]
    steps += [{"note": {"text": "BarWall1 (SpikeDoorA.scr): locked; each of its six BoardSpikes goes on a click, the "
                                "sixth opens it."}},
              *click(world, "BarWall1"), {"advance_runtime": {"seconds": 2}}, state_of(door, "BarWall1", "closed")]
    for s in spikes:
        steps += [*click(world, s), {"advance_runtime": {"seconds": 0.5}}, var(s, 1)]
    steps += [{"note": {"text": "The barricade falls toward the party: step back while it swings."}},
              world.view(world.model_centre("BarWall1"), distances=(900, 1000, 800, 700), name="BarWall1 back", drop=600),
              {"advance_runtime": {"seconds": 4}}, var("BarWall1Open", 1), state_of(door, "BarWall1", "open")]
    rocks = convert.ROCKS[:convert.ROCKS_NEEDED]
    ebora = index["Ebora"]
    steps += [{"note": {"text": "The hard rock (tm_hardrock.scr '10 36 5000'): ten blocks broken by clicks give key 36; "
                                "Ebora (EboraMines.scr FreeAtLast) taunts and vanishes in a column of fire."}},
              {"assert": {"actor_visible": {"actor_index": ebora, "hidden": False}}}]
    # Each block is aimed at the middle of its east face (the party's side), from 250-400 away, lowest first.
    def face(name):
        points = np.array(world.source.models[name].points, float)
        centre = (points.min(0) + points.max(0)) / 2
        centre[0] = points[:, 0].max()
        return tuple(project.native(centre))
    rocks = sorted(convert.ROCKS, key=lambda r: face(r)[2])[:convert.ROCKS_NEEDED]
    first, rocks = rocks[0], rocks[1:]
    steps += [{"note": {"text": f"{first}: a weapon's blow (1 damage, its 1 hit point) breaks it; the others by clicks."}},
              {"console": {"line": f"destructible {breakable[first]['id']} damage 1", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 0.3}}, var(first, 1)]
    for r in rocks:
        steps += [world.view(face(r), distances=(260, 320, 400), name=r, drop=700),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                  {"advance_runtime": {"seconds": 0.3}}, var(r, 1)]
    steps += [{"assert": {"qbit_set": [90000 + convert.KEY_ROCK]}}, var("EboraFree", 1),
              {"advance_runtime": {"seconds": 14}}, var("EboraFree", 4),   # the cinematic ebora_free: 13 s
              {"assert": {"actor_visible": {"actor_index": ebora, "hidden": True}}}]
    for trigger, key, checks in (("Trigger7", convert.KEY_CAVEIN, [var("CaveIn", 1), var("BrokenCaveIn", 1)]),
                                 ("TriggerHardRock", None, [var("BustOut", 1),
                                                            *[var(f"BrokenBustOutBrush{k}", 1) for k in range(3)]])):
        event, (low, high) = scripted["boxes"][trigger]
        bx, by = (low[0] + high[0]) / 2, (low[1] + high[1]) / 2
        bz = floors.z(bx, by, high[2])
        if trigger == "Trigger7":
            # The box stands on CaveIn itself (a breakable, not in the static floors): the party is put on its top.
            points = np.array(world.source.models["CaveIn"].points, float)
            bz = points[:, 1].max() * SCALE + 4
        steps += [{"note": {"text": f"{trigger}: the party in its box fires event {event}."}},
                  {"load_map": {"map": MAP}},
                  {"set_pose": {"map": MAP, "x": int(bx), "y": int(by), "z": int(bz) + 1, "yaw": 0.0, "pitch": 0.0}},
                  {"advance_runtime": {"seconds": 1.5}}, var(f"Fired{trigger}", 1), *checks]
        if key:
            steps.append({"assert": {"qbit_set": [90000 + key]}})
    gnoll = scripted["gnolls"][0]
    steps.append({"assert": {"actor_visible": {"actor_index": gnoll, "hostile_to_party": True}}})
    event, (low, high) = scripted["boxes"]["TriggerLocation0"]
    bx, by = (low[0] + high[0]) / 2, (low[1] + high[1]) / 2
    bz = floors.z(bx, by, high[2] + 40)
    spawned = scripted["spawned"]["SpawnMarker0"]
    steps += [{"note": {"text": "TriggerLocation0 (SpawnMgr.scr, SpawnLoc.scr): three troglodytes appear at SpawnMarker0 "
                                "and hunt the party."}},
              {"load_map": {"map": MAP}},
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": True}}} for i in spawned],
              {"set_pose": {"map": MAP, "x": int(bx), "y": int(by), "z": int(bz) + 1, "yaw": 0.0, "pitch": 0.0}},
              {"advance_runtime": {"seconds": 1.0}}, var("FiredTriggerLocation0", 1),
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": False, "hostile_to_party": True}}}
                for i in spawned]]
    slag = props["slag"]
    base = props["WorldObject0"]
    steps += [{"note": {"text": "The slag extractor: the hatch (RotatingDoor0) opens on a click; the broken part "
                                "(SlagExtractor.scr OnUse) comes to the hand with key 9512."}},
              {"load_map": {"map": MAP}},
              *click(world, "RotatingDoor0"),
              world.view(world.model_centre("RotatingDoor0"), distances=(380, 450, 320), name="hatch back"),
              {"advance_runtime": {"seconds": 3}}, state_of(door, "RotatingDoor0", "open"),
              {"note": {"text": "Headless picking does not follow the hatch's swing (playbook gotcha): the broken part "
                                "and the base are clicked by their events here; GiveItem hands nothing over headless, "
                                "the key shows the grant (the desktop run checks the hand)."}},
              {"execute_event": {"id": convert.EV_SLAG}}, {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"qbit_set": [90000 + convert.KEY_EXTRACTOR]}},
              {"note": {"text": "With the replacement (item 399) a click on the machine's base installs it (SlagBase.scr, "
                                "SlagExtractor.scr OnShow): key 37 and the item taken."}},
              {"grant_item": {"item_id": 10000 + convert.ITEM_REPLACEMENT, "member_index": 0}},
              {"execute_event": {"id": convert.EV_SLAGBASE}}, {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"qbit_set": [90000 + convert.KEY_FIXED]}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- the abandoned mine's machinery ---------------------------------------------------------------------------
    doc = header("machinery", "Thjorad Mine (native BLV) - the abandoned mine's barricades: torch and barrels, mine cart, "
                              "steam valve, falling board, spiked boards; the stalactite")
    steps = doc["steps"]
    barrel_cogs = [breakable[b]["decoration_cog"] for b in convert.BARREL_CHAIN]
    steps += [{"note": {"text": "FallingWallTorch0 (TM_FallingTorch.scr): hit, it falls; TorchHolder0 breaks; after 3 s "
                                "the barrels DB_Barrel0-8 are destroyed one after another (Exploding destructibles: "
                                "their decorations hidden) and DB_Barrel6/7 break ABMineBoards3/2."}},
              var("BrokenABMineBoards2", 0),
              *click(world, "FallingWallTorch0"), {"advance_runtime": {"seconds": 9}},
              var("Torch0", len(convert.BARREL_CHAIN) + 1),
              {"assert": {"sprite_hidden": barrel_cogs}},
              var("BrokenABMineBoards2", 1), var("BrokenABMineBoards3", 1)]
    cart = props["MineCarA"]
    steps += [{"note": {"text": "MineCarA (TM_MineCarA.scr): hit, it rolls into ABMineBoards0, which breaks and knocks "
                                "FallingWallTorch1 loose; its flame sets off DB_Barrel9."}},
              var("BrokenABMineBoards0", 0),
              scenarios.look_at(floors, MAP, (cart["x"], cart["y"], cart["z"]), cart["yaw_degrees"],
                                distances=(150, 200), height=40, max_drop=150, avoid=everyone),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"advance_runtime": {"seconds": 14}}, var("Cart", 2), var("Torch1", 2),
              var("BrokenABMineBoards0", 1), var("BrokenMCarBlocker1", 1), var("BrokenTorchHolder1", 1),
              {"assert": {"sprite_hidden": [breakable["DB_Barrel9"]["decoration_cog"]]}}]
    steps += [{"note": {"text": "SteamValve0 (TM_SteamWater.scr): the jet breaks ABMineBoards1."}},
              *click(world, "SteamValve0"), {"advance_runtime": {"seconds": 3}}, var("Valve", 2),
              var("BrokenABMineBoards1", 1),
              {"note": {"text": "FallingBoard0: falls once on a click."}},
              *click(world, "FallingBoard0"), {"advance_runtime": {"seconds": 6}}, state_of(door, "FallingBoard0", "open")]
    spikes = [s for s, w in convert.SPIKES.items() if w == "ABDoorBoards0"]
    steps += [{"note": {"text": "ABDoorBoards0 (SpikeDoorOpen.scr): six spikes pulled open it."}}]
    for s in spikes:
        steps += [*click(world, s), {"advance_runtime": {"seconds": 0.5}}, var(s, 1)]
    steps += [world.view(world.model_centre("ABDoorBoards0"), distances=(500, 600, 420), name="ABDoorBoards0 back"),
              {"advance_runtime": {"seconds": 4}}, state_of(door, "ABDoorBoards0", "open"),
              {"note": {"text": "DestructableBrush0: hit, the stalactite falls (DeathTrigger: Stalagtite toggle)."}},
              *click(world, "DestructableBrush0", drop=800), {"advance_runtime": {"seconds": 2}},
              state_of(door, "Stalagtite", "open")]
    scenarios.write(PROJECT / "scenario_machinery.yml", doc, "make_scenarios.py")
    return 0


def state_of(door: dict, name: str, value: str) -> dict:
    return {"assert": {"mechanism": {"id": door[name], "state": value}}}


if __name__ == "__main__":
    sys.exit(main())
