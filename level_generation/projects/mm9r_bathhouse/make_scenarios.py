#!/usr/bin/env python3
"""
Write the Bathhouse scenarios from the built map (work/doors.json, work/content.json, props.json):

    scenario_doors_exits.yml   a shut sliding door stops the party, opens on a real click, the party walks through; the
                               exit to Arslegard City; Ladder0 up to the switch's shelf; Door6/7 locked until the drain
    scenario_chests.yml        the four chests open from in front of their models (interact)
    scenario_scripted.yml      the furnace valve (fires, pistons, Ebora's pal boiled), the warning plate, the drain
                               switch and the sinking water, the dives (only without swimming), the spores, Ebora's
                               gossip, her concubines and her escape (keys 349/350), the steam vents, the two letters
    scenario_swim.yml          swimming (the shared rule, dungeon/water.py): into pool B's shaft, under, down to its
                               bed, up to the surface and out; the drained room swum before the drain and dry after it
                               (BlueWater2's top on its mover); a Jellyspore in the shaft stays in the water

    python3 level_generation/projects/mm9r_bathhouse/make_scenarios.py
    for s in doors_exits chests scripted swim; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_bathhouse/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios, water  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "bathhouse.blv"
EXIT_INDEX = 199                  # ExitTrigger0's DAT object index (its map_transitions.txt row)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.bathhouse_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def native(x, y, z) -> tuple:
    """A LithTech point in the native frame (no offset)."""
    return (x * SCALE, z * SCALE, y * SCALE)


def walk(start, yaw, seconds, stop, xy=70, z=24, keys="forward") -> dict:
    step = scenarios.movement(MAP, start, yaw, seconds, stop, xy, z)
    step["movement_segment"]["input"] = keys
    return step


def pose(x, y, z, yaw, pitch=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)), "yaw": round(yaw, 4),
                         "pitch": round(pitch, 4)}}


def var(name, value) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    door = {m["node"][5:]: m for m in movers}
    pads = {p["anchor"]: p for p in content["pads"]}
    actors = {a["anchor"]: a for a in content["actors"]}

    # --- doors, ladder, exit --------------------------------------------------------------------------------------
    doc = header("doors_exits", "Bathhouse (native BLV) - doors, the ladder, the locked drain-room doors, the exit")
    steps = doc["steps"]
    d = door["Door0"]
    x, face_y = 32 * SCALE, -1100 * SCALE
    hall_z = floors.z(x, face_y + 45, 0)
    start_z = floors.z(x, face_y + 350, 0)
    steps += [{"note": {"text": f"Door0 (door {d['door_id']}, event {d['event']}), hall to the south-west pool: shut "
                                "it stops the party; a click on it slides it aside; the party walks through."}},
              {"assert": {"mechanism": {"id": d["door_id"], "state": "closed"}}},
              walk((x, face_y + 350, start_z + 1), 270, 0.8, (x, face_y + 45, hall_z + 1), 80),
              scenarios.look_at(floors, MAP, (x, -1108 * SCALE, 0), 0, distances=(150,), height=0, max_drop=400),
              {"press_interact": {}},
              {"advance_runtime": {"seconds": 3.5}},
              {"assert": {"mechanism": {"id": d["door_id"], "state": "open"}}},
              walk((x, face_y + 150, floors.z(x, face_y + 150, 0) + 1), 270, 0.9,
                   (x, face_y + 150 - 690, floors.z(x, face_y + 150 - 690, 0) + 1), 120, 60)]
    # The exit: from StartPoint0 west into ExitTrigger0 (before the street's invisible brush).
    start = report["starts"][0]["position"]
    steps += [{"note": {"text": "ExitTrigger0 west of the arrival raises the transition to Arslegard City."}},
              walk((start[0], start[1], start[2]), 180, 1.0, (-508 * SCALE + 50, start[1], start[2]), 200, 60),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_INDEX}}},
              {"load_map": {"map": MAP}}]
    # Ladder0: from the switch room's floor up the shelf's west face.
    lx, ly, lz = native(3530, -492, 116)
    tx, ty, tz = native(3624, -416, 116)
    steps += [{"note": {"text": "Ladder0: from the switch room's floor up to the switch's shelf (top exit)."}},
              walk((lx, ly, lz + 1), 0, 1.5, (tx, ty, tz + 1), 160, 60)]
    # Door6/7: locked until Switch0 drains the room (DrainWater.scr, `unlock`); clicked from the drained room's floor.
    d6, d7, sw = door["Door6"], door["Door7"], door["Switch0"]
    door_point = native(5770, -243, -101)
    steps += [{"note": {"text": "Door6/7 (Locked): a click says it is locked and they stay shut."}},
              scenarios.look_at(floors, MAP, door_point, 90, distances=(170,), height=0, max_drop=400),
              {"press_interact": {}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": d6["door_id"], "state": "closed"}}},
              var("Drained", 0),
              {"note": {"text": "Switch0 clicked from its shelf throws it: the room drains and the doors unlock."}},
              scenarios.look_at(floors, MAP, native(3678, -376, 74), 90, distances=(90, 60), height=0, max_drop=200),
              {"press_interact": {}},
              {"advance_runtime": {"seconds": 2}},
              var("Drained", 1),
              {"assert": {"mechanism": {"id": sw["door_id"], "state": "closed"}}},
              scenarios.look_at(floors, MAP, door_point, 90, distances=(170,), height=0, max_drop=400),
              {"press_interact": {}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": d6["door_id"], "state": "open"}}},
              {"assert": {"mechanism": {"id": d7["door_id"], "state": "open"}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Bathhouse (native BLV) - the four MM9 treasure chests open from in front of their models")
    doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Bathhouse (native BLV) - furnace, drain, dives, spores, Ebora, vents, letters")
    steps = doc["steps"]
    fatc = actors["BigColWinPool2"]["actor_index"]
    valve = door["GasRelease0"]
    steps += [{"note": {"text": "The gas valve (BathFurnace.scr): a click swings it open, the big fires light, the "
                                "pistons pump and 2 s later Ebora's pal in pool A is boiled (Fatc.scr Die)."}},
              {"assert": {"actor_visible": {"actor_index": fatc, "hidden": False}}},
              scenarios.look_at(floors, MAP, native(1436, 0, -2049), 180, distances=(120, 160), height=0, max_drop=400),
              {"press_interact": {}},
              {"advance_runtime": {"seconds": 3}},
              var("Furnace", 1),
              var("FatcBoiled", 1),
              {"note": {"text": "The valve turns 180 degrees at MM9's 20 a second."}},
              {"advance_runtime": {"seconds": 7}},
              {"assert": {"mechanism": {"id": valve["door_id"], "state": "open"}}},
              {"assert": {"actor_visible": {"actor_index": fatc, "hidden": True}}},
              {"note": {"text": "The warning plate on the furnace (furnacewarning.scr) answers a click."}},
              scenarios.look_at(floors, MAP, native(1485, -4, -2030), 180, distances=(110, 150), height=0,
                                max_drop=400),
              {"press_interact": {}},
              {"note": {"text": "A second click on the valve closes it and puts the fires out."}},
              scenarios.look_at(floors, MAP, native(1436, 0, -2049), 180, distances=(120, 160), height=0, max_drop=400),
              {"press_interact": {}},
              {"advance_runtime": {"seconds": 1}},
              var("Furnace", 0)]
    # The drain: the water sinks for 30 s.
    flood = [m for m in movers if m["group"] == "FloodWater"]
    steps += [{"note": {"text": "Switch0 (real click from its shelf): BlueWater2's surface sinks to the floor in 30 s."}},
              {"assert": {"mechanism": {"id": flood[0]["door_id"], "state": "closed"}}},
              scenarios.look_at(floors, MAP, native(3678, -376, 74), 90, distances=(90, 60), height=0, max_drop=200),
              {"press_interact": {}},
              {"advance_runtime": {"seconds": 34}},
              {"assert": {"mechanism": {"id": flood[0]["door_id"], "state": "open"}}},
              {"assert": {"mechanism": {"id": flood[1]["door_id"], "state": "open"}}}]
    # The dives (pads on the wading floors; the same-map move is applied by the frame loop, so only its request).
    for name, (low, high, _, _, _) in ({} if water.swimming(project) else convert.DIVES).items():
        pad = pads[name]
        cx, cy, cz = pad["centre"][0], pad["centre"][1], pad["z"] - 3
        # approach from the side the pad's floor continues on: pool pads from the north, chamber pads from the west
        # (the chamber floor), the switch room's from the east (its floor)
        if name.startswith("DivePool"):
            start, yaw = (cx, cy + 300, cz + 1), 270
        elif name in ("DiveSwitchRoom", "DiveChamberB"):      # west of these lies the wall
            start, yaw = (cx + 420, cy, -492 * SCALE + 1), 180
        else:
            start, yaw = (cx - 330, cy, -492 * SCALE + 1), 0
        distance = abs(start[0] - cx) + abs(start[1] - cy)
        arrival = native(*convert.DIVES[name][2])
        steps += [{"note": {"text": f"{name}: stepping onto the dive pad (event {convert.EV_DIVE[name]}) moves the party "
                                    "to the far end of the swim (the walk ends there)."}},
                  walk(start, yaw, round(distance / scenarios.WALK + 0.1, 2), (arrival[0], arrival[1], arrival[2] + 1),
                       260, 60),
                  var("LastDive", convert.EV_DIVE[name])]
    # The steam vents (before the spores and Ebora: after either the party took no vent damage in a headless run, README).
    brush = convert.np.array(convert.dungeon.source.Source(project).models["DamageBrush1"].points, float)
    centre = (brush.min(0) + brush.max(0)) / 2
    vx, vy, vz = native(centre[0], -95, centre[2])
    steps += [{"note": {"text": "SteamVent1: a party standing in its blast takes fire damage while it blows."}},
              pose(vx, vy, vz + 1, 0.0),
              {"advance_runtime": {"seconds": 7}},
              var("VentHit", 1)]          # the fire damage itself can be resisted (MM resistance rolls), so the hit is asserted
    # The spores.
    pad = pads["StepTrigger2"]
    spores = report["scripted"]["spawned"]
    steps += [{"note": {"text": "StepTrigger2 (room A): SpawnLoc1's two Jellyspores appear and attack; the triggers are "
                                "spent (SpawnMgr.scr, SpawnLoc.scr)."}},
              {"assert": {"actor_visible": {"actor_index": spores["SpawnLoc1"][0], "hidden": True}}},
              scenarios.walk_onto(floors, MAP, scenarios.floor_of(pad), "StepTrigger2", distance=520),
              {"advance_runtime": {"seconds": 0.5}},
              var("Spores", 1),
              {"assert": {"actor_visible": {"actor_index": spores["SpawnLoc1"][0], "hidden": False}}},
              {"assert": {"actor_visible": {"actor_index": spores["SpawnLoc1"][1], "hidden": False}}},
              {"assert": {"actor_visible": {"actor_index": spores["SpawnLoc0"][0], "hidden": True}}}]
    # Ebora.
    pad = pads["EboraGossip"]
    ebora = actors["Ebora"]["actor_index"]
    concubines = [actors[n]["actor_index"] for n in ("Concubine1", "Concubine2", "Concubine3")]
    steps += [{"note": {"text": "EboraGossip by Door5: Ebora taunts the party."}},
              scenarios.walk_onto(floors, MAP, scenarios.floor_of(pad), "EboraGossip", distance=330),
              {"advance_runtime": {"seconds": 0.5}},
              var("Gossip", 1),
              {"note": {"text": "Ebora cannot be hurt (EboraBath.scr CanDamage FALSE)."}},
              {"party_attack": {"actor_index": ebora, "count": 5}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"actor_visible": {"actor_index": ebora, "current_hp": convert.ebora_hp()}}},
              {"note": {"text": "On Gostaf's errand (key 348): the three concubines die, Ebora leaves in a column of fire "
                                "and the party gets key 349 (EboraBath.scr DitchTheJoint)."}},
              {"console": {"line": f"qbit set {90000 + convert.KEY_ERRAND}"}}]
    for k, index in enumerate(concubines):
        steps += [{"damage_actor": {"actor_index": index, "amount": 100000}},
                  {"advance_runtime": {"seconds": 0.5}},
                  var("DeadConcubines", k + 1)]
    # The third death starts the cinematic ebora_escape (bath_cinematics.py): its steps run by 3.4 s, it ends at 3.9 s.
    steps += [{"advance_runtime": {"seconds": 4.0}},
              var("EboraGone", 1),
              {"assert": {"qbit_set": [90000 + convert.KEY_CLEANED]}},
              {"assert": {"qbit_clear": [90000 + convert.KEY_CLEANED_UNASKED]}},
              {"assert": {"actor_visible": {"actor_index": ebora, "hidden": True}}}]
    # The letters.
    for name in ("Prop8", "Prop7"):
        e = props[name]
        steps += [{"note": {"text": f"{name} (BookLetter.scr DoLetter {convert.LETTER_ROWS[name]}): a click reads it."}},
                  scenarios.look_at(floors, MAP, (e["x"], e["y"], e["z"]), e["yaw_degrees"], distances=(90, 120),
                                    height=2, max_drop=150),
                  {"press_interact": {}},
                  var(f"Read{name}", 1),
                  {"press_action": {"action": "cancel_dialog"}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    if water.swimming(project):
        swim_scenario(project, floors, content)
    return 0


def swim_scenario(project, floors, content) -> None:
    """The party in pool B's shaft (MM9's swim down to the flooded tunnels), the drained room before and after the
    drain, a Jellyspore in the shaft. Points from the built map: the volumes of its scene, its floors."""
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    volumes = {v["id"]: v for v in scene["water_volumes"]}
    surface = volumes["WaterthatBoilsB"]["pieces"][0]["top"]
    corners = [point for piece in volumes["WaterthatBoilsB"]["pieces"] for point in piece["polygon"]]
    low = [min(c[k] for c in corners) for k in (0, 1)]
    high = [max(c[k] for c in corners) for k in (0, 1)]
    centre = ((low[0] + high[0]) / 2, (low[1] + high[1]) / 2)
    reach = 0.5 * ((high[0] - low[0]) ** 2 + (high[1] - low[1]) ** 2) ** 0.5      # the pool's half diagonal
    shaft = tuple(float(v) for v in native(992, 0, -1457)[:2])                  # the old dive pad over pool B's shaft (convert.DIVES)
    bed = float(floors.z(*shaft, surface))
    rim = (shaft[0] + 460, shaft[1])                   # pool B's east rim, the room's floor
    rim_z = float(floors.z(*rim, surface + 60))
    room = tuple(float(v) for v in native(*convert.FLOOD_PARTS["MECH_FloodWater"][2])[:2])
    room_bed = float(floors.z(*room, volumes["BlueWater2"]["pieces"][0]["top"]))
    spore = next(a for a in content["actors"] if a["anchor"] == "ColSInRoomA0")   # a placed Jellyspore's row
    spawned = len(scene["initial_state"]["actors"])   # spawned actors follow every placed one (density copies too)

    def water_state(**fields):
        return {"assert": {"water": fields}}

    def swim(start, yaw, seconds, keys) -> dict:
        step = walk(start, yaw, seconds, start, 3000, 3000, keys.pop("input", "none"))
        step["movement_segment"].update(keys)
        return step

    doc = header("swim", "Bathhouse (native BLV) - swimming: pool B's shaft, its bed, the surface, out; the drained "
                         "room; a Jellyspore stays in its water")
    steps = doc["steps"]
    steps += [
        {"note": {"text": "On pool B's east rim, dry; then over the shaft (MM9's swim down to the flooded tunnels): "
                          "the party drops in and, its eye under, sinks."}},
        pose(rim[0], rim[1], rim_z + 1, 180),
        {"advance_runtime": {"seconds": 0.5}},
        water_state(state="dry", eye_under=False, breath_min=0.99),
        pose(shaft[0], shaft[1], surface + 40, 180),
        {"advance_runtime": {"seconds": 2.5}},
        water_state(state="submerged", eye_under=True, foot_z_max=round(surface - 100, 1)),
        {"note": {"text": "Down (Fly Down held) the shaft to its bed, where the flooded tunnels start (MM9's swim)."}},
        swim((shaft[0], shaft[1], surface - 200), 0, 4.5, {"fly_down": True}),
        water_state(state="bed", eye_under=True, foot_z_max=round(bed + 8, 1)),
        {"note": {"text": "Up (Fly Up held) to the surface: the eye comes out and the breath refills."}},
        swim((shaft[0], shaft[1], bed + 1), 0, 5.0, {"fly_up": True}),
        water_state(state="surface", eye_under=False, breath_min=0.99),
        {"note": {"text": "Out: from the surface over the shaft's east side a surface jump east clears the basin onto "
                          "the rim, 15 over the water (over the basin's floor, 128 under the surface, the party wades "
                          "and cannot climb its wall: README \"Water\")."}},
        swim((shaft[0] + 60, shaft[1], round(surface - 129, 1)), 0, 2.0, {"input": "forward", "jump": True}),
        water_state(state="dry", eye_under=False, foot_z_min=round(rim_z - 4, 1)),
        {"note": {"text": "The drained room (BlueWater2, its top on the FloodWater movers): flooded over a party on "
                          "its floor before Switch0 drains it, dry after the 30 s drain."}},
        pose(room[0], room[1], room_bed + 1, 0),
        {"advance_runtime": {"seconds": 1}},
        water_state(state="bed", eye_under=True),
        pose(rim[0], rim[1], rim_z + 1, 180),
        {"execute_event": {"id": convert.EV_SWITCH}},
        {"advance_runtime": {"seconds": 34}},
        pose(room[0], room[1], room_bed + 1, 0),
        {"advance_runtime": {"seconds": 1}},
        water_state(state="dry", eye_under=False),
        {"note": {"text": "A Jellyspore (an AISwimFly swimmer) spawned in the shaft and hit by the party on the rim "
                          "runs from a dry party (BaseSwim.inc) and stays in pool B's water: within its footprint, "
                          "over the bed (report_state shows its height under the surface)."}},
        pose(rim[0], rim[1], rim_z + 1, 180),
        {"spawn_actor": {"monster_id": spore["monster_id"], "x": int(round(shaft[0])), "y": int(round(shaft[1])),
                         "z": int(round(bed + 400))}},
        {"advance_runtime": {"seconds": 0.1}},
        {"damage_actor": {"actor_index": spawned, "amount": 1}},
        {"advance_runtime": {"seconds": 8}},
        {"assert": {"actor_visible": {"actor_index": spawned, "report_state": True,
                                      "near": {"x": int(round(centre[0])), "y": int(round(centre[1])),
                                               "max_distance": int(round(reach)), "min_z": int(round(bed - 5))}}}},
    ]
    scenarios.write(PROJECT / "scenario_swim.yml", doc, "make_scenarios.py")


if __name__ == "__main__":
    sys.exit(main())
