#!/usr/bin/env python3
"""
Write the Sturmford City scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json):

    scenario_doors_exits.yml   the general store's double door stops the party, opens on its click and the party
                               walks in; a facade door stays locked; the docks' exit raises its transition to the
                               Sturmford wilderness, the hatch shaft its transition to Beethoven
    scenario_shops.yml         walk-in shops by real clicks: the armourer (Halfdan Steelhands, RUDE 54) and the magic
                               shop (Injor Gostat, RUDE 50) open their dialogues and "Show us your stuff." opens the
                               shop; the innkeeper (a posed RUDEProp) opens his dialogue by its click event
    scenario_chests.yml        the two treasure bags at the bottom of the well open
    scripted: inside shops: shop hours (key 5017), the location key 1026, Ludwig's reward on the poll after his
                               dialogue, a letter, the jail door and Hatlati's arrest at the prison guard
    scenario_thorolf.yml       NPC378.scr: nobody comes with key 106 alone or 83 with 84; with 83 Thorolf runs up
                               to the party he sees and opens RUDE 378 with no click, the other copy removed

    python3 level_generation/projects/mm9r_sturmfordcity/make_scenarios.py
    for s in doors_exits shops chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_sturmfordcity/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios, town_portal  # noqa: E402
from dungeon.source import Project  # noqa: E402
import citylua  # noqa: E402

MAP = "sturmfordcity.blv"
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
EXIT_DOCK, EXIT_S = 771, 766            # DAT object indices of ExitDock and ExitS (map_transitions.txt rows)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.sturmfordcity_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def key(raw: int) -> int:
    return 90000 + raw


def choose(rude: int, node: int, label: str) -> dict:
    with open(RUDE / f"NPC{rude}.rude", newline="", encoding="latin-1") as stream:
        rows = list(csv.reader(stream))
    index = next(k for k, row in enumerate(rows) if int(row[1]) == node and row[3] == label)
    return {"select_topic": {"action_id": index, "match_label": label}}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    door = {m["node"][5:]: m for m in movers}
    start = report["starts"][0]["position"]
    scripted = report["scripted"]
    actors = {name: tuple(scene["initial_state"]["actors"][index]["position"][k] for k in "xyz")
              for name, index in scripted["actors"].items()}
    everyone = [(p[0], p[1]) for p in actors.values()]
    events = citylua.prop_events(None)

    def talk(name: str, rude: int) -> list:
        x, y, z = actors[name]
        return [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(140, 190), height=60,
                                  avoid=[a for a in everyone if a != (x, y)]),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Sturmford City (native BLV) - a shop's double door, a locked facade door, the exits")
    steps = doc["steps"]
    store = door["GenStoreDoor1"]
    # GenStoreDoor1/2 at LT x 3561, z 1661-1709 (the store's west wall): walk east from the street into the store.
    sx, sy = 3561 * 2.56, 1685 * 2.56
    z = floors.z(sx - 300, sy, 20100)
    steps += [{"note": {"text": f"GenStoreDoor1/2 (doors {store['door_id']}, event {store['event']}): shut, stops the "
                                "party, opens on its click; the party walks into the general store."}},
              {"assert": {"mechanism": {"id": store["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (sx - 300, sy, z + 1), 0, 0.8, (sx - 40, sy, z + 1), 60, 40),
              {"execute_event": {"id": store["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": store["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (sx - 300, sy, z + 1), 0, 0.8, (sx + 300, sy, z + 1), 140, 40)]
    facade = door["Door14"]
    steps += [{"note": {"text": "Door14 (a facade door, Locked, MoveDist 0): a click says it is locked; it stays shut."}},
              {"execute_event": {"id": citylua.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": facade["door_id"], "state": "closed"}}}]
    dock = next(t for t in report["transitions"] if t["name"] == "ExitDock" and t["source"] == MAP)
    dx, dy, dz = (int(v) for v in dock["centre"])
    steps += [{"note": {"text": "ExitDock (DAT object 771): south off the docks to the Sturmford wilderness."}},
              scenarios.movement(MAP, (dx, dy + 400, start[2]), 270, 0.9, (dx, dy - 200, start[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_DOCK}}},
              {"load_map": {"map": MAP}}]
    hatch = door["RotatingDoor7"]
    steps += [{"note": {"text": f"The sewer hatch over ExitS (RotatingDoor7, door {hatch['door_id']}): opened, the party "
                                "drops down the shaft into ExitS's volume (to Beethoven)."}},
              {"execute_event": {"id": citylua.TOGGLE_GROUPS["RotatingDoor7"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": hatch["door_id"], "state": "open"}}},
              {"set_pose": {"map": MAP, "x": 1085, "y": 52, "z": 19700, "yaw": 0.0, "pitch": 0.0}},
              {"advance_runtime": {"seconds": 2}},
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_S}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- shops ------------------------------------------------------------------------------------------------------
    doc = header("shops", "Sturmford City (native BLV) - walk-in shops: the shopkeepers' dialogues open by real "
                          "clicks and their service rows open the shops")
    steps = doc["steps"]
    steps += [{"advance_runtime": {"seconds": 1.5}}]
    for name, rude, label in (("Armorer", 54, "Show us your stuff."), ("Magi", 50, "Show us what you have.")):
        steps += [{"note": {"text": f"{name} (RUDE {rude}) in the shop: a click opens the dialogue; \"Show us your "
                                    "stuff.\" (or its like) opens the shop."}}]
        steps += talk(name, rude)
        steps += [choose(rude, rude, label),
                  {"advance_runtime": {"seconds": 0.5}},
                  {"assert": {"dialog": {"active": True, "house_dialog": True}}},
                  {"press_action": {"action": "cancel_dialog"}}, {"press_action": {"action": "cancel_dialog"}},
                  {"advance_runtime": {"seconds": 0.5}}]
    bartender = scripted["actors"]["Bartender"]
    steps += [{"note": {"text": "The innkeeper Kenneth Wartooth (a posed RUDEProp: an actor looping innkeeper2, RUDE "
                                "57): a click on him (his use hook: his voice line) opens his dialogue."}},
              {"interact_actor": {"actor_index": bartender}}, {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"dialog": {"active": True, "source_id": 57}}},
              {"note": {"text": "His inn (RUDE -7) is an MM6-MM8 tavern: the packs filled to its 12 days (house action "
                                "4), a room rented (action 3) rests until dawn."}},
              choose(57, 57, "We'd like to do business."),
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"dialog": {"active": True, "house_dialog": True, "source_id": 30057}}},
              {"select_topic": {"action_id": 4}},
              {"assert": {"food": 12}},
              {"select_topic": {"action_id": 3}},
              {"advance_runtime": {"seconds": 2.0}},
              {"assert": {"game_hour": 6}}]
    scenarios.write(PROJECT / "scenario_shops.yml", doc, "make_scenarios.py")

    # --- chests -----------------------------------------------------------------------------------------------------
    doc = header("chests", "Sturmford City (native BLV) - the two treasure bags at the bottom of the well open")
    for chest in content["chests"]:
        doc["steps"] += [{"execute_event": {"id": chest["event"]}},
                         {"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                         {"press_action": {"action": "cancel_dialog"}}]
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder7")
    foot = [int(round(ladder["bottom"][0])), int(round(ladder["bottom"][1] - 70)), int(round(ladder["bottom"][2]))]
    top = [int(round(v)) for v in ladder["top_exit"]]
    pose = {"map": MAP, "x": foot[0], "y": foot[1], "z": foot[2] + 1, "yaw_degrees": 90, "pitch": 0}
    doc["steps"] += [
        {"note": {"text": "The bags lie on the well's bottom under the water (MM9: diving): the party climbs out by the "
                          "rope (Ladder7, extended to the bottom)."}},
        {"movement_segment": {"input": "forward", "seconds": 9.0, "actor_collision": False, "actor_ai": False,
                              "start": pose, "expect_stop": dict(pose, x=top[0], y=top[1], z=top[2]),
                              "loose_tolerance": True, "tolerance_xy": 900, "tolerance_z": 60}}]
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted ---------------------------------------------------------------------------------------------------
    doc = header("scripted", "Sturmford City (native BLV) - shop hours, the location key, Ludwig's reward, a letter, "
                             "the jail")
    steps = doc["steps"]
    steps += [
        {"note": {"text": "ForadWorld.scr: the location key 1026 on load; shops close (5017) from 20:00 to 06:00."}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"qbit_set": [key(1026)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(5017)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_clear": [key(5017)]}},
        {"note": {"text": "LudwigVan.scr: with his manuscript found (key 19), his dialogue's close pays 12 000 "
                          "experience (key 116) as it closes (his exit hook)."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(19), "value": True}},
        {"interact_actor": {"actor_index": scripted["actors"]["Ludwig"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 47}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(116)]}},
        {"note": {"text": "BookLetter.scr: Prop1, the Wanted poster in the inn (row 450), shows its text."}},
        {"execute_event": {"id": events["Prop1"]}},
        {"assert": {"dialog": {"active": True}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"note": {"text": "Sturmguard.scr: Hatlati arrested (key 154): the guard's dialogue closes and Hatlati is in "
                          "the cell (key 5009), the jail door locked."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(154), "value": True}},
    ]
    guard = scripted["actors"]["PoorTownGuard10"]
    steps += [{"interact_actor": {"actor_index": guard}}, {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"dialog": {"active": True, "source_id": 425}}}]
    steps += [{"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(5009)]}},
              {"assert": {"mechanism": {"id": door["Jaildoor"]["door_id"], "state": "closed"}}}]
    doc["steps"] += town_portal.scenario_steps(PROJECT / "props.json", events, MAP)   # TownPortal.scr
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    # NPC378.scr: with key 83 Thorolf sees the party, runs over and talks (RUDE 378) with no click; nobody comes
    # with 106 alone or with 84 (dungeon/scenarios.py thorolf_document)
    doc = scenarios.thorolf_document(project, floors, MAP, header("thorolf", "Thorolf runs up and talks (NPC378.scr)"),
                                     scripted["actors"], actors, key)
    scenarios.write(PROJECT / "scenario_thorolf.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
