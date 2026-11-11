#!/usr/bin/env python3
"""
Write the Verhoffin Ruins scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json, work/runtime):

    scenario_doors_exits.yml   the exit to the Isle of Ashes raises its MM9 exit trigger; a shut double door stops the
                               party, opens on a click and is walked through; Door5 stays locked until its key (a click
                               on the key, then on the door); PrisonDoor2 stays bolted until its bolt is clicked; the
                               locked DoubleDoor10 stays shut
    scenario_chests.yml        the six chests open from in front of their models (interact; TreasureChest0 from the
                               crevasse's bed, under the water)
    scenario_scripted.yml      the pentagram (a wrong order, then the right one opens the torture chamber), its door's
                               shooters, the water trap (a nozzle floods the room and locks the door, the drain empties
                               it), the saw, the paddle, the electrified pit, the busts, the fake book, the capstone
                               and the writ
    scenario_swim.yml          swimming (overrides.yml `map: {swim: true}`, the engine's water_volumes): off the
                               crevasse's rim into the water, down to the bed, TreasureChest0 under water, breath and
                               drowning, up to the surface, out by the NW ramp; a save under water loads under water
                               with full breath; the trap room floods over the party (it drowns) and drains

    python3 level_generation/projects/mm9r_verhoffinruins/make_scenarios.py
    for s in doors_exits chests scripted swim; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_verhoffinruins/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios, water  # noqa: E402
from dungeon.source import ROOT, SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "verhoffinruins.blv"
EXIT_OBJECT = 230                   # ExitTrigger0 (DAT object index; map_transitions.txt row of this map)


def convert_source_objects() -> list[dict]:
    """The DAT's objects (index, name), for the slab's destructible id (its DAT index)."""
    from dungeon.source import ROOT, read_dat_world
    world = read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS/VERHOFFINRUINS.dat")
    return [{"index": i, "name": str(next((p.value for p in o.properties if p.name == "Name"), ""))}
            for i, o in enumerate(world.objects)]


def bust_heights(actors: list[int], side: str, z: int) -> str:
    """Lua that fails unless every actor stands above (in its pocket) or below (on the corridor floor) native z."""
    test = "z < " if side == "above" else "z > "
    return (f"for _, a in ipairs({{{', '.join(map(str, actors))}}}) do local _, _, z = evt.GetMapActorPosition(a) "
            f"if {test}{z} then error(\"bust actor \" .. a .. \" is not {side} {z}: \" .. z) end end")


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.verhoffinruins_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    swim = water.swimming(project)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    busts = [next(a["actor_index"] for a in content["actors"] if a["anchor"] == name)
             for name in convert.BUSTS["BustTrigger0"]]
    slab = next(o["index"] for o in convert_source_objects() if o["name"] == convert.SLABS["BustTrigger0"][0])
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    start = report["starts"][0]["position"]
    boxes = report["scripted"]["boxes"]
    paddle_centre = [(a + b) / 2 for a, b in zip(*boxes["PaddleTrigger"])]
    group_doors = {}
    for m in movers:
        group_doors.setdefault(m["group"], []).append(m["door_id"])
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime" / MAP)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    faces = {f["index"]: f for f in blv["faces"]}
    door_faces = {d["door_id"]: d["face_ids"] for d in scene["initial_state"]["doors"]}
    decorations = {d["anchor"]: d for d in content["decorations"]}

    breakable = {d["name"]: d for d in scene.get("destructibles", [])}

    def centre(group):
        """A door group's faces' centre; a scene destructible's (by its DAT name) from its cog faces."""
        if group in breakable:
            points = np.concatenate([vertices[f["vertex_indices"]] for f in blv["faces"]
                                     if f["face_param"].get("cog_number") == breakable[group]["cog"]])
        else:
            points = np.concatenate([vertices[faces[f]["vertex_indices"]] for d in group_doors[group]
                                     for f in door_faces[d]])
        return (points.min(0) + points.max(0)) / 2

    def state(name, value):
        return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}

    def mech(group, value, k=0):
        return {"assert": {"mechanism": {"id": group_doors[group][k], "state": value}}}

    def face_point(target, stand, height=0.0):
        """A pose at `stand` (native x, y; its floor) looking at `target` (native x, y, z)."""
        x, y = stand
        z = floors.z(x, y, target[2] + 120)
        if z is None:
            raise SystemExit(f"no floor at {stand}")
        look = math.atan2(target[1] - y, target[0] - x)
        pitch = math.atan2(target[2] + height - (z + scenarios.EYE), math.dist((x, y), target[:2]))
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}

    def click_door(group, side, distance=130):
        """A real click on a door group's leaves from `side` (native unit vector), at the leaves' mid height."""
        c = centre(group)
        stand = (c[0] + side[0] * distance, c[1] + side[1] * distance)
        return [face_point(c, stand), {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]

    def click_decoration(anchor, distances=(90, 120, 160), height=25, max_drop=120):
        d = decorations[anchor]
        x, y, z = d["position"]
        yaw = props[anchor]["yaw_degrees"] if anchor in props else 0
        return [scenarios.look_at(floors, MAP, (x, y, z), yaw, distances=distances, height=height, max_drop=max_drop),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]

    def pose(x, y, z, yaw=0.0):
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)), "yaw": yaw,
                             "pitch": 0}}

    def in_box(name, dx=0.0, dy=0.0):
        low, high = boxes[name]
        x, y = (low[0] + high[0]) / 2 + dx, (low[1] + high[1]) / 2 + dy
        z = floors.z(x, y, high[2] + 60)
        return pose(x, y, (z if z is not None else low[2]) + 1)

    def outside(name, dx):
        """A pose beside a trigger box (dx native along x), so the next in_box is an entry."""
        return in_box(name, dx=dx)

    def walk(stand, yaw, seconds, stop, xy=90, z_tol=40):
        x, y = stand
        z = floors.z(x, y, -200)
        sx, sy = stop
        return scenarios.movement(MAP, (x, y, z + 1), yaw, seconds, (sx, sy, z + 1), xy, z_tol)

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Verhoffin Ruins (native BLV) - the exit, doors, a key door, a bolted door")
    steps = doc["steps"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 230): the stair up to the Isle of Ashes, east of the start."}},
              scenarios.movement(MAP, start, 0, 0.8, (start[0] + 400, start[1], start[2] + 215), 500, 300),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    # DoubleDoor1 (DoubleDoorPortal1, at LT z -688 between the north hall and the ruin): walked from the north.
    c = centre("DD1")
    north = (c[0], c[1] + 330)
    steps += [{"note": {"text": "DoubleDoorL1/R1 is shut and stops the party walking south into it."}},
              mech("DD1", "closed"),
              walk(north, 270, 1.0, (c[0], c[1] + 60), 90),
              {"note": {"text": "A click on the leaves opens the pair; the party walks through."}},
              *click_door("DD1", (0, 1)),
              {"advance_runtime": {"seconds": 3}},
              mech("DD1", "open"), mech("DD1", "open", 1),
              walk(north, 270, 1.0, (c[0], c[1] - 420), 400)]
    # DoubleDoor10: Locked, nothing opens it.
    c = centre("DD10")
    steps += [{"note": {"text": "DoubleDoorL10/R10 (MM9 Locked, nothing unlocks it) stays shut on a click."}},
              *click_door("DD10", (1, 0)),
              {"advance_runtime": {"seconds": 2}},
              mech("DD10", "closed")]
    # Door5 and its key.
    steps += [{"note": {"text": "Door5 (DoorLock.scr \"559 1\") stays locked without its key."}},
              *click_door("Door5", (1, 0)),
              {"advance_runtime": {"seconds": 2}},
              mech("Door5", "closed"),
              {"note": {"text": "The key on the table (Prop0, givetake.scr 559), a world item, picked up."}},
              *scenarios.pick_up_steps(floors, MAP, scene, "Prop0", distances=(80, 100)),
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_DOOR5_KEY, "count": 1}]}},
              {"note": {"text": "With the key Door5 opens on a click and the key is taken."}},
              *click_door("Door5", (1, 0)),
              {"advance_runtime": {"seconds": 3}},
              mech("Door5", "open"),
              state("Door5Unlocked", 1)]
    # PrisonDoor2 and its bolt.
    # (the bolt lies across the door's middle and its hint box takes the bolt's click: a click there is on the bolt)
    steps += [{"note": {"text": f"PrisonDoor2 is bolted (DestructableBrush12, a scene destructible of "
                                f"{breakable['DestructableBrush12']['hp']} hit points): a hit one short of them turns its "
                                "hint off (DamageTrigger) and leaves it and the door shut; a click on the bolt breaks it (the shared click's killing blow); then the door opens on a click."}},
              {"console": {"line": f"destructible {breakable['DestructableBrush12']['id']} damage "
                                   f"{breakable['DestructableBrush12']['hp'] - 1}", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 0.5}},
              state("BoltHintOff", 1), state("BoltBroken", 0),
              mech("PrisonDoor2", "closed"),
              *click_door("DestructableBrush12", (0, -1), distance=110),
              {"advance_runtime": {"seconds": 1.5}},
              state("BoltBroken", 1),
              *click_door("PrisonDoor2", (0, -1)),
              {"advance_runtime": {"seconds": 3}},
              mech("PrisonDoor2", "open")]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Verhoffin Ruins (native BLV) - the six MM9 treasure chests open")
    # TreasureChest0 lies on the crevasse's bed under the water: the pose stands on the bed (swimming: the party dives
    # there; without it the water is a wading floor and the chest is opened by its event).
    monsters = [(a["position"]["x"], a["position"]["y"]) for a in scene["initial_state"]["actors"]]
    for chest in content["chests"]:
        entry = props[chest["anchor"]]
        near = [a["actor_index"] for a in scene["initial_state"]["actors"]
                if math.dist((a["position"]["x"], a["position"]["y"]), (entry["x"], entry["y"])) < 260]
        for index in near:          # a monster standing at the chest takes the click: it is killed first
            doc["steps"].append({"damage_actor": {"actor_index": index, "amount": 100000}})
        if chest["anchor"] == "TreasureChest0" and not swim:
            doc["steps"].append({"execute_event": {"id": chest["event"]}})
        else:
            # the monsters killed above no longer block the click (pack growth puts copies at the chests)
            alive = [(a["position"]["x"], a["position"]["y"]) for a in scene["initial_state"]["actors"]
                     if a["actor_index"] not in near]
            doc["steps"] += [scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                               distances=(110, 150, 190), avoid=alive),
                             {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]
        doc["steps"] += [{"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                         {"press_action": {"action": "cancel_dialog"}}]
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Verhoffin Ruins (native BLV) - pentagram, water trap, saw, paddle, pit, busts, quest objects")
    steps = doc["steps"]
    steps += [
        {"note": {"text": "The torture chamber's door is locked until the pentagram is solved (PentagramPuzzle.scr)."}},
        *click_door("TortureDoor", (1, 0), distance=150),
        {"advance_runtime": {"seconds": 2}},
        mech("TortureDoor", "closed"), mech("TortureDoor", "closed", 1),
        {"note": {"text": "A point before the centre does nothing; the centre lights the five flames (PentaCenter)."}},
        outside("TriggerPentagram1", 200),
        {"advance_runtime": {"seconds": 0.5}},
        in_box("TriggerPentagram1"),
        {"advance_runtime": {"seconds": 0.5}},
        state("PuzzleProgress", 0),
        outside("PentaCenter", 200),
        {"advance_runtime": {"seconds": 0.5}},
        in_box("PentaCenter"),
        {"advance_runtime": {"seconds": 0.5}},
        state("PuzzleStarted", 1),
        {"note": {"text": "Points 1, 2 then 4 (wrong): the puzzle resets (OnFailure)."}},
    ]
    for k in (1, 2, 4):
        steps += [outside(f"TriggerPentagram{k}", 200), {"advance_runtime": {"seconds": 0.5}},
                  in_box(f"TriggerPentagram{k}"), {"advance_runtime": {"seconds": 0.5}}]
    steps += [state("PuzzleProgress", 0), state("PuzzleFailures", 1),
              {"note": {"text": "1, 2, 3, 4, 5 (red, yellow, blue, green, orange): solved, TortureChamberDoor1 opens."}}]
    for k in range(1, 6):
        steps += [outside(f"TriggerPentagram{k}", 200), {"advance_runtime": {"seconds": 0.5}},
                  in_box(f"TriggerPentagram{k}"), {"advance_runtime": {"seconds": 0.5}}]
    leaf1 = next(m["door_id"] for m in movers if m["node"] == "MECH_TortureChamberDoor1")
    leaf0 = next(m["door_id"] for m in movers if m["node"] == "MECH_TortureChamberDoor0")
    steps += [state("PuzzleSolved", 1),
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": leaf1, "state": "open"}}},
              {"assert": {"mechanism": {"id": leaf0, "state": "closed"}}},
              {"note": {"text": "A click swings the pair: TortureChamberDoor0 opens and turns the shooters on, which fire "
                                "at a party in the chamber."}},
              *click_door("TortureDoor", (1, 0), distance=150),
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": leaf0, "state": "open"}}},
              state("ShootersOn", 1),
              in_box("TortureChamber", dx=800),        # beside the pit, inside the chamber
              {"advance_runtime": {"seconds": 6}},
              state("Shot", 1)]
    # The water trap.
    steps += [{"note": {"text": "A click on a nozzle floods the trap room: the door shuts, the water rises."}},
              *click_decoration_door("WaterNozzle0", centre, face_point),
              {"advance_runtime": {"seconds": 1}},
              state("WaterState", 1),
              mech("DD5", "closed"),
              {"advance_runtime": {"seconds": 18}},
              mech("WaterTrap", "closed"),
              # with swimming the engine drowns the party (breath; scenario_swim.yml), else the map's script
              *([] if swim else [state("Drowned", 1)]),
              {"note": {"text": "The drain button lowers the water and frees the door and the nozzles."}},
              *click_decoration_door("WaterRoomButton2", centre, face_point, sides=((0, 1),)),   # north of the partition
              {"advance_runtime": {"seconds": 1}},
              state("WaterState", 0),
              {"advance_runtime": {"seconds": 18}},
              mech("WaterTrap", "open")]
    # The saw, the paddle, the pit, the busts.
    steps += [{"note": {"text": "SawBladeTrigger1: blade and arm slide out across the corridor and back."}},
              outside("SawBladeTrigger1", 250), {"advance_runtime": {"seconds": 0.5}},
              in_box("SawBladeTrigger1"),
              {"advance_runtime": {"seconds": 1.0}},
              state("SawRuns", 1),
              state("SawHit", 1),                       # the trigger stands in the blade's path
              {"advance_runtime": {"seconds": 0.5}},
              mech("Saw", "open"),
              {"advance_runtime": {"seconds": 6}},
              mech("Saw", "closed"),
              {"note": {"text": "PaddleTrigger: the paddle sweeps over its plate toward the pit and back."}},
              # the Frights of the torture chamber follow the party onto the plate and swing the paddle again
              # (AITriggerable)
              *scenarios.clear_monsters(scene["initial_state"]["actors"], paddle_centre, radius=2500),
              outside("PaddleTrigger", 300), {"advance_runtime": {"seconds": 0.5}},
              in_box("PaddleTrigger"),
              {"advance_runtime": {"seconds": 1.8}},           # 110 degrees at MM9's 80 a second
              state("PaddleRuns", 1),
              mech("Paddle", "open"),
              {"advance_runtime": {"seconds": 8}},
              mech("Paddle", "closed"),
              {"note": {"text": "The electrified pit (ElectricDamager1) hurts a party wading in it."}},
              pose((boxes["PitDamage"][0][0] + boxes["PitDamage"][1][0]) / 2,
                   (boxes["PitDamage"][0][1] + boxes["PitDamage"][1][1]) / 2, -161 * SCALE + 2),   # on the wading water
              {"advance_runtime": {"seconds": 2.5}},
              state("PitHit", 1),
              {"note": {"text": "BustTrigger0 breaks BreakOut1 (KingKong.scr ForceFall); the three monsters waiting on it "
                                "in the pocket above fall into the corridor."}},
              {"lua_event": {"source": bust_heights(busts, "above", int(convert.SCALE * 32))}},
              outside("BustTrigger0", 450), {"advance_runtime": {"seconds": 0.5}},
              in_box("BustTrigger0"),
              {"advance_runtime": {"seconds": 1.0}},
              state("BustedBustTrigger0", 1),
              {"lua_event": {"source": f"if not evt.IsDestructibleDestroyed({slab}) then error(\"BreakOut1 stands\") end"}},
              {"advance_runtime": {"seconds": 3.0}},
              {"lua_event": {"source": bust_heights(busts, "below", int(convert.SCALE * -64))}},
              {"assert": {"actor_visible": {"actor_index": busts[0], "hidden": False, "hostile_to_party": True}}}]
    # The quest objects.
    steps += [{"note": {"text": "The fake book (fakebook.scr): keys 281 and 290, item 242; the book is gone."}},
              *click_decoration("Book", distances=(80, 100, 130), height=5),
              {"assert": {"qbit_set": [90000 + convert.KEY_BOOK, 90000 + convert.KEY_BOOK2]}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_FAKE_BOOK, "count": 1}]}},
              {"note": {"text": "The headsman's block without the capstone quest does nothing; with key 98 and the "
                                "Capstone of Order (item 396) it places the capstone (key 99) and the writ appears; "
                                "the writ gives item 392 and key 100."}},
              *click_decoration("HeadsmanBlock1", distances=(110, 140), height=60),
              {"assert": {"qbit_clear": [90000 + convert.KEY_PLACED]}},
              {"console": {"line": f"qbit set {90000 + convert.KEY_CAPSTONE_QUEST}"}},
              {"console": {"line": f"item give {10000 + convert.ITEM_CAPSTONE}"}},
              *click_decoration("HeadsmanBlock1", distances=(110, 140), height=60),
              {"assert": {"qbit_set": [90000 + convert.KEY_PLACED]}},
              *scenarios.pick_up_steps(floors, MAP, scene, "writ", distances=(80, 100, 130)),
              {"assert": {"qbit_set": [90000 + convert.KEY_WRIT]}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_WRIT, "count": 1}]}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    if swim:
        swim_scenario(floors, props, content, centre, face_point, mech, state)
    return 0


