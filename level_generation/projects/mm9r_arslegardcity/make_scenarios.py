#!/usr/bin/env python3
"""
Write the Arslegard City scenarios from the built map (work/doors.json, work/build_report.json, props.json, the scene):

    scenario_doors_exits.yml   the tavern's double door stops the party, opens on its click and the party walks in;
                               the Thousand Terrors' locked double door stays shut; the party walks into the exit
                               volumes of the Bath House, the Hall of the Gods' gate, the Thousand Terrors and the
                               Great Gate (Thjorgard), and falls into the chasm (ExitTrigger3, Thjorgard)
    scenario_shops.yml         walk-in shops by real clicks: the weaponsmith (Talik the Fist, RUDE 340) and the
                               armourer (Grim Olfassen, RUDE 341): the dialogue opens and its service row opens the shop
    scenario_ladders.yml       the temple front's ladders (Ladder6, Ladder7) from the towers' upper floors to the gallery
    scenario_scripted.yml      FateMan.scr (the first arrival: key 98, the cinematic gate_fate, the move to the Dark
                               Passageway), WritMan.scr (the Writ shown: key 9515, the cinematic gate_writ, the gate
                               opens, Hanndl gone), Njam's chase (key
                               470, Njam hostile), Hanndl's and Sven's dialogues, a letter, Njam's Struggle (GiveTake),
                               Njam's door with and without his key

    python3 level_generation/projects/mm9r_arslegardcity/make_scenarios.py
    for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_arslegardcity/scenario_$s.yml --scenario-no-color; done

The DAT has no TreasureChest or TreasureBag: there is no chest scenario.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import Project  # noqa: E402
import citylua  # noqa: E402
import gate_cinematics  # noqa: E402

MAP = "arslegardcity.blv"
# The temple front's ladders stand in its towers, on their upper floors (native 451), reached from the temple's balcony
# through a doorway in each tower's back wall: the probes start on the balcony in line with the doorway (a pose set on
# the south tower's upper floor itself lands on the porch under it: two outside portals at 512 reach into that tower).
# 2.5 s walks to the ladder, climbs it and glides off onto the top exit (the glide since 2026-11-10 takes about 0.5 s of
# it: at 2.0 s the party is still at the ladder's top); walking on from the top exit takes the ladder at its top again
# (grab_at_top) and climbs down, so the window is narrow (2.4-2.6 s pass).
TEMPLE_BALCONY = {"Ladder6": (2440, -1160), "Ladder7": (2440, 380)}
LADDER_SECONDS = 2.5
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
FATE = {"setup_shortcut": {"kind": "set_qbit", "id": 90000 + citylua.KEY_FATE, "value": True}}


def header(name: str, title: str, fate_done: bool = True) -> dict:
    steps = [{"load_map": {"map": MAP}}]
    if fate_done:
        steps.append(FATE)          # FateMan.scr would move the party to the Dark Passageway 3 s after the arrival
    return {"id": f"mm9r.arslegardcity_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": steps}


def key(raw: int) -> int:
    return 90000 + raw


def qbit(raw: int) -> dict:
    return {"setup_shortcut": {"kind": "set_qbit", "id": key(raw), "value": True}}


def var(name: str, value: int) -> dict:
    return {"assert": {"named_map_var_changed": {"name": name, "current": value}}}


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
    scene = yaml.safe_load((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    door = {m["node"][5:]: m for m in movers}
    scripted = report["scripted"]
    actors = {name: tuple(scene["initial_state"]["actors"][index]["position"][k] for k in "xyz")
              for name, index in scripted["actors"].items()}
    everyone = [(p[0], p[1]) for p in actors.values()]
    events = citylua.prop_events(None)
    ox, oy, oz = project.offset

    def native(x, z):
        return x * 2.56 - ox, z * 2.56 - oy

    def talk(name: str, rude: int) -> list:
        x, y, z = actors[name]
        return [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(140, 190), height=60,
                                  avoid=[a for a in everyone if a != (x, y)]),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    starts = {s["name"]: s["position"] for s in report["starts"]}

    def exit_walk(name: str, start_name: str, yaw: float, seconds: float = 2.0, back: float = 0.0) -> list:
        """From a start point (its floor; `back` units behind it, on the street), a forward walk into the exit volume."""
        row = next(t for t in report["transitions"] if t["name"] == name and t["source"] == MAP)
        index = int(row["id"].rsplit("/", 1)[1])
        x, y, z = starts[start_name]
        if back:
            x -= back * (yaw == 0) - back * (yaw == 180)
            y -= back * (yaw == 90) - back * (yaw == 270)
            z = floors.z(x, y, z + 40)
        far = (x + 600 * (yaw == 0) - 600 * (yaw == 180), y + 600 * (yaw == 90) - 600 * (yaw == 270))
        return [{"note": {"text": f"{name} (DAT object {index}) to {row['destination']}: from {start_name} the party "
                                  "walks into it."}},
                scenarios.movement(MAP, (x, y, z), yaw, seconds, (far[0], far[1], z), 900, 400),
                {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": index}}},
                {"load_map": {"map": MAP}}, FATE]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Arslegard City (native BLV) - the tavern's double door, a locked door, the exits")
    steps = doc["steps"]
    tavern = door["TavernDoor0"]
    # TavernDoor0/1 at LT x 5368, z -8032..-7904 (the tavern's west wall): walk east from the street into the tavern.
    sx, sy = native(5368, -7968)
    z = floors.z(sx - 300, sy, oz + 1000)
    steps += [{"note": {"text": f"TavernDoor0/1 (doors {tavern['door_id']}, event {tavern['event']}): shut, stops the "
                                "party, opens on its click; the party walks into the tavern."}},
              {"assert": {"mechanism": {"id": tavern["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (sx - 300, sy, z + 1), 0, 0.8, (sx - 40, sy, z + 1), 60, 40),
              {"execute_event": {"id": tavern["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": tavern["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (sx - 300, sy, z + 1), 0, 0.8, (sx + 300, sy, z + 1), 140, 40)]
    clank = door["ClankDoor1"]
    steps += [{"note": {"text": "ClankDoor1/2 (Locked, no key: the Thousand Terrors' door): a click says it is locked."}},
              {"execute_event": {"id": citylua.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": clank["door_id"], "state": "closed"}}}]
    # BathHouseExit stands on the edge of the door's second step (the walk stops there): from the street, up the steps
    steps += exit_walk("ExitTrigger0", "BathHouseExit", 270, 3.0, back=416)
    steps += exit_walk("ExitTriggerHall", "HallOfTheGodsExit", 0)       # east into the gate's shimmer
    steps += exit_walk("ExitTrigger1", "1000TerrorsExit", 180)          # west into the Thousand Terrors' door
    steps += exit_walk("ExitTrigger4", "StartPoint0", 90)               # north to the Great Gate
    cx, cy = native(3700, -7400)
    steps += [{"note": {"text": "ExitTrigger3 (DAT object 638, a row this map adds): the party falls into the chasm "
                                "through the city (its floor is sky) and lands in Thjorgard."}},
              {"set_pose": {"map": MAP, "x": int(cx), "y": int(cy), "z": -420, "yaw": 0.0, "pitch": 0.0}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": 638}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- shops ------------------------------------------------------------------------------------------------------
    doc = header("shops", "Arslegard City (native BLV) - walk-in shops: the shopkeepers' dialogues open by real "
                          "clicks and their service rows open the shops")
    steps = doc["steps"]
    steps += [{"advance_runtime": {"seconds": 1.5}}]
    for name, rude, label in (("ShopkeeperHuman2MaleA7", 340, "We'd like to see your wares."),
                              ("ShopkeeperHuman2MaleA6", 341, "We'd like to see your armor.")):
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
    doc = header("scripted", "Arslegard City (native BLV) - the Great Gate scene, Njam's chase, Hanndl, Sven, letters",
                 fate_done=False)
    steps = doc["steps"]
    gate = door["RotatingDoor0"]
    a = scripted["actors"]
    steps += [
        {"note": {"text": "FateMan.scr: the first arrival: after about 3 s the cinematic gate_fate (key 98 at once), "
                          "then at its end (71 s) the move to the Dark Passageway (ExitTrigger2's row). "
                          "cinematic_gate_fate_play.yml checks it step by step."}},
        {"advance_runtime": {"seconds": 1.0}},
        {"assert": {"qbit_clear": [key(citylua.KEY_FATE)]}},
        {"advance_runtime": {"seconds": 3.5}},
        {"assert": {"qbit_set": [key(citylua.KEY_FATE)]}},
        {"console": {"line": "cinematic list", "expect_contains": f"playing {gate_cinematics.FATE_ID}"}},
        {"advance_runtime": {"seconds": 72, "follow_map_move": True}},
        {"assert": {"map_arrived": {"map": "darkpassageway.blv"}}},
        {"note": {"text": "WritMan.scr: with the Writ shown (key 100): key 9515, 170 000 experience, Hanndl (the gate's "
                          "actor) removed, the Great Gate opens."}},
        {"load_map": {"map": MAP}}, qbit(citylua.KEY_WRIT),
        {"assert": {"mechanism": {"id": gate["door_id"], "state": "closed"}}},
        {"advance_runtime": {"seconds": 4.5}},
        {"assert": {"qbit_set": [key(citylua.KEY_WRIT_DONE)]}},
        {"console": {"line": "cinematic list", "expect_contains": f"playing {gate_cinematics.WRIT_ID}"}},
        {"assert": {"mechanism": {"id": gate["door_id"], "state": "closed"}}},
        # gate_writ's FadeOut2 (20.9 s) opens it; the gate swings slowly (MM9's Speed 5)
        {"advance_runtime": {"seconds": 22}},
        {"assert": {"mechanism": {"id": gate["door_id"], "state": "opening"}}},
        {"note": {"text": "NjamChase.scr: Trigger0 in Njam's house with the chase on (key 108): key 470, his door "
                          "unlocked, Njam hostile."}},
        {"load_map": {"map": MAP}}, FATE,
        {"assert": {"actor_visible": {"actor_index": a["NjamtheMeddler0"], "hostile_to_party": False}}},
        {"execute_event": {"id": citylua.EV_NJAM_TRIGGER}},
        {"assert": {"qbit_clear": [key(citylua.KEY_NJAM_DONE)]}},
        qbit(citylua.KEY_NJAM_CHASE),
        {"execute_event": {"id": citylua.EV_NJAM_TRIGGER}},
        {"assert": {"qbit_set": [key(citylua.KEY_NJAM_DONE)]}},
        {"advance_runtime": {"seconds": 0.5}},
        {"assert": {"actor_visible": {"actor_index": a["NjamtheMeddler0"], "hostile_to_party": True}}},
        {"execute_event": {"id": citylua.EV_NJAM_CELL}},
        {"advance_runtime": {"seconds": 3}},
        {"assert": {"mechanism": {"id": door["Njamdoor"]["door_id"], "state": "open"}}},
        {"note": {"text": "NjamDoor0/1 (Doorlock.scr 576): locked without Njam's Key, opens with it."}},
        {"execute_event": {"id": citylua.EV_NJAM_HOUSE}},
        {"advance_runtime": {"seconds": 2}},
        {"assert": {"mechanism": {"id": door["NjamDoor0"]["door_id"], "state": "closed"}}},
        {"grant_item": {"item_id": 10000 + citylua.ITEM_NJAM_KEY}},
        {"execute_event": {"id": citylua.EV_NJAM_HOUSE}},
        {"advance_runtime": {"seconds": 3}},
        {"assert": {"mechanism": {"id": door["NjamDoor0"]["door_id"], "state": "open"}}},
        {"note": {"text": "NPC334.scr: Hanndl the Gatekeeper by the gate opens his dialogue (RUDE 334). His row (555, "
                          "drawn by a 3D model) takes no headless click: interact_actor runs the click (Hall of the "
                          "Gods' lesson)."}},
        {"interact_actor": {"actor_index": a["Hanndl1"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 334}}},
    ]
    steps += [{"press_action": {"action": "cancel_dialog"}},
              {"note": {"text": "NPC3.scr: Sven Forkbeard is here with key 102 (and not 104); his click opens RUDE 3."}},
              qbit(102), {"load_map": {"map": MAP}}, FATE, {"advance_runtime": {"seconds": 1.5}},
              {"assert": {"actor_visible": {"actor_index": a["SvenSvenssen0"]}}},
              {"interact_actor": {"actor_index": a["SvenSvenssen0"]}}, {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"dialog": {"active": True, "source_id": 3}}},
              {"press_action": {"action": "cancel_dialog"}}]
    letter = next(name for name in events if name.startswith("Prop8") and name != "Prop8")
    steps += [{"note": {"text": f"BookLetter.scr: {letter} shows its text."}},
              {"execute_event": {"id": events[letter]}},
              {"assert": {"dialog": {"active": True}}},
              {"press_action": {"action": "cancel_dialog"}},
              {"note": {"text": "GiveTake.scr 575 1: Prop8, Njam's Struggle, a world item, picked up."}},
              *scenarios.pick_up_steps(floors, MAP, scene, "Prop8"),
              {"assert": {"inventory_any_member": [{"item_id": 10575, "count": 1}]}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- ladders: the temple front's two, from the towers' upper floors to the gallery over the door ----------------
    doc = header("ladders", "Arslegard City (native BLV) - the temple front's ladders (Ladder6, Ladder7): forward from "
                            "the foot climbs to the gallery over the door")
    for ladder in scene.get("ladders", []):
        bx, by, bz = ladder["bottom"]
        yaw = ladder["facing_degrees"]
        fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        hold = (bx - fx * 41, by - fy * 41)
        start = TEMPLE_BALCONY[ladder["id"]]
        top = ladder["top_exit"]
        doc["steps"] += [
            {"note": {"text": f"{ladder['id']}: from the temple's balcony through its tower's doorway onto the upper "
                              f"floor, forward takes the ladder, climbs it and steps off at {[round(v) for v in top]}."}},
            scenarios.movement(MAP, (start[0], start[1], bz + 1),
                               math.degrees(math.atan2(hold[1] - start[1], hold[0] - start[0])), LADDER_SECONDS, top,
                               tolerance_xy=80, tolerance_z=20)]
    scenarios.write(PROJECT / "scenario_ladders.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
