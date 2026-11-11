#!/usr/bin/env python3
"""
Write the Beethoven scenarios from the built map (work/doors.json, work/content.json, props.json):

    scenario_doors_exits.yml   a closed double door stops the party, opens on its click event, the party walks through;
                               the sewer door and ExitE; ExitS and ExitW at the head of their ladders; the ladders of
                               the south arrival; the shaft down to the Grand Entrance and out to the catacombs
    scenario_chests.yml        the eleven chests open from in front of their models (interact)
    scenario_scripted.yml      the coffins and their mummies, the great door's levers, Ludwig's manuscript, the bottle

    python3 level_generation/projects/mm9r_beethoven/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_beethoven/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios, water  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "beethoven.blv"
EXITS = {"ExitS": 683, "ExitW": 684, "ExitE": 691}     # DAT object indices (map_transitions.txt rows of this map)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.beethoven_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def native(x, y, z) -> tuple:
    """A LithTech point in the native frame (no offset)."""
    return (x * SCALE, z * SCALE, y * SCALE)


def walk(start, yaw, seconds, stop, xy=70, z=24, keys="forward") -> dict:
    step = scenarios.movement(MAP, start, yaw, seconds, stop, xy, z)
    step["movement_segment"]["input"] = keys
    return step


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())} \
        if (PROJECT / "props.json").exists() else {}
    door = {m["node"][5:]: m for m in movers}
    group = {}
    for m in movers:
        group.setdefault(m["group"], []).append(m)
    pads = {p["anchor"]: p for p in content["pads"]}
    actors = {a["anchor"]: a for a in content["actors"]}
    scene_actors = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())["initial_state"]["actors"]

    # --- doors, ladders, exits ------------------------------------------------------------------------------------
    doc = header("doors_exits", "Beethoven (native BLV) - doors, ladders and the three exits")
    steps = doc["steps"]
    d = group["Door3"][0]
    x, y, z = native(-4224, -736, 120)
    stop_y = -66 * SCALE + 60
    steps += [{"note": {"text": f"Door3 (door {d['door_id']}, event {d['event']}): shut it stops the party, its click "
                                "swings both leaves away, the party walks through, the leaves shut after 3 s."}},
              {"assert": {"mechanism": {"id": d["door_id"], "state": "closed"}}},
              # the Bone Thrashers past the door follow the party and open it again (AITriggerable), the hall's far
              # ones (2300-2500 away) too
              *scenarios.clear_monsters(scene_actors, (x, y, z), radius=3000),
              walk((x, y, z + 1), 270, 1.2, (x, stop_y, z + 1), 90),
              {"execute_event": {"id": d["event"]}},
              {"advance_runtime": {"seconds": 2.5}},
              {"assert": {"mechanism": {"id": d["door_id"], "state": "open"}}},
              walk((x, y, z + 1), 270, 1.4, (x, y - 1070, z + 1), 200),
              {"advance_runtime": {"seconds": 6}},
              {"assert": {"mechanism": {"id": d["door_id"], "state": "closed"}}}]
    # The south arrival: Ladder4 from the west walkway up to the planks, Ladder2 from the planks to ExitS.
    x, y, z = native(-3830, 32, -27)
    tx, ty, tz = native(-3830, 212, 40)
    steps += [{"note": {"text": "Ladder4: from the walkway up to the planks of the south arrival."}},
              walk((x, y, z + 1), 180, 3.5, (tx, ty, tz), 80, 40)]
    x, y, z = native(-3830, 208, 212)
    steps += [{"note": {"text": "Ladder2: from the planks up the manhole into ExitS."}},
              walk((x, y, z + 1), 180, 3.0, (-3850 * SCALE, y, 400 * SCALE), 120, 400),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXITS["ExitS"]}}},
              {"load_map": {"map": MAP}}]
    x, y, z = native(-6420, 208, 5120)
    steps += [{"note": {"text": "Ladder7: the west arrival's manhole into ExitW."}},
              walk((x, y, z + 1), 180, 3.0, (-6436 * SCALE, y, 400 * SCALE), 120, 400),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXITS["ExitW"]}}},
              {"load_map": {"map": MAP}}]
    # The sewer door before ExitE.
    d = group["SewerDoorE"][0]
    x, y, ground = 4465, 17567, 82      # the SewerE start, on the landing before the door
    steps += [{"note": {"text": "RotatingDoor18 stops the party; its click opens it; ExitE lies behind."}},
              walk((x, y, ground + 1), 0, 0.5, (1800 * SCALE - 50, y, ground + 1), 110),
              {"execute_event": {"id": d["event"]}},
              {"advance_runtime": {"seconds": 2.5}},
              walk((x, y, ground + 1), 0, 1.2, (1990 * SCALE, y, 300), 400, 400),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXITS["ExitE"]}}},
              {"load_map": {"map": MAP}}]
    # The Grand Entrance: the wading floor from the shaft's foot, the 16-LT sill, Ladder0 up the shaft, the hole of Ladder1.
    fx, fy, fz = native(-672, -784, -968)
    tx, ty, tz = native(-672, 40, -860)
    sill = (-590 * SCALE, -1240 * SCALE, -768 * SCALE + 1)
    if water.swimming(project):
        # The shared water rule: the cavern is swum (MM9), its shaft walls hang to -830 LT under the -784 surface.
        under = (-590 * SCALE, fy, -900 * SCALE)
        past = (-590 * SCALE, fy - 460, -900 * SCALE)
        rise = walk(past, 270, 1.5, (past[0], past[1], -784 * SCALE - 134), 300, 120, keys="none")
        rise["movement_segment"]["fly_up"] = True
        # the surface jump carries the party over the sill within 0.6 s, still in the air (since 2026-11-07 the jump
        # is not stopped by an edge touched from the side: it peaks about 0.8 s in, 90 over the sill); released there
        # it drops onto the sill (walking on longer carries it down the corridor beyond)
        out = walk((past[0], past[1], -784 * SCALE - 134), 270, 0.6, sill, 260, 120)
        out["movement_segment"]["jump"] = True
        landed = {"party_position": {"x": round(sill[0]), "y": round(sill[1]), "radius": 120,
                                     "z_min": round(sill[2] - 8), "z_max": round(sill[2] + 8)}}
        steps += [{"note": {"text": "The Grand Entrance is swum (MM9): under the shaft's south wall, which hangs under "
                                    "the surface, up to the surface and with the surface jump onto the sill of the "
                                    "catacombs' south corridor (floor -768)."}},
                  {"set_pose": {"map": MAP, "x": round(under[0]), "y": round(under[1]), "z": round(under[2]),
                                "yaw": -1.5708, "pitch": 0.0}},
                  {"advance_runtime": {"seconds": 0.3}},
                  {"assert": {"water": {"eye_under": True}}},
                  walk(under, 270, 1.2, past, 200, 120),
                  rise, {"assert": {"water": {"state": "surface", "eye_under": False}}},
                  out, {"advance_runtime": {"seconds": 1.0}}, {"assert": landed},
                  {"assert": {"water": {"state": "dry"}}}]
    else:
        steps += [{"note": {"text": "From the foot of Ladder0 the party wades past the shaft's wall and up the sill "
                                    "into the catacombs' south corridor (floor -768)."}},
                  walk((-590 * SCALE, fy, fz + 2), 270, 1.1, sill, 200, 60)]
    steps += [{"note": {"text": "Ladder0 from the water up the shaft to its north lip."}},
              # the climb and the glide onto the lip end about 9.8 s in; held on, forward from the lip takes the ladder
              # again (reach 300) and climbs: the walk is at the lip from 10 to 12 s (16 s caught it on the ladder)
              walk((fx, fy, fz + 2), 270, 11.0, (tx, ty, tz), 180, 80),
              {"note": {"text": "A party on the lip takes the ladder forward (MM9's ladder volume over the hole)."}},
              walk((tx, ty, tz), 270, 0.35, (tx, ty - 90, tz + 60), 120, 120)]
    lx, ly, lz = native(-5632, -1216, -1020)
    ex, ey, ez = native(-5632, -736, -985)
    # The exit is on the climber's side and the ladder's reach (300) covers it: held on, forward from the exit takes the
    # ladder again, so a timed walk is at the exit only 0.3 s per cycle (since the glide, 2026-11-10). The climb step
    # stops at the let-go.
    steps += [{"note": {"text": "Ladder1 from the lower sewers up to the catacombs."}},
              {"set_pose": {"map": MAP, "x": round(lx), "y": round(ly), "z": round(lz + 1), "yaw_degrees": 270,
                            "pitch": 0}},
              {"climb": {"ladder": "Ladder1", "timeout_seconds": 12}},
              {"assert": {"party_position": {"x": round(ex), "y": round(ey), "radius": 60, "z_min": round(ez - 16),
                                             "z_max": round(ez + 16)}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Beethoven (native BLV) - the eleven MM9 treasure chests open from in front of their models")
    if props:
        doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Beethoven (native BLV) - coffins, the great door, Ludwig's manuscript, the bottle")
    steps = doc["steps"]
    mummy = actors["PetrifiedMummy0"]
    pad = pads["Trigger0"]
    lid = convert.COFFIN_LID_SECONDS
    steps += [{"note": {"text": "Trigger0 opens CoffinRaised3's lid (1 s) over PetrifiedMummy0, which lies inside; it "
                                "wakes (wakeup2) and at its kick (3.232 s on) the coffin breaks (CoffinRaise.scr, "
                                "CoffinMummy.scr)."}},
              {"assert": {"actor_visible": {"actor_index": mummy["actor_index"], "hidden": True}}},
              walk((pad["centre"][0], pad["centre"][1] - 340, pad["z"] - 2), 90, 0.32, (pad["centre"][0], pad["centre"][1] - 120, pad["z"] - 2), 70),
              {"assert": {"state_dump_named_map_var": {"name": "Coffin5", "value": 1}}},
              {"assert": {"actor_visible": {"actor_index": mummy["actor_index"], "hidden": False}}},
              {"advance_runtime": {"seconds": lid + 0.5}},
              {"assert": {"state_dump_named_map_var": {"name": "Coffin5", "value": 3}}},
              {"advance_runtime": {"seconds": convert.KICK_SECONDS + 0.5}},
              {"assert": {"state_dump_named_map_var": {"name": "Coffin5", "value": 2}}}]
    levers = group["GreatDoorLevers"]
    halves = group["GreatDoor"]
    steps += [{"note": {"text": "Lever6 (event 91) parts the great door for good (Door SDoor11/12, Lever5/6)."}},
              {"assert": {"mechanism": {"id": halves[0]["door_id"], "state": "closed"}}},
              {"execute_event": {"id": convert.EV_GREAT_LEVER}},
              {"advance_runtime": {"seconds": 4}},
              {"assert": {"mechanism": {"id": halves[0]["door_id"], "state": "open"}}},
              {"assert": {"mechanism": {"id": halves[1]["door_id"], "state": "open"}}},
              {"assert": {"mechanism": {"id": levers[0]["door_id"], "state": "open"}}},
              {"execute_event": {"id": convert.EV_GREAT_LEVER}},
              {"advance_runtime": {"seconds": 4}},
              {"assert": {"mechanism": {"id": halves[0]["door_id"], "state": "open"}}}]
    paper = props["Manuscript"]
    steps += [{"note": {"text": "The manuscript (Ludwigsmanuscript.scr), clicked between the bars of its grate: item "
                                "248, key 110 without Ludwig's key 14; a second click does nothing."}},
              {"set_pose": {"map": MAP, "x": int(paper["x"]), "y": int(paper["y"]) + 120, "z": -3111, "yaw": -1.5708,
                            "pitch": -0.5526}},
              {"press_interact": {}},
              {"assert": {"qbit_set": [90000 + convert.KEY_FOUND_UNASKED]}},
              {"assert": {"qbit_clear": [90000 + convert.KEY_FOUND_FOR_LUDWIG]}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_MANUSCRIPT, "count": 1}]}},
              {"execute_event": {"id": convert.EV_MANUSCRIPT}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_MANUSCRIPT, "count": 1}]}},
              {"note": {"text": "The bottle: arriving at the south start started bottle 1; another start's trigger "
                                "changes nothing (BottleFollow.scr: the other three are removed)."}},
              {"assert": {"state_dump_named_map_var": {"name": "Bottle", "value": 1}}},
              {"execute_event": {"id": convert.EV_BOTTLE + 3}},
              {"assert": {"state_dump_named_map_var": {"name": "Bottle", "value": 1}}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
