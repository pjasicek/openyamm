#!/usr/bin/env python3
"""
Write the Lindisfarne Monastery scenarios from the built map (work/doors.json, work/content.json,
work/build_report.json, the scene, props.json):

    scenario_doors_exits.yml   the front door raises ExitTrigger0; a shut nave door stops the party, opens on a real
                               click and is walked through; every door group opens on a click; all seven ladders are
                               climbed from their foot to their top exit
    scenario_scripted.yml      the four letters, an organ key and the ropes by real clicks; the bells in a wrong order
                               (no key) and in MM9's order (key 9507, 2000 experience, the Thjorad monks at prayer);
                               Thjorad taken (item 197, key 162, gone); hurting a monk turns every monk hostile
    scenario_quests.yml        RUDE dialogues by real clicks (a monk, the abbot, Grehgknak, the organ player) and their
                               OnRudeExit events (relic, letter, paladin promotion, the hymn; Robert appears at 5:00)
    scenario_immobile.yml      the immobile NPCs and working monks hold their places for 30 s

    python3 level_generation/projects/mm9r_lindisfarnemonastery/make_scenarios.py
    for s in doors_exits scripted quests immobile; do ./build/game/openyamm \\
        --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario \\
        level_generation/projects/mm9r_lindisfarnemonastery/scenario_$s.yml --scenario-no-color; done
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
from dungeon.source import SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "lindisfarnemonastery.blv"
EYE = 160
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"


def key(raw: int) -> int:
    return 90000 + raw


def item(raw: int) -> int:
    return 10000 + raw


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.lindisfarnemonastery_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def pose(x, y, z, yaw_radians, pitch=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                         "yaw": round(yaw_radians, 4), "pitch": round(pitch, 4)}}


def choose(rude: int, node: int, label: str) -> dict:
    """The dialogue row `label` of a RUDE node (its action id is the row's place in the file)."""
    with open(RUDE / f"NPC{rude}.rude", newline="", encoding="latin-1") as stream:
        rows = list(csv.reader(stream))
    index = next(k for k, row in enumerate(rows) if int(row[1]) == node and row[3] == label)
    return {"select_topic": {"action_id": index, "match_label": label}}


def click(target, distance=150, height=60, avoid=(), floors=None) -> list:
    return [scenarios.look_at(floors, MAP, target, 0, distances=(distance, distance + 50, distance - 50),
                              height=height, avoid=avoid),
            {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]


def floors_source(project, name):
    """A DAT object's LT position (the Thjorad prayer markers)."""
    from dungeon.source import Source
    global _SOURCE
    if "_SOURCE" not in globals():
        _SOURCE = Source(project)
    return _SOURCE.properties(name)["Pos"]


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())} \
        if (PROJECT / "props.json").exists() else {}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = yaml.load((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    scripted = report["scripted"]
    actors_by_name = scripted["actors"]
    actor_pos = {a["actor_index"]: (a["position"]["x"], a["position"]["y"], a["position"]["z"])
                 for a in scene["initial_state"]["actors"]}
    everyone = [p[:2] for p in actor_pos.values()]
    door = {m["node"][5:]: m for m in movers}
    groups = {}
    for m in movers:
        groups.setdefault(m["group"], []).append(m)
    portals = {p["name"]: p for p in report["portals"]}
    exit_object = next(t for t in report["transitions"] if "ExitTrigger0" in json.dumps(t))
    exit_id = exit_object.get("source_object_index", exit_object.get("source_id"))

    # --- doors, exit, ladders -------------------------------------------------------------------------------------
    doc = header("doors_exits", "Lindisfarne Monastery (native BLV) - the front door, the doors by real clicks, a shut "
                                "door stops the party, the seven ladders")
    steps = doc["steps"]
    start = report["starts"][0]["position"]
    steps += [{"note": {"text": "ExitTrigger0: the porch, south of StartPoint0 (to Lindisfarne, LindisfarneExit)."}},
              # through the east arch (LT x -80..80): the centre post stands in the start's line
              scenarios.movement(MAP, (0, start[1], start[2]), 270, 1.2, (0, start[1] - 450, start[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": exit_id}}},
              {"load_map": {"map": MAP}}]
    # NaveDoor1 (the narthex into the nave, naveportal1 at LT z 504): shut it stops a walk, opened it lets through.
    cx, cy, cz = portals["naveportal1"]["centre_native"]
    floor = floors.z(cx, cy - 300, cz)
    ids = [m["door_id"] for m in groups["NaveDoor1"]]
    steps += [{"note": {"text": "NaveDoor1: shut, it stops a walk from the narthex; a click opens both leaves; the "
                                "party walks into the nave."}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
              scenarios.movement(MAP, (cx, cy - 300, floor + 1), 90, 1.0, (cx, cy - 70, floor + 1), 60, 20),
              pose(cx, cy - 200, floor, math.pi / 2, math.atan2(cz - (floor + EYE), 200)),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 3}},
              *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids],
              scenarios.movement(MAP, (cx, cy - 300, floor + 1), 90, 0.8, (cx, cy + 300, floor + 1), 120, 20),
              {"load_map": {"map": MAP}}]
    portal_of = {"NaveDoor2": "naveportal2",   # NaveDoor1: walked above (its state survives load_map)
                 "RotatingDoor0": "naveportal3",
                 "RotatingDoor1": "towerportal1", "RotatingDoor2": "monkportal1", "RotatingDoor3": "towerportal2",
                 "RotatingDoor4": "towerportal4", "RotatingDoor5": "towerportal5"}
    for group, portal in portal_of.items():
        cx, cy, cz = portals[portal]["centre_native"]
        normal = portals[portal].get("normal_native") or portals[portal].get("normal")
        sides = []
        # the UserPortal's thin axis (DAT dims): naveportal1/2 lie across the nave (native y), the others across x
        across = ((0, 1), (0, -1)) if portal in ("naveportal1", "naveportal2") else ((1, 0), (-1, 0))
        for (dx, dy), d in [(s, d) for d in (180, 130, 100) for s in across]:
            x, y = cx + dx * d, cy + dy * d
            z = floors.z(x, y, cz)
            if z is not None and cz - z < portals[portal]["height"] / 2 + 40 and floors.clear((x, y), (cx, cy), z):
                sides.append((x, y, z))
        if not sides:
            raise SystemExit(f"{group}: no floor in front of {portal}")
        x, y, z = sides[0]
        dist = math.dist((x, y), (cx, cy))
        ids = [m["door_id"] for m in groups[group]]
        steps += [{"note": {"text": f"{group} (doors {ids}, {portal}): shut, a click from {int(x)}, {int(y)} opens it."}},
                  *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
                  pose(x, y, z, math.atan2(cy - y, cx - x), math.atan2(cz - (z + EYE), dist)),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 6}},
                  *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids]]
    for ladder in scene["ladders"]:
        yaw = math.radians(ladder["facing_degrees"])
        foot = (ladder["bottom"][0] - math.cos(yaw) * 60, ladder["bottom"][1] - math.sin(yaw) * 60, ladder["bottom"][2])
        fz = floors.z(foot[0], foot[1], foot[2] + 40)
        top = ladder["top_exit"]
        start_pose = {"map": MAP, "x": int(round(foot[0])), "y": int(round(foot[1])), "z": int(round(fz)) + 1,
                      "yaw_degrees": round(ladder["facing_degrees"], 1), "pitch": 0}
        seconds = round((ladder["top"][2] - ladder["bottom"][2]) / 150 + 1.5, 2)
        if (top[0] - ladder["bottom"][0]) * math.cos(yaw) + (top[1] - ladder["bottom"][1]) * math.sin(yaw) < 0:
            # The top exit lies on the climber's side (a shaft climbed out of, Ladder3-5): forward on from it walks
            # straight back into the shaft, so the timed walk below cannot overrun. The climb step stops at the let-go.
            steps += [{"note": {"text": f"{ladder['id']}: climbed from its foot, the party lets go at its top exit "
                                        "(on the climber's side: walking on would fall back down the shaft)."}},
                      {"set_pose": dict(start_pose)},
                      {"climb": {"ladder": ladder["id"], "timeout_seconds": seconds}}]
            continue
        steps += [{"note": {"text": f"{ladder['id']}: forward from its foot climbs to its top exit."}},
                  {"movement_segment": {"input": "forward", "seconds": seconds, "actor_collision": False,
                                        "actor_ai": False, "start": start_pose,
                                        "expect_stop": dict(start_pose, x=int(round(top[0])), y=int(round(top[1])),
                                                            z=int(round(top[2]))),
                                        "loose_tolerance": True, "tolerance_xy": 700, "tolerance_z": 40}}]   # forward goes on walking after the top
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- scripted objects (needs props.json: the letters, Thjorad)
    if props:
        doc = header("scripted", "Lindisfarne Monastery (native BLV) - letters, organ, bells, Thjorad, the monks' alarm")
        steps = doc["steps"]
        for name in convert.EV_LETTER:
            entry = props[name]
            steps += [{"note": {"text": f"{name} (BookLetter.scr \"{convert.LETTER_ID[name]} Letter\"): a click shows it."}},
                      scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                        distances=(90, 120, 150), height=2, max_drop=140, avoid=everyone),
                      {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                      {"assert": {"dialog": {"active": True}}},
                      {"press_action": {"action": "cancel_dialog"}}]
        organ = door["OrganC2"]
        # the organist (CommonerElfMaleA0) sits in front of the keys: C2 (LT x -108) from his right
        ox, oy, oz = -108 * SCALE, 4057 * SCALE, 935 * SCALE
        px, py = -30 * SCALE, 4030 * SCALE
        oz_floor = floors.z(px, py, oz)
        steps += [{"note": {"text": "The organ's C2 key: a click from beside the organist presses it (its note plays) "
                                    "and it rises again."}},
                  pose(px, py, oz_floor, math.atan2(oy - py, ox - px),
                       math.atan2(oz - (oz_floor + EYE), math.dist((px, py), (ox, oy)))),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 0.3}},
                  {"assert": {"mechanism": {"id": organ["door_id"], "state": "open"}}},
                  {"advance_runtime": {"seconds": 3.5}},
                  {"assert": {"mechanism": {"id": organ["door_id"], "state": "closed"}}}]
        rope = door["Rope1"]
        rx, ry = -96 * SCALE, 2322 * SCALE
        rz_floor = floors.z(rx, ry + 120, 1300 * SCALE)
        order = ["Rope1", "Rope5", "Rope2", "Rope4", "Rope3"]          # Bell1..Bell5 (the ropes' OpenTrigger0 targets)
        monks = [actors_by_name[n] for n in convert.THJORAD_MARKERS]
        tx, ty, tz = props["thjorad"]["x"], props["thjorad"]["y"], props["thjorad"]["z"]
        markers = [project.native(floors_source(project, m)) for m in convert.THJORAD_MARKERS.values()]
        stop_done = convert.bell_schedule()[-1][0]        # a bell reports to BellControl this long after its use
        steps += [{"note": {"text": "Rope1 by a real click from the bell floor: it lowers and Bell1 swings and rings; "
                                    "it reports Bell1 when it stops."}},
                  pose(rx, ry + 120, rz_floor, -math.pi / 2, math.atan2(1500 * SCALE - (rz_floor + EYE), 120)),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 1.6}},
                  {"assert": {"mechanism": {"id": rope["door_id"], "state": "open"}}},
                  {"assert": {"state_dump_named_map_var": {"name": "BellBusy1", "value": 3}}},   # past both Ring keys
                  {"note": {"text": "Wrong order: Rope2 (Bell3) after Bell1 resets (Gosub Reset); finishing 4-5 gives nothing."}},
                  {"execute_event": {"id": convert.EV_ROPE["Rope2"]}},
                  {"execute_event": {"id": convert.EV_ROPE["Rope4"]}},
                  {"execute_event": {"id": convert.EV_ROPE["Rope3"]}},
                  {"advance_runtime": {"seconds": stop_done + 0.5}},
                  {"assert": {"state_dump_named_map_var": {"name": "FifthBell", "value": 0}}},
                  {"assert": {"qbit_clear": [key(convert.KEY_BELLS)]}},
                  {"note": {"text": "Thjorad before the bells: its event takes nothing (Thjorad.scr: On is False; its "
                                    "four monks stand round it, so the real click comes after the bells)."}},
                  {"execute_event": {"id": convert.EV_THJORAD}},
                  {"advance_runtime": {"seconds": 0.5}},
                  {"assert": {"qbit_clear": [key(convert.KEY_THJORAD_B)]}},
                  {"note": {"text": "MM9's order Bell1-Bell5 (Rope1, Rope5, Rope2, Rope4, Rope3): key 9507, the peal, the "
                                    "Thjorad monks at their prayer markers."}},
                  *[s for r in order for s in ({"execute_event": {"id": convert.EV_ROPE[r]}},
                                               {"advance_runtime": {"seconds": 1}})],
                  {"advance_runtime": {"seconds": stop_done - 1 + 0.5}},
                  {"assert": {"qbit_set": [key(convert.KEY_BELLS)]}},
                  *[{"assert": {"actor_visible": {"actor_index": a, "near": {
                      "x": int(p[0]), "y": int(p[1]), "max_distance": 40}}}} for a, p in zip(monks, markers)],
                  {"note": {"text": "Thjorad now: a click gives item 197, key 162 and 1000 experience; the hammer is gone."}},
                  # from the west, down the room (its north and south walls are close); the monks have gone to pray
                  pose(tx - 160, ty, floors.z(tx - 160, ty, tz), 0.0, math.atan2(tz + 20 - (floors.z(tx - 160, ty, tz)
                                                                                      + EYE), 160)),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                  {"advance_runtime": {"seconds": 0.5}},
                  {"assert": {"qbit_set": [key(convert.KEY_THJORAD_B)]}},
                  {"assert": {"inventory_any_member": [{"item_id": item(convert.ITEM_THJORAD), "count": 1}]}}]
        hoe = actors_by_name["Initiate0"]
        other = actors_by_name["Initiate10"]
        steps += [{"load_map": {"map": MAP}},
                  {"note": {"text": "The monks' alarm (MonkHostility.inc): friendly until the party hurts one; then every "
                                    "monk is hostile."}},
                  {"assert": {"actor_visible": {"actor_index": hoe, "hostile_to_party": False}}},
                  {"assert": {"actor_visible": {"actor_index": other, "hostile_to_party": False}}},
                  {"damage_actor": {"actor_index": hoe, "amount": 5}},   # the party's melee damage path (party_attack: 10 misses)
                  {"advance_runtime": {"seconds": 1}},
                  {"assert": {"actor_visible": {"actor_index": other, "hostile_to_party": True}}}]
        scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- quests (RUDE) ----------------------------------------------------------------------------------------------
    def talk(name, rude):
        a = actors_by_name[name]
        x, y, z = actor_pos[a]
        avoid = [p for p in everyone if p != (x, y)]
        return click((x, y, z), 150, 60, avoid=avoid, floors=floors) + [
            {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
            {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    doc = header("quests", "Lindisfarne Monastery (native BLV) - RUDE dialogues by real clicks and their OnRudeExit events")
    steps = doc["steps"]
    steps += [{"note": {"text": "A hoeing monk (Initiate0, MonkGuardBasic.scr '1 296'): a click opens dialogue 296."}},
              *talk("Initiate0", 296), {"press_action": {"action": "cancel_dialog"}},
              {"note": {"text": "Abbot Leffery (NPC283.scr): with the relic found (key 341) and item 368, closing the talk "
                                "takes the relic, gives 3000 gold, 80000 experience and key 342."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_RELIC_FOUND), "value": True}},
              {"grant_item": {"item_id": item(convert.ITEM_RELIC), "count": 1}},
              *talk("Abbot Leffery", 283), {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_RELIC_DONE)]}},
              {"note": {"text": "Grehgknak (NPC282.scr :giveletter): key 228 without 229 gives key 229 and item 419."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_LETTER_ASKED), "value": True}},
              *talk("Grehgknak", 282), {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_LETTER_GIVEN)]}},
              {"assert": {"inventory_any_member": [{"item_id": item(convert.ITEM_LETTER), "count": 1}]}},
              {"note": {"text": "Grehgknak (:paladins): key 236 without 237 gives key 237 (and promotes holders of 421-424)."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_PALADIN_ASKED), "value": True}},
              *talk("Grehgknak", 282), {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_PALADIN_DONE)]}},
              {"note": {"text": "The organ player (NPC420.scr): key 9506 from his talk; closing plays the hymn and takes it."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_HYMN), "value": True}},
              *talk("CommonerElfMaleA0", 420), {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_clear": [key(convert.KEY_HYMN)]}},
              {"note": {"text": "Robert Aefgil (NPC284.scr) is hidden; after the abbot agrees (key 253) the next 5:00 "
                                "gives key 254 and he appears."}},
              {"assert": {"actor_visible": {"actor_index": actors_by_name[scripted["robert"]], "hidden": True}}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_PRIEST_ASKED), "value": True}},
              {"advance_runtime": {"seconds": 4}},
              {"console": {"line": "time advance 1440"}},
              {"advance_runtime": {"seconds": 4}},
              {"assert": {"qbit_set": [key(convert.KEY_PRIEST_READY)]}},
              {"assert": {"actor_visible": {"actor_index": actors_by_name[scripted["robert"]], "hidden": False}}}]
    scenarios.write(PROJECT / "scenario_quests.yml", doc, "make_scenarios.py")

    doc = {"id": "mm9r.lindisfarnemonastery_immobile", "title": "Lindisfarne Monastery (native BLV) - immobile actors hold "
           "position", "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"],
           "steps": [{"load_map": {"map": MAP}}, {"advance_runtime": {"seconds": 30}}]}
    doc["steps"] += [{"assert": {"actor_visible": {"actor_index": a["actor_index"], "near": {
        "x": a["position"]["x"], "y": a["position"]["y"], "max_distance": 8}}}}
        for a in scene["initial_state"]["actors"] if a.get("immobile")
        and a["actor_index"] != actors_by_name[scripted["robert"]]]
    scenarios.write(PROJECT / "scenario_immobile.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
