#!/usr/bin/env python3
"""
Write the Ta'Sar Academy scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json, work/runtime):

    scenario_doors_exits.yml   the exit to Lindisfarne raises its MM9 exit trigger; a shut double door stops the party,
                               opens on a click and is walked through; the library's secret door stays locked; a wall
                               switch opens its secret door; a book button swings the bookcase; the cracked wall
                               breaks on a click; Ladder0 climbs to the library tower's first floor
    scenario_chests.yml        the four chests open from in front of their models (interact)
    scenario_scripted.yml      the trap doors and the spikes, the sparring, the crate's Dagrell, the chalices, the
                               letters, the skill books, the library puzzle (real clicks on books and tables, in order)
                               and the Book of Rules (Ludwig's quest key)

    python3 level_generation/projects/mm9r_tasaracademy/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_tasaracademy/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import ROOT, SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "tasaracademy.blv"
EXIT_OBJECT = 319                   # ExitTrigger0 (DAT object index; map_transitions.txt row of this map)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.tasaracademy_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = ({e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
             if (PROJECT / "props.json").exists() else {})
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    start = report["starts"][0]["position"]
    boxes = report["scripted"]["boxes"]
    actors = report["scripted"]["actors"]
    group_doors = {}
    for m in movers:
        group_doors.setdefault(m["group"], []).append(m["door_id"])
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime" / MAP)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    faces = {f["index"]: f for f in blv["faces"]}
    door_faces = {d["door_id"]: d["face_ids"] for d in scene["initial_state"]["doors"]}
    decorations = {d["anchor"]: d for d in content["decorations"]}
    monsters = [(a["position"]["x"], a["position"]["y"]) for a in scene["initial_state"]["actors"]]

    def centre(group):
        points = np.concatenate([vertices[faces[f]["vertex_indices"]] for d in group_doors[group]
                                 for f in door_faces[d]])
        return (points.min(0) + points.max(0)) / 2

    def state(name, value):
        return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}

    def mech(group, value, k=0):
        return {"assert": {"mechanism": {"id": group_doors[group][k], "state": value}}}

    def face_point(target, stand, height=0.0, z_from=None):
        """A pose at `stand` (native x, y; its floor) looking at `target` (native x, y, z)."""
        x, y = stand
        z = floors.z(x, y, target[2] + 120 if z_from is None else z_from)
        if z is None:
            raise SystemExit(f"no floor at {stand}")
        look = math.atan2(target[1] - y, target[0] - x)
        pitch = math.atan2(target[2] + height - (z + scenarios.EYE), math.dist((x, y), target[:2]))
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}

    def click_door(group, side, distance=130, height=0.0, z_from=None):
        """A real click on a door group's leaves from `side` (native unit vector)."""
        c = centre(group)
        stand = (c[0] + side[0] * distance, c[1] + side[1] * distance)
        return [face_point(c, stand, height, z_from), {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]

    def click_decoration(anchor, distances=(90, 120, 160), height=25, max_drop=120):
        d = decorations[anchor]
        x, y, z = d["position"]
        yaw = props[anchor]["yaw_degrees"] if anchor in props else 0
        return [scenarios.look_at(floors, MAP, (x, y, z), yaw, distances=distances, height=height, max_drop=max_drop,
                                  avoid=monsters),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]

    def pose(x, y, z, yaw=0.0):
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)), "yaw": yaw,
                             "pitch": 0}}

    def in_box(name, dx=0.0, dy=0.0, z=None):
        low, high = boxes[name]
        x, y = (low[0] + high[0]) / 2 + dx, (low[1] + high[1]) / 2 + dy
        if z is not None:
            return pose(x, y, z)
        z = floors.z(x, y, high[2] + 60)
        return pose(x, y, (z if z is not None else low[2]) + 1)

    def lt(x, y, z):
        return project.native([x, y, z])

    def walk(stand, yaw, seconds, stop, xy=90, z_tol=40, z_from=400):
        x, y = stand
        z = floors.z(x, y, z_from)
        sx, sy = stop
        return scenarios.movement(MAP, (x, y, z + 1), yaw, seconds, (sx, sy, z + 1), xy, z_tol)

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Ta'Sar Academy (native BLV) - the exit, doors, secret doors, bookcase, crack, ladder")
    steps = doc["steps"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 319): the front door to Lindisfarne, just north of the start."}},
              scenarios.movement(MAP, start, 90, 1.0, (start[0], start[1] + 400, start[2]), 500, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    # Door0/Door1 (Door_0_1_portal at LT z -1680): from the east corridor south into the dormitory.
    c = centre("D0_1")
    north = (c[0], c[1] + 300)
    steps += [{"note": {"text": "Door0/Door1 (linear double door) is shut and stops the party walking south into it."}},
              mech("D0_1", "closed"),
              walk(north, 270, 1.0, (c[0], c[1] + 60), 90),
              {"note": {"text": "A click on the leaves opens the pair; the party walks through into the dormitory."}},
              *click_door("D0_1", (0, 1)),
              {"advance_runtime": {"seconds": 2.5}},
              mech("D0_1", "open"), mech("D0_1", "open", 1),
              walk(north, 270, 1.0, (c[0], c[1] - 300), 200)]
    # The library's secret door: locked until the puzzle.
    steps += [{"note": {"text": "LibraryDoor (Locked; only the library puzzle opens it) stays shut on a click."}},
              *click_door("LibraryDoor", (0, 1), distance=120, height=60, z_from=500 * SCALE),
              {"advance_runtime": {"seconds": 2}},
              mech("LibraryDoor", "closed")]
    # Switch1 opens SecretDoor0 (the store room); it shuts after 7 s.
    sw = centre("Switch1")
    steps += [{"note": {"text": "Switch1 (a wall switch in the east corridor): a click opens SecretDoor0."}},
              mech("SecretDoor0", "closed"),
              face_point(sw, (sw[0] - 110, sw[1])),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"advance_runtime": {"seconds": 3}},
              mech("SecretDoor0", "open"),
              state("FoundPerceptionBrush0", 1)]
    # The bookcase: the front book button swings it.
    button = centre("BookButtonFront1")
    steps += [{"note": {"text": "BookButtonFront1 (a book on the rotating bookcase, south hall side): a click presses it "
                                "and swings the bookcase open."}},
              mech("RotatingBookcase1", "closed"),
              # the two hostile Guards whose patrol path starts by the bookcase come for the party into its swing,
              # which holds for a body in it (bodies: hold): they are cleared first
              *scenarios.clear_monsters(scene["initial_state"]["actors"], tuple(button), radius=1200),
              face_point(button, (button[0] + 260, button[1])),     # outside the bookcase's swing
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"advance_runtime": {"seconds": 7}},
              state("BookcaseTurns", 1),
              mech("RotatingBookcase1", "open")]
    # The cracked wall between the library and the pit's tunnel.
    walls = {d["name"]: d for d in scene["destructibles"]}
    wall, inner = walls["door crack"], walls["door crack 2"]
    cog_points = np.concatenate([vertices[f["vertex_indices"]] for f in blv["faces"]
                                 if f["face_param"].get("cog_number") in (wall["cog"], inner["cog"])])
    crack = (cog_points.min(0) + cog_points.max(0)) / 2
    steps += [{"note": {"text": f"The cracked wall (\"door crack\", a scene destructible of {wall['hp']} hit points; "
                                "its damage breaks \"door crack 2\", TriggerDestroyOnly): one short of its hit points "
                                "it stands; a click from the library breaks it (the shared click's killing blow) and "
                                "the party walks through."}},
              {"console": {"line": f"destructible {wall['id']} damage {wall['hp'] - 1}", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 0.5}},
              state("CrackBroken", 0),
              face_point(crack, (crack[0] + 150, crack[1])),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"advance_runtime": {"seconds": 2}},
              state("CrackBroken", 1),
              walk((crack[0] + 150, crack[1]), 180, 1.2, (crack[0] - 120, crack[1]), 150, 40, z_from=100)]
    # Ladder0: from the library floor up through the tower's first floor. Both ladders step off backwards (the exit on
    # the climber's side): the climb and the glide onto the exit (since 2026-11-10) end at 2.8 s; held on, forward walks
    # back to the hole (2.5-3.0 s pass).
    secs = 2.8
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder0")
    foot = [int(round(ladder["bottom"][0])), int(round(ladder["bottom"][1] - 60)), int(round(ladder["bottom"][2]))]
    top = [int(round(v)) for v in ladder["top_exit"]]
    climb_pose = {"map": MAP, "x": foot[0], "y": foot[1], "z": foot[2] + 1, "yaw_degrees": 90, "pitch": 0}
    steps += [{"note": {"text": "Ladder0: forward from its foot climbs to the tower's floor at 208 LT."}},
              {"movement_segment": {"input": "forward", "seconds": secs, "actor_collision": False, "actor_ai": False,
                                    "start": climb_pose, "expect_stop": dict(climb_pose, x=top[0], y=top[1], z=top[2]),
                                    "loose_tolerance": True, "tolerance_xy": 160, "tolerance_z": 60}}]
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder1")
    foot = [int(round(ladder["bottom"][0])), int(round(ladder["bottom"][1] + 60)), int(round(ladder["bottom"][2]))]
    top = [int(round(v)) for v in ladder["top_exit"]]
    climb_pose = {"map": MAP, "x": foot[0], "y": foot[1], "z": foot[2] + 1, "yaw_degrees": 270, "pitch": 0}
    steps += [{"note": {"text": "Ladder1: forward from its foot on the 208 floor climbs to the bridge's floor at 416 LT."}},
              {"movement_segment": {"input": "forward", "seconds": secs, "actor_collision": False, "actor_ai": False,
                                    "start": climb_pose, "expect_stop": dict(climb_pose, x=top[0], y=top[1], z=top[2]),
                                    "loose_tolerance": True, "tolerance_xy": 160, "tolerance_z": 60}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    if not props:
        print("note: props.json is missing: only scenario_doors_exits.yml written")
        return 0

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Ta'Sar Academy (native BLV) - the four MM9 treasure chests open")
    doc["steps"] += [{"note": {"text": "The chests stand behind the two secret doors: both are opened first."}},
                     {"execute_event": {"id": convert.EV_SWITCH}}, {"execute_event": {"id": convert.EV_SWITCH1}},
                     {"advance_runtime": {"seconds": 3}}]
    for chest in content["chests"]:
        entry = props[chest["anchor"]]
        doc["steps"] += [scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                           distances=(110, 150, 190), avoid=monsters),
                         {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                         {"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                         {"press_action": {"action": "cancel_dialog"}}]
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Ta'Sar Academy (native BLV) - trap, sparring, crate, chalices, letters, library puzzle")
    steps = doc["steps"]
    pit = centre("PitDoor")
    steps += [{"note": {"text": "The PerceptionBrushes show at Perception 10 and not below (checked every 3 s)."}},
              {"console": {"line": "skill set Perception 1 B"}},
              {"advance_runtime": {"seconds": 4}},
              state("PerceptionHints", 1),
              {"console": {"line": "skill set Perception 10 E"}},
              {"advance_runtime": {"seconds": 4}},
              state("PerceptionHints", 2)]
    steps += [{"note": {"text": "PitDoorTrigger1: stepping on the trap doors in front of the podium opens them; the "
                                "party falls onto the spikes (40)."}},
              mech("PitDoor", "closed"),
              in_box("PitDoorTrigger1", dy=400),
              {"advance_runtime": {"seconds": 0.5}},
              in_box("PitDoorTrigger1", z=2),             # on the trap doors (a mover: not in the static floors)
              {"advance_runtime": {"seconds": 3}},
              state("PitTrips", 1),
              state("SpikeHits", 1)]
    steps += [{"note": {"text": "Trigger0 (the arena's north-east mouth): the sparring starts (TaSarTeacher.scr)."}},
              in_box("Trigger0", dx=300),
              {"advance_runtime": {"seconds": 0.5}},
              in_box("Trigger0"),
              {"advance_runtime": {"seconds": 0.5}},
              state("Sparring", 1)]
    steps += [{"note": {"text": "Trigger4 in the store room smashes the crate; its Dagrell appears (hostile)."}},
              {"execute_event": {"id": convert.EV_SWITCH1}},
              {"advance_runtime": {"seconds": 2}},
              in_box("Trigger4", dx=-200),
              {"advance_runtime": {"seconds": 0.5}},
              in_box("Trigger4"),
              {"advance_runtime": {"seconds": 0.5}},
              state("CrateBroken", 1)]
    steps += [{"note": {"text": "The right chalice (Prop151) gives key 9500; another does nothing."}},
              *click_decoration("Prop148", distances=(80, 100, 130), height=5),
              {"assert": {"qbit_clear": [90000 + convert.KEY_CHALICE]}},
              *click_decoration("Prop151", distances=(80, 100, 130), height=5),
              {"assert": {"qbit_set": [90000 + convert.KEY_CHALICE]}},
              state("Chalice0", 1)]
    steps += [{"note": {"text": "The skill book Prop5 (\"Blade\"), a world item, picked up: item 285."}},
              *scenarios.pick_up_steps(floors, MAP, scene, "Prop5", distances=(80, 100, 130), avoid=monsters),
              {"assert": {"inventory_any_member": [{"item_id": 10285, "count": 1}]}}]
    # The library puzzle, in order: take 435 from the Start table, put it on Offense, then 436 to Strategy, 437 to
    # Defense, 438 to Intelligence. First a wrong move: 436 cannot be taken before 435 is placed.
    steps += [{"note": {"text": "Textbook 436 cannot be taken from the Start table before 435 stands on Offense."}},
              *click_decoration("Start436", distances=(70, 90, 110), height=3),
              state("AtStart436", 1)]
    for location, item, table in (("Offense", 435, "Prop164"), ("Strategy", 436, "Prop166"),
                                  ("Defense", 437, "Prop163"), ("Intelligence", 438, "Prop165")):
        steps += [{"note": {"text": f"Take textbook {item} from the Start table, put it on the {location} table."}},
                  *click_decoration(f"Start{item}", distances=(70, 90, 110), height=3),
                  state(f"AtStart{item}", 0),
                  {"assert": {"inventory_any_member": [{"item_id": 10000 + item, "count": 1}]}},
                  *click_decoration(table, distances=(90, 120, 150), height=30, max_drop=30),
                  state(f"At{location}{item}", 1),
                  {"assert": {"qbit_set": [90000 + convert.TABLE_KEY[location]]}}]
    steps += [{"note": {"text": "All four in place: key 9516, the library's secret door opens."}},
              {"assert": {"qbit_set": [90000 + convert.KEY_LIBRARY_DONE]}},
              {"advance_runtime": {"seconds": 4}},
              mech("LibraryDoor", "open")]
    steps += [{"note": {"text": "The letter behind the door (Prop179, 440) and the Start table's scroll read."}},
              *click_decoration("Prop96", distances=(70, 90, 110), height=3),
              {"press_action": {"action": "cancel_dialog"}}]
    steps += [{"note": {"text": "The Book of Rules on Ludwig's errand (key 57): a world item: item 391 and key 59."}},
              {"console": {"line": f"qbit set {90000 + convert.KEY_LUDWIG}"}},
              {"execute_event": {"id": convert.EV_BOOK_BUTTON}},
              {"advance_runtime": {"seconds": 6}},
              *scenarios.pick_up_steps(floors, MAP, scene, "BookRules", distances=(80, 100, 130), avoid=monsters),
              {"assert": {"qbit_set": [90000 + convert.KEY_RULES_QUEST]}},
              {"assert": {"qbit_clear": [90000 + convert.KEY_RULES_FREE]}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_RULES, "count": 1}]}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
