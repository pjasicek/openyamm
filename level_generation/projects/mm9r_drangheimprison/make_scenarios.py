#!/usr/bin/env python3
"""
Write the Drangheim Prison scenarios from the built map (work/doors.json, work/content.json, props.json):

    scenario_doors_exits.yml   a closed door stops the party, opens on its click and the party walks through; a cell
                               stays locked and its lever opens it; the hatch stops a climb up Ladder0 and opened
                               lets it through; the front door raises its MM9 exit trigger
    scenario_chests.yml        the six chests open from in front of their models (interact)
    scenario_scripted.yml      the prison's scripted objects by their events: pass and alarm, interrogation, smith
    scenario_quests.yml        the NPCs by interact: an indoor click opens their RUDE dialogue, its rows set the keys,
                               and closing it runs the OnRudeExit event (the pass, the cook's deal, Antoni, Ivsar)

    python3 level_generation/projects/mm9r_drangheimprison/make_scenarios.py
    for s in doors_exits chests scripted quests; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_drangheimprison/scenario_$s.yml --scenario-no-color; done
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

MAP = "drangheimprison.blv"
EXIT_OBJECT = 411                   # ExitTrigger1 (DAT object index; map_transitions.txt row of this map)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.drangheimprison_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def key(raw: int) -> int:
    return 90000 + raw


RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"


def choose(rude: int, node: int, label: str) -> dict:
    """The dialogue row `label` of a RUDE node (its action id is the row's place in the file)."""
    import csv
    with open(RUDE / f"NPC{rude}.rude", newline="", encoding="latin-1") as stream:
        rows = list(csv.reader(stream))
    index = next(k for k, row in enumerate(rows) if int(row[1]) == node and row[3] == label)
    return {"select_topic": {"action_id": index, "match_label": label}}


def talk(floors, actors, name, rude, avoid=()) -> list:
    """Open an NPC's RUDE dialogue with a real click from in front of it."""
    x, y, z = actors[name]
    click = [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(150, 200), height=60, avoid=avoid),
             {"advance_runtime": {"seconds": 0.2}},        # a frame at the new pose: picking follows rendered state
             {"press_interact": {}}]
    return click + [{"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                    {"assert": {"dialog": {"active": True, "source_id": rude}}}]


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())} \
        if (PROJECT / "props.json").exists() else {}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    door = {m["node"][5:]: m for m in movers}
    start = report["starts"][0]["position"]
    scripted = report["scripted"]
    actors = {name: tuple(scene["initial_state"]["actors"][index]["position"][k] for k in "xyz")
              for name, index in scripted["actors"].items()}
    pads = {p["anchor"]: p for p in content["pads"]}
    everyone = [(p[0], p[1]) for p in actors.values()]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Drangheim Prison (native BLV) - doors, a lever and its cell, a ladder and hatch, the front door")
    steps = doc["steps"]
    steps += [{"note": {"text": "ExitTrigger1 (DAT object 411): the front door to Drangheim, just south of the start."}},
              scenarios.movement(MAP, start, 270, 0.8, (start[0], start[1] - 300, start[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    # The entrance door: rising double door at z -2352 (native y -6021), walked from the hall.
    entry = door["RightDoor1a"]
    z = floors.z(-2171, -6300, -2100)
    steps += [{"note": {"text": f"RightDoor1a (door {entry['door_id']}) is shut, stops the party, opens on event "
                                f"{entry['event']}; the party walks through."}},
              {"assert": {"mechanism": {"id": entry["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (-2171, -6300, z + 1), 90, 0.9, (-2171, -6030, z + 1), 90, 20),
              {"execute_event": {"id": entry["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": entry["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (-2171, -6300, z + 1), 90, 1.0, (-2171, -5543, z + 1), 140, 40)]
    # A locked cell and its lever: lever5 opens Celldoor6, Ivsar's cell.
    cell = door["Celldoor6"]
    steps += [{"note": {"text": "Celldoor6 stays shut on a click (event 230: locked); lever5 opens it, back shuts it."}},
              {"execute_event": {"id": convert.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": cell["door_id"], "state": "closed"}}},
              {"execute_event": {"id": convert.EV_LEVER["lever5"]}},
              {"advance_runtime": {"seconds": 5}},
              {"assert": {"mechanism": {"id": cell["door_id"], "state": "open"}}},
              {"assert": {"mechanism": {"id": door["lever5"]["door_id"], "state": "open"}}},
              {"execute_event": {"id": convert.EV_LEVER["lever5"]}},
              {"advance_runtime": {"seconds": 5}},
              {"assert": {"mechanism": {"id": cell["door_id"], "state": "closed"}}}]
    # Celldoor18 (StartOpen, authored standing open: built swung shut, starting open): lever17 shuts it, back opens it.
    cell = door["Celldoor18"]
    steps += [{"note": {"text": "Celldoor18 starts open (MM9 StartOpen); lever17 swings it shut, back opens it again."}},
              {"assert": {"mechanism": {"id": cell["door_id"], "state": "open"}}},
              {"execute_event": {"id": convert.EV_LEVER["lever17"]}},
              {"advance_runtime": {"seconds": 6}},
              {"assert": {"mechanism": {"id": cell["door_id"], "state": "closed"}}},
              {"execute_event": {"id": convert.EV_LEVER["lever17"]}},
              {"advance_runtime": {"seconds": 6}},
              {"assert": {"mechanism": {"id": cell["door_id"], "state": "open"}}}]
    # Ladder0: the hatch stops a climb while shut; opened, the party climbs out of the cave into the storeroom.
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder0")
    hatch = door["RotatingDoor3"]
    foot = [int(round(ladder["bottom"][0] - 60)), int(round(ladder["bottom"][1])), int(round(ladder["bottom"][2]))]
    top = [int(round(v)) for v in ladder["top_exit"]]

    def climb(seconds, stop, tolerance_xy, tolerance_z):
        pose = {"map": MAP, "x": foot[0], "y": foot[1], "z": foot[2] + 1, "yaw_degrees": 0, "pitch": 0}
        return {"movement_segment": {"input": "forward", "seconds": seconds, "actor_collision": False, "actor_ai": False,
                                     "start": pose, "expect_stop": dict(pose, x=stop[0], y=stop[1], z=stop[2]),
                                     "loose_tolerance": True, "tolerance_xy": tolerance_xy, "tolerance_z": tolerance_z}}
    steps += [{"note": {"text": "Ladder0: the shut hatch stops the climb under it."}},
              climb(5.0, (foot[0] + 60, foot[1], int(ladder["top"][2]) - 200), 90, 90),
              {"note": {"text": f"Hatch (door {hatch['door_id']}) opens on its click; the party climbs out on top."}},
              {"execute_event": {"id": hatch["event"]}},
              {"advance_runtime": {"seconds": 5}},
              {"assert": {"mechanism": {"id": hatch["door_id"], "state": "open"}}},
              climb(3.5, top, 200, 40)]      # the climb plus the glide onto the top exit (since 2026-11-10)
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    if props:
        doc = header("chests", "Drangheim Prison (native BLV) - the six MM9 treasure chests open from in front of them")
        direct = {"TreasureChest2", "TreasureChest3"}          # behind the secret door
        doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props, direct)
        scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Drangheim Prison (native BLV) - the alarm, the grate and smith, the interrogation")
    steps = doc["steps"]
    guard = scripted["actors"]["GuardCaptain0"]
    interr = door["RightDoor0"]
    steps += [
        {"note": {"text": "The PerceptionBrushes' glow shows at Perception 12 and not below (checked every 3 s)."}},
        {"console": {"line": "skill set Perception 1 B"}},
        {"advance_runtime": {"seconds": 3.5}},
        {"assert": {"state_dump_named_map_var": {"name": "PerceptionHints", "value": 1}}},
        {"console": {"line": "skill set Perception 12 G"}},
        {"advance_runtime": {"seconds": 3.5}},
        {"assert": {"state_dump_named_map_var": {"name": "PerceptionHints", "value": 2}}},
        {"note": {"text": "No pass: the inner guards are hostile; the gate guards are not (DrangheimHostility.inc)."}},
        {"assert": {"actor_visible": {"actor_index": guard, "hostile_to_party": True}}},
        {"assert": {"actor_visible": {"actor_index": scripted["actors"]["Guard0"], "hostile_to_party": False}}},
        {"note": {"text": "The smithy's grate (Door1): a click opens it and the smith stops (Open/CloseTrigger)."}},
        {"execute_event": {"id": convert.EV_GRATE}},
        {"advance_runtime": {"seconds": 3}},
        {"assert": {"mechanism": {"id": door["Door1"]["door_id"], "state": "open"}}},
        {"assert": {"state_dump_named_map_var": {"name": "SmithOff", "value": 1}}},
        {"note": {"text": "TriggerBeatings1 (event 251): the interrogator walks to the first cell and the warden opens "
                          "it; the prisoner follows him to the interrogation room, which the doorman shuts behind them, "
                          "and the beating sounds (BeatStep 18 while it plays)."}},
        {"execute_event": {"id": convert.EV_BEATINGS["TriggerBeatings1"]}},
        {"advance_runtime": {"seconds": 12}},
        {"assert": {"state_dump_named_map_var": {"name": "Beatings", "value": 1}}},
        {"assert": {"mechanism": {"id": door["Celldoor14"]["door_id"], "state": "open"}}},
        {"advance_runtime": {"seconds": 52}},
        {"assert": {"state_dump_named_map_var": {"name": "BeatStep", "value": 18}}},
        {"assert": {"mechanism": {"id": interr["door_id"], "state": "closed"}}},
        {"assert": {"actor_visible": {"actor_index": scripted["actors"]["InterrPrisoner0"],
                                      "near": {"x": scripted["points"]["Beaten"][0], "y": scripted["points"]["Beaten"][1],
                                               "max_distance": 200}}}},
    ]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- the quests by interact ------------------------------------------------------------------------------------
    doc = header("quests", "Drangheim Prison (native BLV) - indoor clicks open the NPCs' RUDE dialogues and their "
                           "OnRudeExit events run")
    steps = doc["steps"]
    steps += [{"note": {"text": "Guard2 (dialogue 426): the visitor's questions; closing runs GuardRude.scr's OnRude, "
                                "which hands over the Visitor's Pass item, and the inner guards stand down."}}]
    steps += talk(floors, actors, "Guard2", 426, [a for a in everyone if a != actors["Guard2"][:2]])
    steps += [choose(426, node, label) for node, label in ((426, "We want to get into the prison."), (1, "Alright."),
                                                           (2, "No."), (3, "No."), (4, "Uhhh, no."))]
    steps += [{"assert": {"qbit_set": [key(convert.KEY_PASS)]}},
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_PASS, "count": 1}]}},
              {"assert": {"actor_visible": {"actor_index": scripted["actors"]["GuardCaptain0"],
                                          "hostile_to_party": False}}},
              {"note": {"text": "The cook (dialogue 419): the deal gives key 5004; closing gives 5005 and Celldoor29 "
                                "opens on a click (NPC419.scr)."}},
              {"execute_event": {"id": convert.EV_COOK_CAGE}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": door["Celldoor29"]["door_id"], "state": "closed"}}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_ON_MISSION), "value": True}}]
    steps += talk(floors, actors, "CommonerHuman2MaleA0", 419)
    steps += [choose(419, node, label) for node, label in (
        (419, "We've got a Visitor's Pass"), (1, "We've come to rescue Ivsar Forktooth."), (2, "Why not?"),
        (3, "Of course!  What sort of help did you need?"), (4, "And what will you do for us?"),
        (5, "Sounds like a deal!"))]
    steps += [{"assert": {"qbit_set": [key(convert.KEY_DEAL)]}},
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_COOK_DONE)]}},
              {"execute_event": {"id": convert.EV_COOK_CAGE}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": door["Celldoor29"]["door_id"], "state": "open"}}},
              {"note": {"text": "Antoni (dialogue 427): freed, his exit gives key 370 and the 4000 experience, and he "
                                "is gone (NPC427.scr)."}},
              {"execute_event": {"id": convert.EV_LEVER["lever3"]}},
              {"advance_runtime": {"seconds": 3}}]
    steps += talk(floors, actors, "Antoni", 427)
    steps += [choose(427, node, label) for node, label in (
        (427, "Are you the cooks brother?"), (1, "We're not guards.  We're here to rescue you."),
        (3, "No torture.  You're free to go."))]
    steps += [{"assert": {"qbit_set": [key(convert.KEY_BROTHER_FREED)]}},
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_BROTHER_REWARD)]}},
              {"note": {"text": "Ivsar (dialogue 90): Bjarni's men; his exit raises the alarm and he goes ahead "
                                "(NPC90.scr)."}},
              {"execute_event": {"id": convert.EV_LEVER["lever5"]}},
              {"advance_runtime": {"seconds": 5}}]
    steps += talk(floors, actors, "Ivsar", 90)
    steps += [choose(90, node, label) for node, label in ((90, "We've come to take you back to Sturmford."),
                                                          (1, "We've been sent by Bjarni Thorvaldssen to rescue you."))]
    steps += [{"assert": {"qbit_set": [key(convert.KEY_SENT_BY_BJARNI)]}},
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_HOSTILE)]}},
              {"assert": {"actor_visible": {"actor_index": scripted["actors"]["GuardCaptain0"],
                                          "hostile_to_party": True}}}]
    scenarios.write(PROJECT / "scenario_quests.yml", doc, "make_scenarios.py")

    # Every actor placed immobile (the gate guards, Ivsar, the prisoners, the cook) stays where the map put it.
    doc = {"id": "mm9r.drangheimprison_immobile", "title": "Drangheim Prison (native BLV) - immobile actors hold position",
           "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"],
           "steps": [{"load_map": {"map": MAP}}, {"advance_runtime": {"seconds": 30}}]}
    doc["steps"] += [{"assert": {"actor_visible": {"actor_index": a["actor_index"], "near": {
        "x": a["position"]["x"], "y": a["position"]["y"], "max_distance": 8}}}}
        for a in scene["initial_state"]["actors"] if a.get("immobile")]
    scenarios.write(PROJECT / "scenario_immobile.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
