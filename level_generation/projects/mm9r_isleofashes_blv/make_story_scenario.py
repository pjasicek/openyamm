#!/usr/bin/env python3
"""
Write story.yml: the headless scenario of the Isle of Ashes chain on this BLV (the ODM pilot's
../mm9r_isleofashes/make_story_scenario.py, with poses from this build's scene and BLV, its door ids, and the arrival
in sturmford.blv). Run convert.py first, then:

    python3 level_generation/projects/mm9r_isleofashes_blv/make_story_scenario.py
    (prints the command that runs it against output/mm9_rework/isleofashes_blv_root)
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT))
from util.map_export import parse_blv_file  # noqa: E402

MAP = "isleofashes.blv"
ASSETS = ROOT / "output/mm9_rework/isleofashes_blv_root"
SCENE = ASSETS / "worlds/mm9/maps/isleofashes.scene.yml"
EYE = 176
LECTERN_EVENT = 30496               # Prop159's Use (PropTrigger.scr 'Book Use')
TURRET_KEY = 10568


def main() -> int:
    scene = json.loads(SCENE.read_text())
    blv = parse_blv_file(ASSETS / "worlds/mm9/maps" / MAP)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] if isinstance(v, dict) else v for v in blv["vertices"]], float)
    actors = {a["mm9_source_object_index"]: a for a in scene["initial_state"]["actors"]
              if "mm9_source_object_index" in a}
    doors = {json_door["door_id"]: json_door for json_door in json.loads((PROJECT / "work/doors.json").read_text())}
    bunker_ids = [door_id for door_id, door in doors.items() if door["group"] == "BunkerDoor"]
    scene_doors = {d["door_id"]: d for d in scene["initial_state"]["doors"]}
    door_points = vertices[[v for f in scene_doors[bunker_ids[0]]["face_ids"] for v in blv["faces"][f]["vertex_indices"]]]
    door_x, door_y = door_points[:, 0].mean() + 40, door_points[:, 1].mean()
    door_floor, door_z = door_points[:, 2].min(), door_points[:, 2].mean()
    lectern = next(e for e in blv["entities"] if e["event_id_secondary"] == LECTERN_EVENT)["position"]

    def index(source):
        return actors[source]["actor_index"]

    yrsa, forad, annud = index(46), index(61), index(747)
    flyers = [index(source) for source in (21, 22, 23, 26, 27, 31, 32, 33)]      # 8 of KillControl's 12

    def near(source, dx=-160, dy=0):
        position = actors[source]["position"]
        return {"set_pose": {"map": MAP, "x": position["x"] + dx, "y": position["y"] + dy, "z": position["z"],
                             "yaw": 0.0, "pitch": 0.0}}

    def talk(actor, rows, note):
        steps = [{"note": {"text": note}}, {"interact_actor": {"actor_index": actor}},
                 {"assert": {"dialog": {"active": True}}}]
        return steps + [{"select_topic": {"action_id": row}} for row in rows]

    def facing(x, y, z, floor, distance=150):
        """Stand south of a point on the floor under it, looking north at it."""
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y - distance)), "z": int(round(floor)),
                             "yaw": round(math.pi / 2, 4), "pitch": round(math.atan2(z - (floor + EYE), distance), 4)}}

    def door_state(door_id, state):
        return {"assert": {"mechanism": {"id": door_id, "state": state}}}

    steps = [{"new_game_flow": {"start_map": MAP}}]
    # Forad Darre at the bridge (FORAD.scr OnUse, NPC2 node 2): the crash, Yrsa's name (477); OnRudeExit 368.
    steps.append(near(61))
    steps += talk(forad, [4, 14, 1], "Forad Darre: the crash, Yrsa's name (477); OnRudeExit 368 + 4000 xp")
    steps.append({"assert": {"qbit_set": [90480, 90477, 90368], "qbit_clear": [90029]}})
    # Yrsa (YRSA.scr OnUse, NPC1): the dragonfly task (7).
    steps.append(near(46))
    steps += talk(yrsa, [20, 9], "Yrsa: the dragonfly task (7)")
    steps.append({"assert": {"qbit_set": [90365, 90007], "qbit_clear": [90027]}})
    # The dragonflies: the eighth death of KillControl's senders gives key 27 (tm_Hardrock.scr '8 27 200').
    steps.append(near(21, dx=-600))
    for flyer in flyers[:7]:
        steps.append({"damage_actor": {"actor_index": flyer, "amount": 30000}})
    steps += [{"advance_runtime": {"seconds": 1}}, {"assert": {"qbit_clear": [90027]}},
              {"damage_actor": {"actor_index": flyers[7], "amount": 30000}}, {"advance_runtime": {"seconds": 1}},
              {"note": {"text": "the eighth OneDown gives key 27"}}, {"assert": {"qbit_set": [90027]}}]
    # Yrsa again: destiny (1); OnRudeExit 366 and 367.
    steps.append(near(46))
    steps += talk(yrsa, [5, 10, 6, 7, 0, 1, 2, 3], "Yrsa: destiny (1); OnRudeExit dragonfly 366 and mainline 367")
    steps.append({"assert": {"qbit_set": [90001, 90366, 90367]}})
    # The bunker is locked without the Turret Key (DoorLock.scr 568).
    steps += [facing(door_x, door_y, door_z, door_floor), {"press_interact": {}}, {"advance_runtime": {"seconds": 2}},
              door_state(bunker_ids[0], "closed")]
    # Forad joins (hire row: 29 and 371); its "Welcome Aboard." ends the dialogue, whose exit runs OnRude: he leaves.
    steps.append(near(61))
    steps += talk(forad, [4, 7, 2, 15, 10, 11, 12], "Forad Darre joins: hire row grants 29 and 371")
    steps += [{"assert": {"dialog": {"active": False}}},
              {"assert": {"qbit_set": [90029, 90371]}},
              {"assert": {"actor_visible": {"actor_index": forad, "hidden": True}}}]
    # Yrsa: the Turret Key (469, item 568).
    steps.append(near(46))
    steps += talk(yrsa, [24, 9], "Yrsa: the Turret Key (469, item 568)")
    steps += [{"assert": {"qbit_set": [90469], "held_item": {"active": True, "item_id": TURRET_KEY}}},
              {"assert": {"held_item": {"active": False, "item_id": TURRET_KEY}}},
              {"assert": {"inventory_any_member": [{"item_id": TURRET_KEY}]}}]
    # The bunker opens with the key, which it keeps.
    steps += [facing(door_x, door_y, door_z, door_floor), {"press_interact": {}}, {"advance_runtime": {"seconds": 2.5}}]
    steps += [door_state(door_id, "open") for door_id in bunker_ids]
    steps += [{"assert": {"inventory_any_member": [{"item_id": TURRET_KEY, "count": 0}]}}]
    # The book on the lectern: the cinematic (book_sinking plays on runtime), key 28 and 5200 xp at OnSink (4.5 s),
    # then Sturmford at FadeOut2 (17 s, ExitTrigger1).
    steps += [facing(lectern["x"], lectern["y"], lectern["z"] + 90, lectern["z"], distance=140),
              {"execute_event": {"id": LECTERN_EVENT}},
              {"advance_runtime": {"seconds": 4.0}}, {"assert": {"qbit_clear": [90028]}},
              {"advance_runtime": {"seconds": 1.0}}, {"note": {"text": "OnSink (4.5 s): key 28, 5200 xp"}},
              {"assert": {"qbit_set": [90028]}},
              {"advance_runtime": {"seconds": 12.0, "follow_map_move": True}},
              {"note": {"text": "FadeOut2 (17 s): ExitTrigger1 to Sturmford"}},
              {"assert": {"map_arrived": {"map": "sturmford.blv"}}}]
    # A later visit: Annud Redeye at the dock offers passage (NPC138 line 3). His Fre's Rain sails on Tuesday to
    # Thursday, Saturday and Sunday (transport_routes.txt dock 138, MM9's BoatSchedule), not on the new game's first
    # day: the visit is a day later. "We'd like passage" lists the day's voyage (a transport action, id 0) with the
    # schedule and Back.
    steps += [{"advance_game_time": {"days": 1}},
              {"load_map": {"map": MAP}},
              {"assert": {"actor_visible": {"actor_index": annud, "hidden": False}}},
              {"assert": {"actor_visible": {"actor_index": yrsa, "hidden": True}}},
              near(747)]
    steps += talk(annud, [2], "Annud Redeye: passage to Sturmford (transport_routes.txt dock 138)")
    steps += [{"select_topic": {"action_id": 0}}, {"assert": {"map_arrived": {"map": "sturmford.blv"}}}]
    document = {"id": "mm9r.isleofashes_blv.story", "world": "mm9", "mode": "faithful", "steps": steps}
    path = PROJECT / "story.yml"
    path.write_text("# The Isle of Ashes story chain on the BLV. Written by make_story_scenario.py.\n"
                    + yaml.safe_dump(document, sort_keys=False))
    run = PROJECT / "work/scenario_run"
    run.mkdir(parents=True, exist_ok=True)
    settings = (ROOT / "output/mm9_rework/scenario_run/settings.ini").read_text().split("\n")
    (run / "settings.ini").write_text("\n".join(f"root={ASSETS}" if line.startswith("root=") else line
                                                for line in settings))
    print(path)
    print(f"cd {run} && {ROOT}/build/game/openyamm --world mm9 --headless-run-scenario {path} --scenario-no-color")
    return 0


if __name__ == "__main__":
    sys.exit(main())
