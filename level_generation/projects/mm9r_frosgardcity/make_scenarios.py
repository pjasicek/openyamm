#!/usr/bin/env python3
"""
Write the Frosgard City scenarios from the built map (work/doors.json, work/build_report.json, the scene):

    scenario_doors_exits.yml   the tavern's door stops the party, opens on its click and the party walks in; a facade
                               door stays locked; the bank's hatch opens with the banker's dialogue and shuts at its
                               exit; the north gate's exit raises its transition to the Frosgard wilderness
    scenario_shops.yml         walk-in shops by real clicks: Tryggva Ironhands (RUDE 201) and Thora the
                               Skull-toucher (RUDE 203) open their dialogues and "... see your wares/stuff." opens the shop
    scenario_scripted.yml      the location key 1029, shop hours (5017), a letter, the town portal altar (5015), the
                               maypole (267 + 500 gold -> 268), the powder barrel breaks the ice (71 -> 72, the floes
                               drop), the dockmaster's schedule (378), Jarl Tryggva's ice reward (73 -> 175), the Battle
                               of Frosgard starting on 104 (377)

No chest scenario: MM9 places no TreasureChest or TreasureBag in Frosgard City.

    python3 level_generation/projects/mm9r_frosgardcity/make_scenarios.py
    for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_frosgardcity/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios, town_portal  # noqa: E402
from dungeon.source import Project  # noqa: E402
import citylua  # noqa: E402

MAP = "frosgardcity.blv"
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
EXIT_NORTH = 46                     # DAT object index of ExitTrigger0 (map_transitions.txt row frosgardcity/46)
SCALE = 2.56
FORAD_RUDE = 2                      # convert.py FORAD_RUDE: NPC2.rude, Forad Darre


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.frosgardcity_{name}", "title": title, "world": "mm9", "mode": "faithful",
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
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = yaml.load((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    door = {m["node"][5:]: m for m in movers}
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

    def chat(name: str, rude: int) -> list:
        """The actor's click (its activation, as a real click runs it), the dialogue, its close."""
        return [{"interact_actor": {"actor_index": scripted["actors"][name]}}, {"advance_runtime": {"seconds": 0.3}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}},
                {"press_action": {"action": "cancel_dialog"}}, {"advance_runtime": {"seconds": 1.2}}]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Frosgard City (native BLV) - the tavern's door, a locked facade door, the bank's "
                                "hatch, the north gate's exit")
    steps = doc["steps"]
    tavern = door["Taverndoor"]
    # Taverndoor at LT (632, -1032), across z: walk south from the street into the tavern.
    sx, sy = 632 * SCALE, -1032 * SCALE
    z = floors.z(sx, sy + 300, 600)
    inside = floors.z(sx, sy - 300, 150)        # the tavern's floor, 17 LT (44 native) up its doorstep
    doorstep = max(floors.z(sx, sy + 40 + d, 120) or z for d in range(-36, 37, 4))
    steps += [{"note": {"text": f"Taverndoor (door {tavern['door_id']}, event {tavern['event']}): shut, stops the party, "
                                "opens on its click; the party walks into the tavern."}},
              {"assert": {"mechanism": {"id": tavern["door_id"], "state": "closed"}}},
              # the shut door stops the body over the doorstep: it stands on the highest floor under its radius
              # (the threshold, 44 up, reaches under the front of the body)
              scenarios.movement(MAP, (sx, sy + 300, z + 1), 270, 0.8, (sx, sy + 40, doorstep + 1), 60, 40),
              {"execute_event": {"id": tavern["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": tavern["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (sx, sy + 300, z + 1), 270, 0.8, (sx, sy - 300, inside + 1), 140, 40)]
    facade = door["Door14"]
    steps += [{"note": {"text": "Door14 (a facade door, Locked, MoveDist 0): a click says it is locked; it stays shut."}},
              {"execute_event": {"id": citylua.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": facade["door_id"], "state": "closed"}}}]
    hatch = door["Bankdoor_INV"]          # the hatch is invisible faces only (citylua.py)
    steps += [{"note": {"text": "The bank's hatch (Bankdoor): a click opens it and the banker's dialogue (RUDE 206); "
                                "the dialogue's exit shuts it (NPC206.scr :OnRude toggles bankdoor)."}},
              {"execute_event": {"id": citylua.EV_BANK}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"dialog": {"active": True, "source_id": 206}}},
              # the open dialogue pauses the world: the hatch is still on its way
              {"assert": {"mechanism": {"id": hatch["door_id"], "state": "opening"}}},
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": hatch["door_id"], "state": "closed"}}}]
    north = next(t for t in report["transitions"] if t["name"] == "ExitTrigger0" and t["source"] == MAP)
    nx, ny, nz = (int(v) for v in north["centre"])
    z = floors.z(nx, ny - 450, 1000)
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 46): the north gate road to the Frosgard wilderness."}},
              scenarios.movement(MAP, (nx, ny - 450, z + 1), 90, 1.2, (nx, ny + 100, z + 1), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_NORTH}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- shops ------------------------------------------------------------------------------------------------------
    doc = header("shops", "Frosgard City (native BLV) - walk-in shops: the shopkeepers' dialogues open by real clicks "
                          "and their service rows open the shops")
    steps = doc["steps"]
    steps += [{"advance_runtime": {"seconds": 1.5}}]
    for name, rude, label in (("201", 201, "Yes.  We'd like to see your wares."),
                              ("203", 203, "We'd like to see your stuff.")):
        steps += [{"note": {"text": f"{name} (RUDE {rude}) in the shop: a click opens the dialogue; \"{label}\" opens "
                                    "the shop."}}]
        steps += talk(name, rude)
        steps += [choose(rude, rude, label),
                  {"advance_runtime": {"seconds": 0.5}},
                  {"assert": {"dialog": {"active": True, "house_dialog": True}}},
                  {"press_action": {"action": "cancel_dialog"}}, {"press_action": {"action": "cancel_dialog"}},
                  {"advance_runtime": {"seconds": 0.5}}]
    scenarios.write(PROJECT / "scenario_shops.yml", doc, "make_scenarios.py")

    # --- scripted ---------------------------------------------------------------------------------------------------
    doc = header("scripted", "Frosgard City (native BLV) - location key, shop hours, a letter, the altar, the maypole, "
                             "the ice, the dockmaster, Tryggva's reward, the battle")
    steps = doc["steps"]
    first_ice = door["DestructableBrush27"]
    last_ice = door["DestructableBrush8"]
    letter = next(name for name in events if name.startswith("Prop") and name not in citylua.COGS)
    steps += [
        {"note": {"text": "ForadWorld.scr: the location key 1029 on load; shops close (5017) from 20:00 to 06:00."}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"qbit_set": [key(1029)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(5017)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_clear": [key(5017)]}},
        {"note": {"text": f"BookLetter.scr: {letter} shows its text."}},
        {"execute_event": {"id": events[letter]}},
        {"assert": {"dialog": {"active": True}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"note": {"text": "NPC190.scr: with the maypole task (267) and 500 gold, the dialogue's close pays for the new "
                          "maypole (268)."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(267), "value": True}},
        {"console": {"line": "gold set 1000"}},
    ]
    steps += chat("190", 190)
    steps += [{"assert": {"qbit_set": [key(268)]}},
              {"note": {"text": "BreakIce.scr: with the quest (71) and the powder delivered (1022), the barrel on the ice "
                                "goes off; its cinematic (break_ice, 16.3 s) drops the floes in MM9's waves and the quest is "
                                "done (72)."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(71), "value": True}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(1022), "value": True}},
              {"assert": {"mechanism": {"id": first_ice["door_id"], "state": "closed"}}},
              {"execute_event": {"id": citylua.EV_BARREL}},
              {"advance_runtime": {"seconds": 17}},
              {"assert": {"qbit_set": [key(72)]}},
              {"assert": {"mechanism": {"id": first_ice["door_id"], "state": "open"}}},
              {"assert": {"mechanism": {"id": last_ice["door_id"], "state": "open"}}},
              {"note": {"text": "NPC209.scr: the dockmaster gives the dock schedule (378) once the docks are free."}}]
    steps += chat("Dockmaster", 209)
    steps += [{"assert": {"qbit_set": [key(378)]}},
              {"note": {"text": "NPC180.scr: Jarl Tryggva's reward for the ice (73 -> 175)."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(73), "value": True}}]
    steps += chat("TryggvaRavenlocks0", 180)
    steps += [{"assert": {"qbit_set": [key(175)]}},
              {"note": {"text": "BattleMan.scr: entering on key 104 starts the Battle of Frosgard (377): the Horde and "
                                "the clan soldiers come, Forad Darre and Tamur Leng appear."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(104), "value": True}},
              {"load_map": {"map": MAP}},
              {"advance_runtime": {"seconds": 1.5}},
              {"assert": {"qbit_set": [key(377)]}}]
    # Forad.scr :OnAppear (BattleMan's Appear) -> OnTargetWithinDist 16 :Talk: he opens his dialogue himself when the
    # party comes near (citylua approach_talk, reach = his radius + the party's + 16 LT); its close with key 104 turns
    # him on the party
    forad = scripted["actors"]["ForadDarre"]
    fx, fy, fz = actors["ForadDarre"]
    far_z, near_z = (int(round(floors.z(fx - d, fy, fz + 100) or fz)) for d in (500, 110))
    steps += [{"note": {"text": "Forad.scr :OnAppear: after the battle starts Forad talks by himself when the party "
                                "comes within 16 LT of him (no click); closing it with 104 turns him on the party."}},
              {"assert": {"actor_visible": {"actor_index": forad, "hidden": False}}},
              {"set_pose": {"map": MAP, "x": fx - 500, "y": fy, "z": far_z + 1, "yaw": 0.0, "pitch": 0.0}},
              {"advance_runtime": {"seconds": 1.0, "present_dialogs": True}},
              {"assert": {"dialog": {"active": False}}},
              {"set_pose": {"map": MAP, "x": fx - 110, "y": fy, "z": near_z + 1, "yaw": 0.0, "pitch": 0.0}},
              # present_dialogs: a headless run otherwise leaves a map script's dialogue queued
              {"advance_runtime": {"seconds": 0.6, "present_dialogs": True}},
              {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": FORAD_RUDE}}},
              {"assert": {"dialog": {"active": True, "source_id": FORAD_RUDE}}},
              {"press_action": {"action": "cancel_dialog"}}, {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"actor_visible": {"actor_index": forad, "hostile_to_party": True}}}]
    doc["steps"] += town_portal.scenario_steps(PROJECT / "props.json", events, MAP)   # TownPortal.scr
    # NPC378.scr :Init (key 83) -> OnFoundPlayer :OnFound: Thorolf0 sees the party, runs to it (RunTo 16) and talks
    # (DoRude 378), and Thorolf1 is removed (dungeon/lua.py thorolf_approaches)
    tx, ty, tz = actors["Thorolf0"]
    pose_z = int(round(floors.z(tx - 700, ty, tz + 100) or tz))
    doc["steps"] += [
        {"note": {"text": "NPC378.scr :OnFound: with key 83 Thorolf runs up to the party that he sees and talks (RUDE "
                          "378); the other copy goes."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(83), "value": True}},
        {"load_map": {"map": MAP}},
        {"advance_runtime": {"seconds": 1.0}},
        {"set_pose": {"map": MAP, "x": tx - 700, "y": ty, "z": pose_z + 1, "yaw": 0.0, "pitch": 0.0}},
        {"advance_runtime": {"seconds": 6.0, "present_dialogs": True}},
        {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": 378}}},
        {"assert": {"dialog": {"active": True, "source_id": 378}}},
        {"assert": {"actor_visible": {"actor_index": scripted["actors"]["Thorolf1"], "hidden": True}}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
