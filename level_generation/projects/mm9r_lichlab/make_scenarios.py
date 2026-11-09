#!/usr/bin/env python3
"""
Write the Lich Lab scenarios from the built map (work/doors.json, work/content.json, props.json):

    scenario_doors_exits.yml   a closed door stops the party, opens on its click event, the party walks through
                               (an upper and a ground door); the exit to Yorwick raises its MM9 exit trigger
    scenario_chests.yml        the eight chests open from in front of their models (interact)
    scenario_scripted.yml      each scripted object class: the elixir chain (pickups, cook pot, burner), a letter,
                               the Transmutation Engine (pod, strike, a Wizard becomes a Lich, key 299), the skeleton
                               transformer, the shooting range, the summoner's ghost pools, the cages, the ickies

    python3 level_generation/projects/mm9r_lichlab/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_lichlab/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import Project  # noqa: E402
import convert  # noqa: E402

MAP = "lichlab.blv"
EXIT_OBJECT = 1201                  # ExitTrigger0 (DAT object index; map_transitions.txt row of this map)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.lichlab_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene_actors = json.loads((PROJECT / "work/runtime/lichlab.scene.yml").read_text())["initial_state"]["actors"]
    door = {m["node"][5:]: m for m in movers}
    group_doors = {}
    for m in movers:
        group_doors.setdefault(m["group"], []).append(m["door_id"])
    pads = {p["anchor"]: p for p in content["pads"]}
    start = report["starts"][0]["position"]
    positions = report["scripted"]["positions"]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Lich Lab (native BLV) - doors swing open on their click and the party walks through; "
                                "the entrance raises its exit trigger to Yorwick")
    steps = doc["steps"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 1201): the entrance to Yorwick, just south of the start."}},
              scenarios.movement(MAP, start, 270, 0.8, (start[0], start[1] - 300, start[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    # RotatingDoor176: the entrance hall's east door (upper storey), and RotatingDoor157 (ground: east corridor to the
    # east lab). Each: the party walks at it from the room side, stops at the leaf, the click opens it, walks through.
    for name, (sx, sy), yaw, stop, through in (("RotatingDoor176", (450, -3932), 0, 692, 1524),
                                               ("RotatingDoor157", (4588, 4424), 180, 3895, 3514)):
        m = door[name]
        z = floors.z(sx, sy, 3000 if name == "RotatingDoor176" else 600)
        steps += [{"note": {"text": f"{name} (door {m['door_id']}, event {m['event']}) is shut."}},
                  {"assert": {"mechanism": {"id": m["door_id"], "state": "closed"}}},
                  scenarios.movement(MAP, (sx, sy, z + 1), yaw, 1.2, (stop, sy, z + 1), 70, 20),
                  {"execute_event": {"id": m["event"]}},
                  {"advance_runtime": {"seconds": 3}},
                  {"assert": {"mechanism": {"id": m["door_id"], "state": "open"}}},
                  scenarios.movement(MAP, (sx, sy, z + 1), yaw, 1.4, (through, sy, z + 1), 140, 40)]
    # The engine hall's stairs up to the cross hall's bridges (the walkability audit cannot follow them: MM9 lays an
    # invisible ramp over their foot): the party climbs from the basement floor (-654) onto the bridge (0).
    steps += [{"note": {"text": "The engine hall's south-east stair: from the basement floor up onto the cross hall's "
                                "bridge (MM9's invisible ramp over its foot, then 8-LT steps)."}},
              scenarios.movement(MAP, (-1075, 4669, -654), 0, 2.5, (805, 4669, 0), 120, 20)]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Lich Lab (native BLV) - the eight MM9 treasure chests open from in front of their models")
    doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Lich Lab (native BLV) - the elixir, a letter, the Transmutation Engine, the skeleton "
                             "transformer, the shooting range, the summoner, the cages and the ickies")
    steps = doc["steps"]
    pickups = report["scripted"]["pickups"]
    herb = next(n for n in pickups if props[n]["prop"] == "bagherbs")
    jar = next(n for n in pickups if props[n]["prop"] == "jar")
    scene = json.loads((PROJECT / "work/runtime/lichlab.scene.yml").read_text())
    ids = {k: 10000 + v for k, v in (("herbs", convert.ITEM_HERBS), ("jar", convert.ITEM_JAR),
                                      ("fluid", convert.ITEM_FLUID), ("elixir", convert.ITEM_ELIXIR))}
    steps += [
        {"note": {"text": f"Storeroom B: a herb bag ({herb}) and a jar ({jar}) are world items (Givetake.scr): "
                          "picked up, they give Elixir Ingredients and a Jar."}},
        *scenarios.pick_up_steps(floors, MAP, scene, herb),
        *scenarios.pick_up_steps(floors, MAP, scene, jar),
        {"assert": {"inventory_any_member": [{"item_id": ids["herbs"], "count": 1}, {"item_id": ids["jar"], "count": 1}]}},
        {"note": {"text": "The kitchen's cook pot (Prop18, ElixirCook.scr) turns the ingredients into Elixir Fluid; the "
                          "burner (Prop17, GiveElixir.scr) turns fluid and jar into the Elixir of Defedation."}},
        {"execute_event": {"id": convert.EV_COOKPOT}},
        {"assert": {"inventory_any_member": [{"item_id": ids["fluid"], "count": 1}]}},
        {"execute_event": {"id": convert.EV_BURNER}},
        {"assert": {"inventory_any_member": [{"item_id": ids["elixir"], "count": 1}]}},
        {"note": {"text": "The letter scroll Prop20 (BookLetter.scr, letter 592) shows MM9's Elixir Instructions."}},
        {"execute_event": {"id": convert.EV_LETTER["Prop20"]}},
        {"press_action": {"action": "cancel_dialog"}},
    ]
    # The engine: a Wizard who carries the elixir stands in pod 1 with the Lich Instructions (key 296).
    box = report["scripted"]["pod_box"]
    centre = [(box[0][0] + box[1][0]) // 2, (box[0][1] + box[1][1]) // 2]
    pod_z = floors.z(centre[0], centre[1], -400)
    pod = group_doors["EnginePod1"][0]
    steps += [
        {"note": {"text": "Without the Lich Instructions the pod closes, the engine strikes and nothing happens."}},
        # the engine room's Oculus comes for the party; under the rising pod it turns it back (ReopenOnContact)
        *scenarios.clear_monsters(scene_actors, (centre[0], centre[1], pod_z), radius=3500, height=2500),
        {"set_pose": {"map": MAP, "x": centre[0], "y": centre[1], "z": int(pod_z) + 1, "yaw": 0, "pitch": 0}},
        {"execute_event": {"id": convert.EV_LICHSWITCH}},
        {"advance_runtime": {"seconds": 4.2}},
        {"assert": {"mechanism": {"id": pod, "state": "open"}}},
        {"assert": {"state_dump_named_map_var": {"name": "EngineStrikes", "value": 1}}},
        {"assert": {"qbit_clear": [90000 + convert.KEY_LICH]}},
        {"advance_runtime": {"seconds": 5}},
        {"assert": {"mechanism": {"id": pod, "state": "closed"}}},
        {"note": {"text": "With key 296 and a Wizard carrying the elixir: the strike makes the Wizard a Lich, gives "
                          "key 299 (quest 'Become a Lich' done) and MM9's 63000 experience."}},
        {"console": {"line": "player add Wizard Risdar", "expect_contains": "Added Risdar as Wizard"}},
        {"grant_item": {"item_id": ids["elixir"], "member_index": 1}},   # the headless party is one member; Risdar is 1
        {"setup_shortcut": {"kind": "set_qbit", "id": 90000 + convert.KEY_INSTRUCTIONS, "value": True}},
        {"set_pose": {"map": MAP, "x": centre[0], "y": centre[1], "z": int(pod_z) + 1, "yaw": 0, "pitch": 0}},
        {"execute_event": {"id": convert.EV_LICHSWITCH}},
        {"advance_runtime": {"seconds": 4.2}},
        {"assert": {"state_dump_named_map_var": {"name": "Transmuted", "value": 1}}},
        {"assert": {"qbit_set": [90000 + convert.KEY_LICH]}},
        {"advance_runtime": {"seconds": 5}},
        {"assert": {"mechanism": {"id": pod, "state": "closed"}}},
    ]
    # The skeleton transformer (upper storey, TransformSwitch0).
    chamber_door = group_doors["SkeletonDoorA"][0]
    steps += [
        {"note": {"text": "TransformSwitch0 (event 202): the switches lock, the chamber's glass door lowers; with the door "
                          "down a Commoner (9050, PeasantTransformee.scr) appears at MarkerSpawn, walks into the chamber "
                          "and cowers; the strike turns him into a Skeleton (9135), the door rises, the switches unlock."}},
        {"assert": {"mechanism": {"id": chamber_door, "state": "open"}}},
        {"execute_event": {"id": convert.EV_TRANSFORM_SWITCH["TransformSwitch0"]}},
        {"advance_runtime": {"seconds": 2}},
        {"assert": {"mechanism": {"id": door["TransformSwitch1"]["door_id"], "state": "open"}}},
        {"advance_runtime": {"seconds": 3.3}},
        {"assert": {"mechanism": {"id": chamber_door, "state": "closed"}}},
        {"assert": {"actor_count": {"monster_id": convert.PEASANT, "min": 1}}},
        {"advance_runtime": {"seconds": 12}},
        {"assert": {"state_dump_named_map_var": {"name": "SkeletonDoorACowered", "value": 1}}},
        {"assert": {"state_dump_named_map_var": {"name": "SkeletonsMade", "value": 1}}},
        {"assert": {"actor_count": {"monster_id": convert.SKELETON, "min": 1}}},
        {"advance_runtime": {"seconds": 5.5}},
        {"assert": {"mechanism": {"id": chamber_door, "state": "open"}}},
        {"assert": {"mechanism": {"id": door["TransformSwitch0"]["door_id"], "state": "closed"}}},
    ]
    # The shooting range.
    target = group_doors["Target19"][0]
    steps += [
        {"note": {"text": "firebook2 (event 206, ILSshootingbook.scr) starts shootfire1: ten bolts break the straw "
                          "target DestructableBrush19, which sinks; the book is done."}},
        {"execute_event": {"id": convert.EV_BOOK["firebook2"]}},
        {"advance_runtime": {"seconds": 17}},
        {"assert": {"state_dump_named_map_var": {"name": "Target19Hits", "value": convert.TARGET_SHOTS}}},
        {"assert": {"mechanism": {"id": target, "state": "open"}}},
        {"assert": {"state_dump_named_map_var": {"name": "firebook2", "value": 2}}},
    ]
    # The summoner: walk onto TriggerLich at the foot of the ramp.
    steps += [
        {"note": {"text": "TriggerLich (event 230): the summoner wakes and a Specter (9140) rises from each ghost pool."}},
        scenarios.walk_onto(floors, MAP, scenarios.floor_of(pads["TriggerLich"]), "TriggerLich", distance=160),
        {"assert": {"state_dump_named_map_var": {"name": "Summoner", "value": 1}}},
        {"assert": {"state_dump_named_map_var": {"name": "GhostsRaised", "value": 4}}},
        {"assert": {"actor_count": {"monster_id": convert.SPECTER, "min": 4}}},
    ]
    # The cages and the ickies.
    cage = group_doors["CageGhast"][0]
    steps += [
        {"note": {"text": "TriggerExplodeL (event 231): the four critters smash their cage fronts (they sink)."}},
        {"assert": {"mechanism": {"id": cage, "state": "closed"}}},
        scenarios.walk_onto(floors, MAP, scenarios.floor_of(pads["TriggerExplodeL"]), "TriggerExplodeL", distance=160),
        {"advance_runtime": {"seconds": 2}},
        {"assert": {"mechanism": {"id": cage, "state": "open"}}},
        {"assert": {"state_dump_named_map_var": {"name": "CagesBroken", "value": 1}}},
        {"note": {"text": "LobbyBatTrigger1 (event 234): the lobby's eight ickies turn hostile."}},
        scenarios.walk_onto(floors, MAP, scenarios.floor_of(pads["LobbyBatTrigger1"]), "LobbyBatTrigger1", distance=650),
        {"assert": {"state_dump_named_map_var": {"name": "BatsLobby", "value": 1}}},
    ]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
