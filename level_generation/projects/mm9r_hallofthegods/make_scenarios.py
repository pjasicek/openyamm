#!/usr/bin/env python3
"""
Write the Hall of the Gods scenarios from the built map (work/content.json, work/build_report.json, the scene,
props.json):

    scenario_doors_exits.yml   the party walks from the start into the hall and up the stair to the throne hall; the
                               gate's shimmer (ExitTriggerHall) raises the transition to Arslegard City
    scenario_scripted.yml      the bill of sale by a real click (BookLetter.scr 480); the end of the game (WinMan.scr
                               Part2): with key 109 the cinema's gods appear and Krohn0 is hidden, Hanndl stands at his
                               mark (the cinematic gods_epilogue), after it the Writ of Fate (394) is given and Krohn0 is back; no second
                               cinema once the Writ is held
    scenario_quests.yml        RUDE dialogues by real clicks (Krohn 335, Skraelos 336, Fre 337, the Great Honk 377) and
                               their OnRudeExit events (Njam's Key, the six fires' reward, the Golden Honk, Skraelos'
                               teleport to the Afterworld)
    scenario_immobile.yml      the immobile gods hold their places for 30 s

    python3 level_generation/projects/mm9r_hallofthegods/make_scenarios.py
    for s in doors_exits scripted quests immobile; do ./build/game/openyamm \\
        --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario \\
        level_generation/projects/mm9r_hallofthegods/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
import cinematics_hall  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "hallofthegods.blv"


def key(raw: int) -> int:
    return 90000 + raw


def item(raw: int) -> int:
    return 10000 + raw


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.hallofthegods_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def var(name: str, value: int) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())} \
        if (PROJECT / "props.json").exists() else {}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = yaml.load((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    scripted = report["scripted"]
    actor = scripted["actors"]
    actor_pos = {a["actor_index"]: (a["position"]["x"], a["position"]["y"], a["position"]["z"])
                 for a in scene["initial_state"]["actors"]}
    facing = {a["actor_index"]: a["initial_yaw_units"] / 2048 * 360 for a in scene["initial_state"]["actors"]}
    shown = [actor_pos[actor[n]][:2] for n in actor if n not in scripted["cinema"]]
    start = report["starts"][0]["position"]
    table = PROJECT.parents[2] / "output/mm9_rework/assets_dev/worlds/mm9/data_tables/map_transitions.txt"
    rows = {line.split("\t")[0]: line.split("\t") for line in table.read_text(encoding="latin-1").splitlines()}
    gate = {"centre": rows["mm9:transition/hallofthegods/142"][6:9]}       # the review root's row (CenterX, Y, Z)

    # --- walks and the gate ---------------------------------------------------------------------------------------
    doc = header("doors_exits", "Hall of the Gods (native BLV) - from the start into the hall and up to the throne; "
                                "the gate's shimmer to Arslegard City")
    steps = doc["steps"]
    y = start[1]
    throne_hall = floors.z(900 * SCALE, 1400 * SCALE, 2000)     # the throne hall's floor past the landing's riser
    lane = 1400 * SCALE                 # LT z 1400: north of the pool's basin on the hall's axis
    steps += [{"note": {"text": "From inside the gate (LT x -2700) east along LT z 1400 (the pool's basin stands on the "
                                "axis) to the foot of the stair (LT x -800)."}},
              scenarios.movement(MAP, (-2700 * SCALE, lane, 1), 0, round(1900 * SCALE / scenarios.WALK, 2),
                                 (-800 * SCALE, lane, 1), 300, 20),
              {"note": {"text": "Up the stair, over its top landing (LT 256) and the landing's last 8 LT riser into the "
                                "throne hall (LT x 900), as on the desktop (work/walkdbg/collision_trace.txt). Headless "
                                "the walk used to stop at that riser; since 2026-11-07 it walks on."}},
              scenarios.movement(MAP, (-800 * SCALE, lane, 1), 0, round(1700 * SCALE / scenarios.WALK, 2),
                                 (900 * SCALE, lane, throne_hall), 120, 20),
              {"note": {"text": "ExitTriggerHall: the shimmer in the gate west of the start (to Arslegard City, "
                                "HallOfTheGodsExit)."}},
              scenarios.movement(MAP, start, 180, 1.0, (float(gate["centre"][0]), y, 1), 400, 40),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": 142}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- scripted: the letter and the end of the game -----------------------------------------------------------------
    doc = header("scripted", "Hall of the Gods (native BLV) - the bill of sale; the end of the game (WinMan.scr Part2)")
    steps = doc["steps"]
    if "Prop3" in props:
        entry = props["Prop3"]
        steps += [{"note": {"text": "Prop3 (BookLetter.scr '480 Letter 1'): a real click shows the bill of sale."}},
                  scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                    distances=(90, 110, 130), height=2, avoid=shown),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 0.3}},
                  {"assert": {"dialog": {"active": True}}}, {"press_action": {"action": "cancel_dialog"}}]
    cinema = [actor[n] for n in scripted["cinema"]]
    krohn0 = actor["Krohn0"]
    mark = [int(v) for v in report["hanndl_mark"]]
    steps += [{"note": {"text": "Without key 109 the cinema's gods stay hidden and Krohn sits on his throne."}},
              {"advance_runtime": {"seconds": 1}},
              *[{"assert": {"actor_visible": {"actor_index": a, "hidden": True}}} for a in cinema],
              {"assert": {"actor_visible": {"actor_index": krohn0, "hidden": False}}},
              {"note": {"text": "Njam beaten (key 109): on arrival the gods gather (Hanndl at his mark, the Wyrdes, Krohn "
                                "and Skraelos), Krohn0 leaves his throne; after the cinema the Writ of Fate is given."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_NJAM_BEATEN), "value": True}},
              {"load_map": {"map": MAP}}, {"advance_runtime": {"seconds": 2}},
              {"console": {"line": "cinematic list", "expect_contains": "playing gods_epilogue"}},
              *[{"assert": {"actor_visible": {"actor_index": a, "hidden": False}}} for a in cinema],
              {"assert": {"actor_visible": {"actor_index": krohn0, "hidden": True}}},
              {"note": {"text": "Hanndl walks to his mark, stopping 75 LT short as MM9's WalkTo (the cinematic "
                                "gods_epilogue, cinematics_hall.py: 12.7 s)."}},
              {"advance_runtime": {"seconds": 14}},
              {"assert": {"actor_visible": {"actor_index": actor["Hanndl"], "near": {
                  "x": mark[0], "y": mark[1], "max_distance": cinematics_hall.WALK_STOP_SHORT_LT * SCALE + 40}}}},
              {"advance_runtime": {"seconds": cinematics_hall.epilogue_seconds() - 16 + 2}},
              var("CinemaDone", 1),
              {"assert": {"inventory_any_member": [{"item_id": item(convert.ITEM_WRIT), "count": 1}]}},
              *[{"assert": {"actor_visible": {"actor_index": a, "hidden": True}}} for a in cinema],
              {"assert": {"actor_visible": {"actor_index": krohn0, "hidden": False}}},
              {"note": {"text": "With the Writ held the cinema does not run again."}},
              {"load_map": {"map": MAP}}, {"advance_runtime": {"seconds": 2}},
              *[{"assert": {"actor_visible": {"actor_index": a, "hidden": True}}} for a in cinema]]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- quests (RUDE) ----------------------------------------------------------------------------------------------
    # Krohn (row 565 KnightPlate A) and Skraelos (568 BLich A) draw the MM6 world's 3D models; headless picking has no
    # hit shape for a model actor (every pose missed, work/dbg_krohn.yml), so their talks go through interact_actor
    # (the click's own activation path); the sprite actors (Fre, the Great Honk) take real clicks.
    MODEL_ACTORS = {"Krohn0", "Skraelos"}

    def talk(name, rude):
        a = actor[name]
        x, y, z = actor_pos[a]
        avoid = [p for p in shown if p != (x, y)]
        pose = scenarios.look_at(floors, MAP, (x, y, z), facing[a] - 90, distances=(200, 250, 300, 160), height=90,
                                 avoid=avoid, max_drop=200)
        if name in MODEL_ACTORS:
            return [pose, {"advance_runtime": {"seconds": 0.2}}, {"interact_actor": {"actor_index": a}}, {"advance_runtime": {"seconds": 0.3}},
                    {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                    {"assert": {"dialog": {"active": True, "source_id": rude}}}]
        x, y, z = actor_pos[a]
        avoid = [p for p in shown if p != (x, y)]
        # in front of the actor first (look_at takes a model yaw: an actor's facing minus 90)
        return [scenarios.look_at(floors, MAP, (x, y, z), facing[a] - 90, distances=(200, 250, 300, 160), height=90, avoid=avoid,
                                  max_drop=200),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 0.3}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    def close() -> list:
        return [{"press_action": {"action": "cancel_dialog"}}, {"advance_runtime": {"seconds": 1}}]

    doc = header("quests", "Hall of the Gods (native BLV) - the gods' RUDE dialogues by real clicks and their "
                           "OnRudeExit events")
    steps = doc["steps"]
    steps += [{"note": {"text": "Every god is the party's friend (MM9's gods; the picture rows' relations are lent the "
                                "peasant family's: ally 118)."}},
              *[{"assert": {"actor_visible": {"actor_index": actor[n], "hostile_to_party": False}}} for n in actor],
              {"note": {"text": "The Great Honk (NPC377.scr :OnUse DoRude 377)."}},
              *talk("TheGreatHonk0", 377), *close(),
              {"note": {"text": "Krohn (NPC335.scr :StopNjam): nothing without key 108; with it Njam's Key, key 191."}},
              *talk("Krohn0", 335), *close(),
              {"assert": {"qbit_clear": [key(convert.KEY_NJAM_DONE)]}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_TAMUR), "value": True}},
              *talk("Krohn0", 335), *close(),
              {"assert": {"qbit_set": [key(convert.KEY_NJAM_DONE)]}},
              {"assert": {"inventory_any_member": [{"item_id": item(convert.ITEM_NJAM_KEY), "count": 1}]}},
              {"note": {"text": "Fre (NPC337.scr :GoldenHonk): key 346 and the Golden Honk give 10000 gold and key 347."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_HONK_FOUND), "value": True}},
              {"grant_item": {"item_id": item(convert.ITEM_GOLDEN_HONK), "count": 1}},
              *talk("Fre", 337), *close(),
              {"assert": {"qbit_set": [key(convert.KEY_HONK_DONE)]}},
              {"note": {"text": "Skraelos (NPC336.scr :sixfires): key 103 gives key 189 and 52000 experience."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_FIRES_DONE), "value": True}},
              *talk("Skraelos", 336), *close(),
              {"assert": {"qbit_set": [key(convert.KEY_FIRES_REWARD)]}},
              var("ToAfterworld", 0),
              {"note": {"text": "Skraelos (:Teleport): key 101 without 102 gives key 379 and sends the party to the "
                                "Afterworld (ExitTrigger0's arrival)."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_SENT), "value": True}},
              *talk("Skraelos", 336), *close(),
              {"assert": {"qbit_set": [key(convert.KEY_ARRIVED)]}},
              # evt.MoveToMap is applied by the frame loop (headless advance_runtime does not move the party: the
              # Chasm of the Dead's lesson): the request is asserted by its counter, the move checked on the desktop.
              var("ToAfterworld", 1)]
    scenarios.write(PROJECT / "scenario_quests.yml", doc, "make_scenarios.py")

    doc = {"id": "mm9r.hallofthegods_immobile", "title": "Hall of the Gods (native BLV) - the gods hold position",
           "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"],
           "steps": [{"load_map": {"map": MAP}}, {"advance_runtime": {"seconds": 30}}]}
    doc["steps"] += [{"assert": {"actor_visible": {"actor_index": a["actor_index"], "near": {
        "x": a["position"]["x"], "y": a["position"]["y"], "max_distance": 8}}}}
        for a in scene["initial_state"]["actors"] if a.get("immobile") and a["actor_index"] not in
        [actor[n] for n in scripted["cinema"]]]
    scenarios.write(PROJECT / "scenario_immobile.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
