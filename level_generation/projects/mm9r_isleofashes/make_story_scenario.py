#!/usr/bin/env python3
"""
Write story.yml: a headless scenario of the Isle of Ashes chain on the remade map, from the arrival to the departure
for Sturmford, then a later visit with Annud Redeye's passage. Poses come from the built scene (run convert.py
first); dialogue choices are RUDE row indices (the source line minus one). Run it from output/mm9_rework/scenario_run:

    python3 level_generation/projects/mm9r_isleofashes/make_story_scenario.py
    cd output/mm9_rework/scenario_run && ../../../build/game/openyamm --world mm9 \\
        --headless-run-scenario ../../../level_generation/projects/mm9r_isleofashes/story.yml --scenario-no-color
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import convert  # noqa: E402

MAP = convert.MAP
EYE = 176
# story.lua's timer (event 31000, every 0.25 s) runs the cinema. Headless runs do not advance outdoor map timers (the
# scene's frame update belongs to the game view), so the scenario runs the timer's event once per tick.
STORY_TIMER_EVENT = 31000
TICK_SECONDS = 0.25


def story_ticks(count):
    return [{"execute_event": {"id": STORY_TIMER_EVENT}} for _ in range(int(round(count)))]


def main() -> int:
    scene = json.loads((convert.SOURCE / f"{convert.STEM}.scene.yml").read_text())
    native = convert.parse_odm_file(convert.review_root.mirror_path(Path("worlds/mm9/maps") / MAP))["payload"]
    heights = np.array(native["height_map"], dtype=np.float64).reshape(convert.GRID, convert.GRID) * 32
    actors = {a["mm9_source_object_index"]: (index, a) for index, a in enumerate(scene["initial_state"]["actors"])}
    models = {b["name"]: b for b in native["bmodels"]}
    entities = {e["event_id_secondary"]: e for e in scene["entities"] if e["event_id_secondary"]}

    def entities_by_source(source):
        return entities[30000 + source]
    yrsa, forad, annud = actors[46][0], actors[61][0], actors[747][0]
    flyers = [actors[source][0] for source in (21, 22, 23, 26, 27, 31, 32, 33)]      # 8 of KillControl's 12

    def near(source, dx=-160, dy=0):
        position = actors[source][1]["position"]
        return {"set_pose": {"map": MAP, "x": position["x"] + dx, "y": position["y"] + dy, "z": position["z"],
                             "yaw": 0.0, "pitch": 0.0}}

    def talk(actor, rows, note):
        steps = [{"note": {"text": note}}, {"interact_actor": {"actor_index": actor}},
                 {"assert": {"dialog": {"active": True}}}]
        steps += [{"select_topic": {"action_id": row}} for row in rows]
        return steps

    def facing(x, y, z, distance=150):
        """Stand south of a point, looking north at it."""
        ground = convert.ground_at(heights, x, y - distance)
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y - distance)), "z": int(round(ground)),
                             "yaw": round(math.pi / 2, 4), "pitch": round(math.atan2(z - (ground + EYE), distance), 4)}}

    door = models["BMODEL_BunkerDoor1"]
    door_x = (door["bounds_min"]["x"] + door["bounds_max"]["x"]) / 2 + 40
    door_y = (door["bounds_min"]["y"] + door["bounds_max"]["y"]) / 2
    door_z = (door["bounds_min"]["z"] + door["bounds_max"]["z"]) / 2
    lectern = entities[30496]["position"]     # Prop159: the book itself has no pick radius (decoration row)
    turret_key = 10568

    steps = [{"new_game_flow": {"start_map": MAP}}]
    # Forad Darre at the bridge: FORAD.scr OnUse (480, 800 xp), NPC2 node 2. Line 5 "Our boat crashed" -> node 3,
    # line 15 "No. Who is that?" (forbids 1; grants 477) -> node 4, line 2 "Goodbye." closes: OnRude gives 368, 4000 xp.
    steps.append(near(61))
    steps += talk(forad, [4, 14, 1], "Forad Darre: the crash, Yrsa's name (477); OnRudeExit 368 + 4000 xp")
    steps.append({"assert": {"qbit_set": [90480, 90477, 90368], "qbit_clear": [90029]}})
    # Yrsa: YRSA.scr OnUse (480, 365, 800 xp), NPC1 node 1. Line 21 "Who are you?" (forbids 27; grants 7) -> 999,
    # line 10 "Goodbye" closes.
    steps.append(near(46))
    steps += talk(yrsa, [20, 9], "Yrsa: the dragonfly task (7)")
    steps.append({"assert": {"qbit_set": [90365, 90007], "qbit_clear": [90027]}})
    # The dragonflies beyond the tunnel: 8 of the 12 KillControl senders (tm_Hardrock.scr '8 27 200').
    steps.append(near(21, dx=-600))
    for flyer in flyers[:7]:
        steps.append({"damage_actor": {"actor_index": flyer, "amount": 30000}})
    steps += [{"advance_runtime": {"seconds": 1}}, {"assert": {"qbit_clear": [90027]}},
              {"damage_actor": {"actor_index": flyers[7], "amount": 30000}}, {"advance_runtime": {"seconds": 1}},
              {"note": {"text": "the eighth OneDown gives key 27"}}, {"assert": {"qbit_set": [90027]}}]
    # Yrsa again: line 6 "Who are you?" (needs 27, forbids 1) -> 15, line 11 "Very well." -> 2, line 7 -> 3,
    # line 8 -> 4, line 1 -> 5, line 2 -> 6, line 3 (grants 1) -> 7, line 4 "Goodbye" closes: OnRude 366, 367.
    steps.append(near(46))
    steps += talk(yrsa, [5, 10, 6, 7, 0, 1, 2, 3], "Yrsa: destiny (1); OnRudeExit dragonfly 366 and mainline 367")
    steps.append({"assert": {"qbit_set": [90001, 90366, 90367]}})
    # The bunker door is locked without the Turret Key (DoorLock.scr 568).
    steps += [facing(door_x, door_y, door_z), {"press_interact": {}}, {"advance_runtime": {"seconds": 2}},
              {"assert": {"mechanism": {"id": 900498, "state": "closed"}}}]
    # Forad again: line 5 -> 3, line 8 "Yrsa sent us" (needs 1) -> 5, line 3 -> 6, line 16 -> 17, line 11 -> 18,
    # line 12 -> 998, line 13 "Welcome Aboard." (hire: grants 29, 371); closing runs OnRude: Forad leaves (29).
    steps.append(near(61))
    steps += talk(forad, [4, 7, 2, 15, 10, 11, 12], "Forad Darre joins: hire row grants 29 and 371")
    steps += [{"press_action": {"action": "cancel_dialog"}},
              {"assert": {"qbit_set": [90029, 90371]}},
              {"assert": {"actor_visible": {"actor_index": forad, "hidden": True}}}]
    # Yrsa: line 25 "How do we through that door?" (needs 29; grants 469) -> 999, line 10 closes: OnRude Key gives
    # item 568.
    steps.append(near(46))
    steps += talk(yrsa, [24, 9], "Yrsa: the Turret Key (469, item 568)")
    # GiveItem puts the key on the cursor; the party places it in a pack.
    steps += [{"assert": {"qbit_set": [90469], "held_item": {"active": True, "item_id": turret_key}}},
              {"assert": {"held_item": {"active": False, "item_id": turret_key}}},
              {"assert": {"inventory_any_member": [{"item_id": turret_key}]}}]
    # The bunker doors open with the key and keep it (bTakeKey).
    steps += [facing(door_x, door_y, door_z), {"press_interact": {}}, {"advance_runtime": {"seconds": 2.5}},
              {"assert": {"mechanism": {"id": 900498, "state": "open"}}},
              {"assert": {"mechanism": {"id": 900499, "state": "open"}}},
              {"assert": {"inventory_any_member": [{"item_id": turret_key, "count": 0}]}}]
    # The book on the lectern (using the lectern uses the book): the cinema, key 28 and 5200 xp, then Sturmford
    # (ExitTrigger1, 4 days).
    # Headless runs pick decorations through their model triangles, which they do not load: the lectern's event
    # (its click, PropTrigger.scr) runs directly; the click itself is a desktop check.
    steps += [facing(lectern["x"], lectern["y"], lectern["z"] + 90, distance=140),
              {"execute_event": {"id": entities_by_source(496)["event_id_secondary"]}}]
    steps += story_ticks(4.0 / TICK_SECONDS) + [{"assert": {"qbit_clear": [90028]}}]
    steps += story_ticks(1.0 / TICK_SECONDS) + [{"note": {"text": "OnSink (4.5 s): key 28, 5200 xp"}},
                                                {"assert": {"qbit_set": [90028]}}]
    steps += story_ticks(12.0 / TICK_SECONDS) + [{"note": {"text": "FadeOut2 (17 s): ExitTrigger1 to Sturmford"}},
                                                 {"assert": {"map_arrived": {"map": "sturmford.odm"}}}]
    # A later visit: Annud Redeye is at the dock (HideModel 28 unhide) and offers passage (NPC138 line 3, -5).
    steps += [{"load_map": {"map": MAP}},
              {"assert": {"actor_visible": {"actor_index": annud, "hidden": False}}},
              {"assert": {"actor_visible": {"actor_index": yrsa, "hidden": True}}},
              near(747)]
    steps += talk(annud, [2], "Annud Redeye: passage to Sturmford (transport_routes.txt dock 138)")
    # The route of the day: this run arrives on a Wednesday (route day index 4: mm9:transport/138/wednesday).
    steps += [{"select_topic": {"action_id": 4}}, {"assert": {"map_arrived": {"map": "sturmford.odm"}}}]
    document = {"id": "mm9r.isleofashes.story", "world": "mm9", "mode": "faithful", "steps": steps}
    path = PROJECT / "story.yml"
    path.write_text("# The Isle of Ashes story chain on the remade map. Written by make_story_scenario.py.\n"
                    + yaml.safe_dump(document, sort_keys=False))
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
