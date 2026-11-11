#!/usr/bin/env python3
"""
Write the Klusos House scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json):

    scenario_doors_exits.yml   every door group opens on a real click (interact from in front of it); a shut door
                               stops the party and, opened, lets it through; both MM9 exit triggers (the front door,
                               the west window) raise their transitions
    scenario_chests.yml        the chest opens from in front of its model (interact)
    scenario_scripted.yml      the letter (BookLetter.scr) and the Blackheart (Blackheart.scr) by real clicks: the
                               item and key, the hidden guards appear, the sleepers wake

    python3 level_generation/projects/mm9r_klusoshouse/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_klusoshouse/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "klusoshouse.blv"
EXITS = {52: "ExitTrigger1, the front door", 53: "ExitTrigger0, the west window"}
BLACKHEART_ITEM = 10029             # MM9.ItemIds[29] (state/item_script_reference_report.yml: BLACKHEART.scr giveitem 29)
EYE = 160
WATCH = 320                         # the party's distance from the watched sleeper


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.klusoshouse_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def pose(x, y, z, yaw_radians, pitch=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                         "yaw": round(yaw_radians, 4), "pitch": round(pitch, 4)}}


def door_sides(floors, centre, distance):
    """Poses on both sides of a doorway (native centre at mid height): (x, y, floor z, yaw toward the door)."""
    cx, cy, cz = centre
    floor = cz - 112                     # the doorways are 225 high: centre 112 over the floor
    out = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = cx + dx * distance, cy + dy * distance
        z = floors.z(x, y, floor + 60)
        if z is not None and abs(z - floor) < 40:
            out.append((x, y, z, math.atan2(cy - y, cx - x)))
    return out


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scripted = report["scripted"]
    portals = {p["name"]: p for p in report["portals"]}
    groups = {}
    for m in movers:
        groups.setdefault(m["group"], []).append(m)
    portal_of = {"RDoor9": "doorportal10", "RDoor10": "doorportal4", "RDoor11": "doorportal11", "RDoor12": "doorportal6",
                 "RDoor13": "doorportal9", "RDoor14": "doorportal8", "RDoor15": "doorportal7", "RDoor16": "doorportal5",
                 "RotatingDoor7": "DDPortal0", "RotatingDoor0": "doorportal1", "RotatingDoor3": "doorportal2",
                 "RDoor4": "RDoor4"}
    centres = {g: portals[p]["centre_native"] for g, p in portal_of.items()}
    centres["RDoor2"] = [int(round(-8 * SCALE)), int(round(904 * SCALE)), int(round(44 * SCALE))]   # its leaves' middle

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Klusos House (native BLV) - every door by a click, a shut door stops the party, both exits")
    steps = doc["steps"]
    starts = report["starts"]
    front, window = starts[0]["position"], starts[1]["position"]
    steps += [{"note": {"text": "ExitTrigger1 (DAT object 52): the front door, east of StartPoint0."}},
              scenarios.movement(MAP, front, 0, 0.6, (front[0] + 180, front[1], front[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": 52}}},
              {"load_map": {"map": MAP}},
              {"note": {"text": "ExitTrigger0 (DAT object 53): the west window, beside WindowStartPoint."}},
              scenarios.movement(MAP, window, 180, 0.6, (window[0] - 200, window[1], window[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": 53}}},
              {"load_map": {"map": MAP}}]
    # A shut door stops the party; opened, the party walks through (the dining room's door from the hall).
    group = "RotatingDoor0"
    sides = door_sides(floors, centres[group], 260)
    x, y, z, yaw = sides[0]
    cx, cy, _ = centres[group]
    beyond = (cx + (cx - x) * 0.9, cy + (cy - y) * 0.9)
    stop = (cx + (x - cx) * 70 / 260, cy + (y - cy) * 70 / 260)
    ids = [m["door_id"] for m in groups[group]]
    steps += [{"note": {"text": f"{group}: the shut door stops a walk from {int(x)}, {int(y)}; opened by a click, the "
                                f"party walks through into the dining room."}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
              scenarios.movement(MAP, (x, y, z + 1), math.degrees(yaw), 0.8,
                                 (stop[0], stop[1], floors.z(stop[0], stop[1], z + 80) + 1), 50, 20),
              pose(x, y, z, yaw, math.atan2(centres[group][2] - (z + EYE), 260)),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 2.5}},
              *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids],
              scenarios.movement(MAP, (x, y, z + 1), math.degrees(yaw), 0.6,
                                 (beyond[0], beyond[1], floors.z(beyond[0], beyond[1], z + 80) + 1), 90, 20),
              {"advance_runtime": {"seconds": 12}},     # MM9 CloseWaitTime 10 s: shut again
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids]]
    # Count Kluso (no script, MM9's plain monster AI) comes for the party and opens RDoor4 on his way (AITriggerable,
    # BaseDoor.inc): the house is cleared first, so each door is found shut and opened by its own click.
    scene_actors = json.loads((PROJECT / "work/runtime/klusoshouse.scene.yml").read_text())["initial_state"]["actors"]
    steps += scenarios.clear_monsters(scene_actors, (0, 0, 0), radius=1e9, height=1e9)
    for group, members in sorted(groups.items()):
        sides = door_sides(floors, centres[group], 170)
        if not sides:
            raise SystemExit(f"{group}: no floor beside its doorway")
        x, y, z, yaw = sides[0]
        pitch = math.atan2(centres[group][2] - (z + EYE), 170)
        ids = [m["door_id"] for m in members]
        steps += [{"note": {"text": f"{group} (doors {ids}): shut, a click from {int(x)}, {int(y)} opens both leaves."}},
                  *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
                  pose(x, y, z, yaw, pitch), {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                  {"advance_runtime": {"seconds": 2.5}},
                  *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids]]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Klusos House (native BLV) - the MM9 treasure chest opens from in front of it")
    doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Klusos House (native BLV) - the kitchen letter, the Blackheart and the guards it wakes")
    steps = doc["steps"]
    hidden, sleepers = scripted["hidden"], scripted["sleepers"]
    scene = json.loads((PROJECT / "work/runtime/klusoshouse.scene.yml").read_text())
    sleeper_at = {i: (scene["initial_state"]["actors"][i]["position"]["x"], scene["initial_state"]["actors"][i]["position"]["y"])
                  for i in sleepers}
    watched = scripted["actors"]["UpperSleep1"]
    wx, wy = sleeper_at[watched]
    wz = floors.z(wx, wy + WATCH, 520)
    watch_pose = pose(wx, wy + WATCH, wz, -math.pi / 2, 0.0)
    letter = props["Prop46"]
    # the Blackheart is a world item (dungeon/pickups.py): aim at the item where it lies
    scene = json.loads((PROJECT / "work/runtime/klusoshouse.scene.yml").read_text())
    heart = {k: v for k, v in scenarios.world_item(scene, "Blackheart")["position"].items()}
    steps += [{"note": {"text": "Before: the seven KlusosHidden guards are hidden, the eight sleepers lie dormant."}},
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": True}}} for i in hidden],
              {"note": {"text": f"Sleeper {watched} (UpperSleep1) in plain view {WATCH} units up the corridor: it sleeps on."}},
              watch_pose,
              {"advance_runtime": {"seconds": 4}},
              {"assert": {"actor_visible": {"actor_index": watched, "hidden": False, "report_state": True,
                                            "combat_targeting_party": False,
                                            "near": {"x": sleeper_at[watched][0], "y": sleeper_at[watched][1],
                                                     "max_distance": 8}}}},
              {"load_map": {"map": MAP}},
              {"note": {"text": "Prop46, the letter on the kitchen table (BookLetter.scr DoLetter 456): a click shows it."}},
              scenarios.look_at(floors, MAP, (letter["x"], letter["y"], letter["z"]), letter["yaw_degrees"],
                                distances=(90, 120), height=2, max_drop=140),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"assert": {"dialog": {"active": True}}},
              {"press_action": {"action": "cancel_dialog"}},
              {"note": {"text": "The Blackheart (Blackheart.scr :OnUse), a world item, picked up: item 29; key 223, the "
                                "alarm; the hidden guards appear and the sleepers wake (OnObjectLinkBroken)."}},
              # from the room in front of the fireplace (north of it), not from the mantel's own top
              pose(heart["x"], heart["y"] + 150, floors.z(heart["x"], heart["y"] + 150, heart["z"]), -math.pi / 2,
                   math.atan2(heart["z"] + 3 - (floors.z(heart["x"], heart["y"] + 150, heart["z"]) + EYE), 150)),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"qbit_set": [90000 + convert.KEY_BLACKHEART]}},
              {"assert": {"inventory_any_member": [{"item_id": BLACKHEART_ITEM, "count": 1}]}},
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": False}}} for i in hidden],
              {"advance_runtime": {"seconds": 1}},
              *[{"assert": {"actor_visible": {"actor_index": i, "report_state": True}}} for i in hidden],
              {"note": {"text": f"Awake now: sleeper {watched} sees the party from the same spot and comes for it."}},
              watch_pose,
              {"advance_runtime": {"seconds": 2}},
              # it has the party and has left its bed (its combat target drops for a moment between route steps)
              {"assert": {"actor_visible": {"actor_index": watched, "report_state": True, "has_detected_party": True,
                                            "far": {"x": wx, "y": wy, "min_distance": 100}}}},
              {"note": {"text": "Its pickup event again gives nothing more."}},
              {"execute_event": {"id": convert.EV_BLACKHEART}},
              {"assert": {"inventory_any_member": [{"item_id": BLACKHEART_ITEM, "count": 1}]}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
