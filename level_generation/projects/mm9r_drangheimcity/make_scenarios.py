#!/usr/bin/env python3
"""
Write the Drangheim City scenarios from the built map (work/doors.json, work/content.json, work/build_report.json):

    scenario_doors_exits.yml   the inn's double door stops the party, opens on its click and the party walks in;
                               Klusos House's locked front door stays shut on its click; the west gate's exit raises
                               its transition to the Drangheim wilderness, the exit volume in front of Klusos House's
                               door its transition into the house, and the window at the end of the north wall's
                               walkway its transition to Klusos House's window room
    scenario_shops.yml         walk-in shops by real clicks: the armourer Fintan A'Dlinn (RUDE 97) and the spell shop's
                               Daonai A'Norta a'meich (RUDE 99) open their dialogues and their service rows open the
                               shops; the innkeeper Thorkatla the Indiscreet (RUDE 101) by a click too
    scenario_chests.yml        Drangheim City has no treasure chest (no TreasureChest or TreasureBag in the DAT): not
                               written
    scenario_scripted.yml      the location key 1027, the shop hours (5017), Sigmund's reward on closing his dialogue,
                               a letter, the town portal altar (5013), Atli's Assassin promotion, Guaire A'Velsi shown by
                               Atli's task and his death (225), Hrolf's key 5010 on first sight
    scenario_thorolf.yml       NPC378.scr: nobody comes with key 106 alone or 83 with 84; with 83 Thorolf runs up
                               to the party he sees and opens RUDE 378 with no click, the other copy removed

    python3 level_generation/projects/mm9r_drangheimcity/make_scenarios.py
    for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_drangheimcity/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios, town_portal  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import citylua  # noqa: E402

MAP = "drangheimcity.blv"
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
# Ladders the party also takes at the top (`grab_at_top`): TowerLadder1, the leaning ladder through the slot in the
# north wall's walkway, the only way down for a party arriving by Klusos House's window.
LADDER_HOLD = 37 + 4                 # the party's radius and the ladder's hold gap: how far in front of the strip it climbs
LADDER_CLIMB_SPEED = 192
# The walkway from Klusos House's window arrival (start 0) to TowerLadder1's top exit, in straight legs (native x, y): the
# window's landing, north along the wall, round the corner and east to the slot. The headless walk overshoots short
# legs, so a leg asserts only that the party stays on the walkway (its height); the last one ends at the top exit.
WINDOW_TO_LADDER = [(15340, -10281), (15662, -10250), (15662, -8300), (16175, -7900), (16550, -7850), (16950, -8025),
                    (17200, -8137)]
WALKWAY_Z = 2356
EXIT_WEST, EXIT_KLUSOS_WINDOW, EXIT_KLUSOS_DOOR = 81, 62, 64      # DAT object indices of ExitTrigger0, 1, 2


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.drangheimcity_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def key(raw: int) -> int:
    return 90000 + raw


def choose(rude: int, node: int, label: str) -> dict:
    with open(RUDE / f"NPC{rude}.rude", newline="", encoding="latin-1") as stream:
        rows = list(csv.reader(stream))
    index = next(k for k, row in enumerate(rows) if int(row[1]) == node and row[3].startswith(label))
    return {"select_topic": {"action_id": index, "match_label": rows[index][3]}}


def native(x, z) -> tuple[float, float]:
    return x * SCALE, z * SCALE


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    door = {m["node"][5:]: m for m in movers}
    starts = {s["name"]: s["position"] for s in report["starts"]}
    scripted = report["scripted"]
    actors = {name: tuple(scene["initial_state"]["actors"][index]["position"][k] for k in "xyz")
              for name, index in scripted["actors"].items()}
    everyone = [(p[0], p[1]) for p in actors.values()]
    events = citylua.prop_events(None)
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}

    def talk_click(name: str, rude: int) -> list:
        """A real click on an actor whose click runs a map handler first (it then opens the dialogue)."""
        x, y, z = actors[name]
        return [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(140, 190), height=60,
                                  avoid=[a for a in everyone if a != (x, y)]),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 0.3}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    def talk(name: str, rude: int) -> list:
        x, y, z = actors[name]
        return [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(140, 190), height=60,
                                  avoid=[a for a in everyone if a != (x, y)]),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Drangheim City (native BLV) - the inn's double door, Klusos House's locked door, the "
                                "exits to the wilderness and into Klusos House")
    steps = doc["steps"]
    inn = door["InnDoorLeft"]
    # InnDoorLeft/Right at LT x 6580-6588, z -1480..-1352 (the inn's east wall): walk west from the street into the inn.
    sx, sy = native(6584, -1416)
    z = floors.z(sx + 300, sy, 1000)
    zd = floors.z(sx + 40, sy, z + 150)           # the inn's porch steps up to the threshold
    zi = floors.z(sx - 300, sy, z + 150)
    steps += [{"note": {"text": f"InnDoorLeft/Right (doors {inn['door_id']}, event {inn['event']}): shut, stops the "
                                "party, opens on its click; the party walks into the inn."}},
              {"assert": {"mechanism": {"id": inn["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (sx + 300, sy, z + 1), 180, 0.8, (sx + 40, sy, zd + 1), 60, 40),
              {"execute_event": {"id": inn["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": inn["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (sx + 300, sy, z + 1), 180, 0.8, (sx - 300, sy, zi + 1), 140, 40)]
    klusos = door["AlchemistDoorLeft"]
    steps += [{"note": {"text": "AlchemistDoorLeft/Right (Klusos House's front door, Locked, no key): a click says it "
                                "is locked; it stays shut."}},
              {"execute_event": {"id": citylua.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": klusos["door_id"], "state": "closed"}}}]
    gate = starts["StartPoint0"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 81): from the west gate's arrival west into the exit volume "
                                "to the Drangheim wilderness."}},
              scenarios.movement(MAP, (gate[0], gate[1], gate[2]), 180, 1.2, (gate[0] - 700, gate[1], gate[2]), 700,
                                 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_WEST}}},
              {"load_map": {"map": MAP}}]
    front = starts["KlusoDoorExit"]
    steps += [{"note": {"text": "ExitTrigger2 (DAT object 64): from Klusos House's door arrival south into the exit "
                                "volume in front of the locked door (MM9's way into the house)."}},
              scenarios.movement(MAP, (front[0], front[1], front[2]), 270, 0.8,
                                 (front[0], front[1] - 150, front[2]), 160, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger",
                                                      "source_id": EXIT_KLUSOS_DOOR}}},
              {"load_map": {"map": MAP}}]
    window = starts["KlusoWindowExit"]
    wx, wy = native(5900, -3960)
    yaw = math.degrees(math.atan2(wy - window[1], wx - window[0])) % 360
    steps += [{"note": {"text": "ExitTrigger1 (DAT object 62): from the window arrival on the north wall's walkway back "
                                "into the window to Klusos House."}},
              scenarios.movement(MAP, (window[0], window[1], window[2]), yaw, 0.8, (wx, wy, window[2]), 300, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger",
                                                      "source_id": EXIT_KLUSOS_WINDOW}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- shops ------------------------------------------------------------------------------------------------------
    doc = header("shops", "Drangheim City (native BLV) - walk-in shops: the shopkeepers' dialogues open by real "
                          "clicks and their service rows open the shops")
    steps = doc["steps"]
    steps += [{"advance_runtime": {"seconds": 1.5}}]
    for name, rude, label in (("ShopkeeperHumanFemaleA1", 97, "Yes.  We would like to see what you have"),
                              ("ShopkeeperHumanFemaleA3", 99, "We would like to look at your spells.")):
        steps += [{"note": {"text": f"{name} (RUDE {rude}) in the shop: a click opens the dialogue; \"{label}\" opens "
                                    "the shop."}}]
        steps += talk(name, rude)
        steps += [choose(rude, rude, label),
                  {"advance_runtime": {"seconds": 0.5}},
                  {"assert": {"dialog": {"active": True, "house_dialog": True}}},
                  {"press_action": {"action": "cancel_dialog"}}, {"press_action": {"action": "cancel_dialog"}},
                  {"advance_runtime": {"seconds": 0.5}}]
    steps += [{"note": {"text": "The innkeeper Thorkatla the Indiscreet (RUDE 101): a click opens her dialogue."}}]
    steps += talk("ShopkeeperHumanFemaleA0", 101)
    steps += [{"press_action": {"action": "cancel_dialog"}}]
    scenarios.write(PROJECT / "scenario_shops.yml", doc, "make_scenarios.py")

    # --- scripted ---------------------------------------------------------------------------------------------------
    a = scripted["actors"]
    doc = header("scripted", "Drangheim City (native BLV) - the location key, shop hours, Sigmund's reward, a letter, "
                             "the altar, Atli's promotion, Guaire A'Velsi, Hrolf")
    steps = doc["steps"]
    letter = next(name for name, e in props.items() if str(e.get("script") or "").lower().startswith("bookletter"))
    steps += [
        {"note": {"text": f"ForadWorld.scr: the location key {citylua.LOCATION_KEY} on load; shops close (5017) from "
                          "20:00 to 06:00."}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"qbit_set": [key(citylua.LOCATION_KEY)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(5017)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_clear": [key(5017)]}},
        {"note": {"text": "NPC87.scr: with the gossip told (key 55), closing Sigmund's dialogue pays 5 000 experience "
                          "and gold (key 300)."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(55), "value": True}},
        *talk_click("SigmundtheStressed0", 87),
        {"press_action": {"action": "cancel_dialog"}}, {"advance_runtime": {"seconds": 0.5}},
        {"assert": {"qbit_set": [key(300)]}},
        {"note": {"text": f"BookLetter.scr: {letter} shows its text."}},
        {"execute_event": {"id": events[letter]}},
        {"assert": {"dialog": {"active": True}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"note": {"text": "NPC88.scr: the Assassin's trial done (key 226): closing Atli's dialogue gives key 227."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(226), "value": True}},
        {"interact_actor": {"actor_index": a["CommonerElfMaleA0"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 88}}},
        {"press_action": {"action": "cancel_dialog"}}, {"advance_runtime": {"seconds": 0.5}},
        {"assert": {"qbit_set": [key(227)]}},
        {"note": {"text": "NPC95.scr: Guaire A'Velsi is hidden until Atli gives his task (key 222); his death gives "
                          "key 225."}},
        {"assert": {"actor_visible": {"actor_index": a["CommonerElfMaleA1"], "hidden": True}}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(222), "value": True}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"actor_visible": {"actor_index": a["CommonerElfMaleA1"], "hidden": False}}},
        {"damage_actor": {"actor_index": a["CommonerElfMaleA1"], "amount": 100000}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_set": [key(225)]}},
    ]
    hx, hy, hz = actors["Hrolf"]
    steps += [{"note": {"text": "NPC110.scr: Hrolf perceives the party: the quarrel (cinematic dwarves_and_humans) "
                                  "starts with key 5010."}},
              {"assert": {"qbit_clear": [key(citylua.HROLF_SEEN_KEY)]}},
              {"set_pose": {"map": MAP, "x": round(hx + 400), "y": round(hy), "z": round(hz), "yaw": 3.1416,
                            "pitch": 0.0}},
              {"advance_runtime": {"seconds": 2}},
              {"assert": {"qbit_set": [key(citylua.HROLF_SEEN_KEY)]}}]
    doc["steps"] += town_portal.scenario_steps(PROJECT / "props.json", events, MAP)   # TownPortal.scr
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- ladders ----------------------------------------------------------------------------------------------------
    doc = header("ladders", "Drangheim City (native BLV) - the three ladders: the tower's, the small house's and the "
                            "leaning one up to the north wall's walkway, climbed up and back down")
    for ladder in scene.get("ladders", []):
        bx, by, bz = ladder["bottom"]
        yaw = ladder["facing_degrees"]
        fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        foot = (bx - fx * 60, by - fy * 60, floors.z(bx - fx * 60, by - fy * 60, bz + 120) + 1)
        top = ladder["top_exit"]
        pose = {"map": MAP, "x": round(foot[0]), "y": round(foot[1]), "z": round(foot[2]), "yaw_degrees": yaw,
                "pitch": 0}
        seconds = max(4.0, (ladder["top"][2] - bz) / 120 + 2)
        doc["steps"] += [
            {"note": {"text": f"{ladder['id']}: forward from its foot climbs to the top and steps off at "
                              f"{[round(v) for v in top]}."}},
            {"movement_segment": {"input": "forward", "seconds": round(seconds, 1), "actor_collision": False,
                                  "actor_ai": False, "start": pose,
                                  "expect_stop": dict(pose, x=round(top[0]), y=round(top[1]), z=round(top[2])),
                                  "loose_tolerance": True, "tolerance_xy": 260, "tolerance_z": 60}}]
        if ladder.get("grab_at_top"):
            # From the top exit, walking toward the ladder's top takes it there and walking on climbs down the line
            # to its foot, on the street.
            tx, ty, tz = ladder["top"]
            down_yaw = math.degrees(math.atan2(ty - top[1], tx - top[0])) % 360.0
            on_top = {"map": MAP, "x": round(top[0]), "y": round(top[1]), "z": round(top[2]), "yaw_degrees":
                      round(down_yaw, 1), "pitch": 0}
            at_foot = dict(on_top, x=round(bx - fx * LADDER_HOLD), y=round(by - fy * LADDER_HOLD), z=round(bz))
            down_seconds = (tz - 16 - bz) / LADDER_CLIMB_SPEED + 0.2
            route = WINDOW_TO_LADDER + [(top[0], top[1])]
            doc["steps"].append({"note": {"text": f"{ladder['id']}: from Klusos House's window arrival (start 0) along "
                                                  "the walkway to the ladder's top exit, in legs, never leaving the "
                                                  "walkway's height."}})
            for k, (a, b) in enumerate(zip(route, route[1:])):
                last = k == len(route) - 2
                leg = scenarios.movement(MAP, (a[0], a[1], WALKWAY_Z),
                                         math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0,
                                         round(math.dist(a, b) / 360, 2), (b[0], b[1], WALKWAY_Z),
                                         tolerance_xy=80 if last else 600, tolerance_z=20)
                doc["steps"].append(leg)
            doc["steps"] += [
                {"note": {"text": f"{ladder['id']}: from its top exit, forward toward its top takes it and climbs down "
                                  f"to its foot at {[at_foot['x'], at_foot['y'], at_foot['z']]}."}},
                {"movement_segment": {"input": "forward", "seconds": round(down_seconds, 1), "actor_collision": False,
                                      "actor_ai": False, "start": on_top, "expect_stop": at_foot,
                                      "loose_tolerance": True, "tolerance_xy": 120, "tolerance_z": 40}}]
    scenarios.write(PROJECT / "scenario_ladders.yml", doc, "make_scenarios.py")

    # --- half steps -------------------------------------------------------------------------------------------------
    doc = header("half_steps", "Drangheim City (native BLV) - forward walks onto the raised floors with the city "
                               "converter's invisible half steps (CITY_PLAYBOOK \"Raised floors\"): probes (read walk_z_distance in the log; the tolerances only keep the run going)")
    for k, step in enumerate(report["stats"].get("city_half_steps") or []):
        cx, cy, cz = step["centre"]
        best = None
        for yaw in (0, 90, 180, 270):
            dx, dy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            low = floors.z(cx - dx * 120, cy - dy * 120, cz + 10)
            high = floors.z(cx + dx * 120, cy + dy * 120, cz + 80)
            if low is not None and high is not None and 50 < high - low <= 66:
                best = (yaw, dx, dy, low, high)
        if best is None:
            continue
        yaw, dx, dy, low, high = best
        pose = {"map": MAP, "x": round(cx - dx * 160), "y": round(cy - dy * 160), "z": round(low + 1),
                "yaw_degrees": yaw, "pitch": 0}
        doc["steps"] += [
            {"note": {"text": f"half step {k + 1} at {step['centre']} (length {step['length']}): from the street "
                              f"({round(low)}) onto the raised floor ({round(high)})."}},
            {"movement_segment": {"input": "forward", "seconds": 1.0, "actor_collision": False, "actor_ai": False,
                                  "start": pose, "expect_stop": dict(pose, x=round(cx + dx * 120),
                                                                     y=round(cy + dy * 120), z=round(high + 1)),
                                  "loose_tolerance": True, "tolerance_xy": 400, "tolerance_z": 200}}]
    scenarios.write(PROJECT / "scenario_half_steps.yml", doc, "make_scenarios.py")
    # NPC378.scr: with key 83 Thorolf sees the party, runs over and talks (RUDE 378) with no click; nobody comes
    # with 106 alone or with 84 (dungeon/scenarios.py thorolf_document)
    doc = scenarios.thorolf_document(project, floors, MAP, header("thorolf", "Thorolf runs up and talks (NPC378.scr)"),
                                     scripted["actors"], actors, key)
    scenarios.write(PROJECT / "scenario_thorolf.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