# Swimming (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md; the engine's `water` assert). Native coordinates.
WATER_TOP = -453.1                  # the crevasse's water (BlueWater0/1 top, -177 LT)
SURFACE_FOOT = WATER_TOP + 1 + 25.6 - 160   # the surface pose: the eye point (eye - 25.6) 1 over the water
RIM = (-4347, -560, -328)           # the ruin floor north of TreasureChest0; its edge (an 82-thick slab) ends at y -630
RAMP_FOOT = (-3700, -1600)          # the NW ramp: from the bed (-655) at x -3727 up west to -348 at x -4383, then -328
TRAP_FULL = -76.8                   # WaterTrap full (-30 LT): over the heads of a party on the room's floor (-328)


def swim_scenario(floors, props, content, centre, face_point, mech, state) -> None:
    def segment(start, yaw, pitch, seconds, stop, keys=None, tolerance=2000, tolerance_z=2000):
        pose = {"map": MAP, "x": int(round(start[0])), "y": int(round(start[1])), "z": int(round(start[2])),
                "yaw": round(yaw, 4), "pitch": round(pitch, 4)}
        step = {"input": "forward", "seconds": seconds, "actor_collision": False, "actor_ai": False, "start": pose,
                "expect_stop": dict(pose, x=int(round(stop[0])), y=int(round(stop[1])), z=int(round(stop[2]))),
                "loose_tolerance": True, "tolerance_xy": tolerance, "tolerance_z": tolerance_z}
        step.update(keys or {})
        return {"movement_segment": step}

    def water(**fields):
        return {"assert": {"water": {key: round(float(v), 2) if isinstance(v, float) else v
                                     for key, v in fields.items()}}}

    def pose(x, y, z, yaw=0.0, pitch=0.0):
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)), "yaw": yaw,
                             "pitch": pitch}}

    chest = props["TreasureChest0"]
    bed = round(float(floors.z(chest["x"], chest["y"], WATER_TOP)), 1)
    at_chest = scenarios.look_at(floors, MAP, (chest["x"], chest["y"], chest["z"]), chest["yaw_degrees"],
                                 distances=(110, 150, 190))
    chest_id = next(c["container_id"] for c in content["chests"] if c["anchor"] == "TreasureChest0")
    doc = header("swim", "Verhoffin Ruins (native BLV) - swimming: dive, chest on the bed, breath, drowning, surface, "
                         "ramp, save under water, the trap room floods")
    steps = doc["steps"]
    steps += [
        {"note": {"text": "Off the crevasse's rim: the party walks off the ruin floor, falls into the water and, its "
                          "eye under, sinks (102 a second) to the bed."}},
        pose(*RIM[:2], RIM[2] + 1, yaw=-math.pi / 2),
        {"advance_runtime": {"seconds": 0.5}},
        water(state="dry", eye_under=False, breath_min=0.99),
        segment((RIM[0], RIM[1], RIM[2] + 1), -math.pi / 2, 0.0, 0.3, (RIM[0], RIM[1] - 230, RIM[2])),
        {"advance_runtime": {"seconds": 3}},
        water(state="bed", eye_under=True, foot_z_max=bed + 8),
        {"note": {"text": "TreasureChest0 on the bed: opened from in front of it, under water."}},
        at_chest,
        {"advance_runtime": {"seconds": 0.2}},
        {"press_interact": {}},
        {"assert": {"chest_opened": {"chest_id": chest_id}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"note": {"text": "Breath (MM9): 15 s under water, then every 2 s each member loses 1/6 of maximum HP. Out of "
                          "the water first (breath full), then on the bed for 10, 16 and 20 s."}},
        pose(*RIM[:2], RIM[2] + 1, yaw=-math.pi / 2),
        {"advance_runtime": {"seconds": 0.5}},
        water(eye_under=False, breath_min=0.99),
        at_chest,
        {"advance_runtime": {"seconds": 10}},
        water(eye_under=True, breath_min=0.25, breath_max=0.42, drowning_ticks_max=0),
        {"assert": {"party_health": {"full": True}}},
        {"advance_runtime": {"seconds": 6}},
        water(eye_under=True, breath_max=0.01, drowning_ticks_min=1),
        {"advance_runtime": {"seconds": 4}},
        water(eye_under=True, drowning_ticks_min=3),
        {"assert": {"party_health": {"full": False}}},
        {"note": {"text": "Up (Fly Up held): the party rises at 384 a second and holds at the surface, its eye out; "
                          "breath refills at once."}},
        segment((at_chest["set_pose"]["x"], at_chest["set_pose"]["y"], bed + 1), 0.0, 0.0, 1.5,
                (at_chest["set_pose"]["x"], at_chest["set_pose"]["y"], SURFACE_FOOT), {"input": "none",
                                                                                        "fly_up": True}),
        water(state="surface", eye_under=False, breath_min=0.99, foot_z_min=SURFACE_FOOT - 4,
              foot_z_max=SURFACE_FOOT + 4),
        {"note": {"text": "A save under water loads under water, with full breath (breath is not saved)."}},
        at_chest,
        {"advance_runtime": {"seconds": 5}},
        water(eye_under=True, breath_max=0.7),
        {"save_game": {"name": "verhoffin_swim_under"}},
        {"load_game": {"name": "verhoffin_swim_under"}},
        water(state="bed", eye_under=True, breath_min=0.99),
        {"note": {"text": "Out by the NW ramp: from the surface over its foot the party swims west onto it and walks "
                          "up out of the water onto the ruin floor."}},
        segment((RAMP_FOOT[0], RAMP_FOOT[1], SURFACE_FOOT), math.pi, 0.0, 2.5, (-4500, RAMP_FOOT[1], -328)),
        water(state="dry", eye_under=False, foot_z_min=-360),
    ]
    # The trap room: a nozzle floods it over the party's heads; the drain empties it.
    steps += [{"note": {"text": "The trap room (WaterTrap on its slide mover): a nozzle floods it to -77, over the "
                                "heads of a party on its floor; after 15 s under it drowns."}},
              *click_decoration_door("WaterNozzle0", centre, face_point),
              {"advance_runtime": {"seconds": 1}},
              state("WaterState", 1),
              {"advance_runtime": {"seconds": 29}},
              mech("WaterTrap", "closed"),
              water(eye_under=True, breath_max=0.01),
              {"note": {"text": "The drain button lowers the water: the party's eye comes out, breath is full."}},
              *click_decoration_door("WaterRoomButton2", centre, face_point, sides=((0, 1),)),
              {"advance_runtime": {"seconds": 1}},
              state("WaterState", 0),
              {"advance_runtime": {"seconds": 18}},
              mech("WaterTrap", "open"),
              water(eye_under=False, breath_min=0.99)]
    scenarios.write(PROJECT / "scenario_swim.yml", doc, "make_scenarios.py")


def click_decoration_door(group, centre, face_point, distance=110, sides=((0, -1), (0, 1), (-1, 0), (1, 0))):
    """A real click on a small mover (a nozzle, a button) from the room side: the side whose floor is level."""
    c = centre(group) + np.array([0.0, 0.0, 15.0])        # above the middle: a nozzle is a hollow pipe end
    for side in sides:
        try:
            stand = (c[0] + side[0] * distance, c[1] + side[1] * distance)
            pose = face_point(c, stand)
        except SystemExit:
            continue
        if abs(pose["set_pose"]["z"] - (c[2] - 30)) < 200:
            return [pose, {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]
    raise SystemExit(f"{group}: nowhere to stand")


if __name__ == "__main__":
    sys.exit(main())
