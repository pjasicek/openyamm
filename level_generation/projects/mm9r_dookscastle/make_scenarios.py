#!/usr/bin/env python3
"""
Write the Dook's Castle scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json, the compiled scene):

    scenario_doors_exits.yml   the gate exit raises its transition; a shut door stops the party, opens on a real click
                               and lets it through; every double door opens on a real click; Ladder0 climbs from the
                               lake's wading surface to the bridge
    scenario_chests.yml        the six chests on floors open from in front of their models (interact); the seventh,
                               on the lake bed, by the dive pad over it
    scenario_scripted.yml      the guards stay friendly; both letters and Baron Dook's dialogue by real clicks; the
                               sleepers' trigger, the scurrying basilisks; the shield opens the secret door, which
                               turns the guards hostile
    scenario_alarm.yml         hurting a guard rings the alarm and turns every guard hostile

    python3 level_generation/projects/mm9r_dookscastle/make_scenarios.py
    for s in doors_exits chests scripted alarm; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_dookscastle/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "dookscastle.blv"
EXIT_OBJECT = 384                   # ExitTrigger0 (DAT object 384): the gate, south of StartPoint0
EYE = 160
RUDE_BARON = 415


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.dookscastle_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def pose(x, y, z, yaw_radians, pitch=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                         "yaw": round(yaw_radians, 4), "pitch": round(pitch, 4)}}


def var(name: str, value: int) -> dict:
    return {"assert": {"named_map_var_changed": {"name": name, "current": value}}}


# Doorways whose UserPortal is flat across LT z (dims [64, 60, 0]): their normal is native y; the others' is x.
NORMAL_Y = {"door05", "door06"}


def door_sides(floors, centre, distance, group):
    """Poses on both sides of a doorway (native centre at mid height) along its normal: (x, y, floor z, yaw toward the
    door)."""
    cx, cy, cz = centre
    floor = cz - 154                     # the doorways are 307 high: centre 154 over the floor
    out = []
    for dx, dy in (((0, 1), (0, -1)) if group in NORMAL_Y else ((1, 0), (-1, 0))):
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
    scene = yaml.load((PROJECT / "work/runtime/dookscastle.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    actors = scene["initial_state"]["actors"]
    scripted = report["scripted"]
    index = scripted["actors"]
    portals = {p["name"]: p for p in report["portals"]}
    groups = {}
    for m in movers:
        groups.setdefault(m["group"], []).append(m)
    doors = {f"door0{k}": portals[f"doorportal0{k}"]["centre_native"] for k in range(1, 8)}

    def at(name):
        a = actors[index[name]]["position"]
        return a["x"], a["y"], a["z"]

    # --- doors, ladder and the exit -------------------------------------------------------------------------------
    doc = header("doors_exits", "Dook's Castle (native BLV) - the gate, every double door by a click, the lake ladder")
    steps = doc["steps"]
    start = report["starts"][0]["position"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 384): the gate, south of StartPoint0."}},
              scenarios.movement(MAP, start, 270, 0.8, (start[0], start[1] - 250, start[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    group = "door03"
    sides = door_sides(floors, doors[group], 260, group)
    x, y, z, yaw = next(s for s in sides if s[0] < doors[group][0])        # from the corridor, west of it
    cx, cy, _ = doors[group]
    beyond = (cx + (cx - x) * 0.9, cy + (cy - y) * 0.9)
    stop = (cx + (x - cx) * 70 / 260, cy + (y - cy) * 70 / 260)
    ids = [m["door_id"] for m in groups[group]]
    steps += [{"note": {"text": f"{group}: the shut door stops a walk from {int(x)}, {int(y)}; opened by a click, the "
                                "party walks through; MM9's CloseWaitTime 3 s shuts it again."}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
              scenarios.movement(MAP, (x, y, z + 1), math.degrees(yaw), 0.8,
                                 (stop[0], stop[1], floors.z(stop[0], stop[1], z + 80) + 1), 50, 20),
              pose(x, y, z, yaw, math.atan2(doors[group][2] - (z + EYE), 260)),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 2.5}},
              *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids],
              scenarios.movement(MAP, (x, y, z + 1), math.degrees(yaw), 0.7,
                                 (beyond[0], beyond[1], floors.z(beyond[0], beyond[1], z + 80) + 1), 90, 20),
              {"advance_runtime": {"seconds": 8}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids]]
    for group, centre in sorted(doors.items()):
        sides = door_sides(floors, centre, 170, group)
        if not sides:
            raise SystemExit(f"{group}: no floor beside its doorway")
        x, y, z, yaw = sides[0]
        ids = [m["door_id"] for m in groups[group]]
        steps += [{"note": {"text": f"{group} (doors {ids}): shut, a click from {int(x)}, {int(y)} opens both leaves."}},
                  {"advance_runtime": {"seconds": 5}},
                  *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
                  pose(x, y, z, yaw, math.atan2(centre[2] - (z + EYE), 170)), {"advance_runtime": {"seconds": 0.2}},
                  {"press_interact": {}}, {"advance_runtime": {"seconds": 2.5}},
                  *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids]]
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder0")
    bx, by, bz = ladder["bottom"]
    tx, ty, tz = ladder["top_exit"]
    swim = "DiveChest6" not in scripted["pads"]      # the shared water rule: Ladder0's foot under the surface (MM9)
    steps += [{"note": {"text": "Ladder0: from the lake " + ("water, its foot under the surface," if swim else
                                                             "'s wading surface (-1504 LT)") +
                                " up the rungs to the bridge's platform (MM9: the way out of the water)."}},
              {"load_map": {"map": MAP}},
              scenarios.movement(MAP, (bx - 74, by, bz + 1), 0, 3.0 if swim else 2.6, (tx, ty, tz + 1), 200, 60)]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Dook's Castle (native BLV) - the chests open from in front of them; the lake bed's by diving")
    dive = scripted["pads"].get("DiveChest6")
    # The shared water rule: the lake is swum, TreasureChest6 an ordinary chest on its bed (no dive pad)
    floor_chests = [c for c in content["chests"] if c["anchor"] != convert.DIVE_CHEST or dive is None]
    doc["steps"] += scenarios.chest_steps(floors, MAP, floor_chests, props)
    lake = next(c for c in content["chests"] if c["anchor"] == convert.DIVE_CHEST)
    dx, dy, dz = dive["centre"] if dive else (0, 0, 0)
    doc["steps"] += [] if dive is None else [{"note": {"text": "TreasureChest6 on the lake bed (MM9: the party dives): stepping onto the wading "
                                       "surface over it opens it."}},
                     scenarios.movement(MAP, (dx - 220, dy, dz), 0, 0.6, (dx, dy, dz), 120, 40),
                     {"advance_runtime": {"seconds": 0.3}},
                     {"assert": {"chest_opened": {"chest_id": lake["container_id"]}}},
                     {"press_action": {"action": "cancel_dialog"}}]
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Dook's Castle (native BLV) - friendly guards, letters, Baron Dook, sleepers, basilisks, "
                             "the secret door and the hostility it brings")
    steps = doc["steps"]
    guard = index["DooksGuardCaptain11"]
    gx, gy, gz = at("DooksGuardCaptain11")
    watch = pose(gx, gy - 400, floors.z(gx, gy - 400, gz + 60), math.pi / 2)
    # Hostile, a monster closes to about 400 of a party in plain view and holds there (Drangheim Prison's probes): the
    # chase is watched from 1000 down the corridor.
    far = pose(gx, gy - 1000, floors.z(gx, gy - 1000, gz + 60), math.pi / 2)
    everyone = [(a["position"]["x"], a["position"]["y"]) for a in actors]
    steps += [{"note": {"text": "DookHostility.inc: AddFriend Player while DOOK_HOSTILITY stands. Guard "
                                f"{guard} in plain view 400 units up the corridor does not come for the party."}},
              watch, {"advance_runtime": {"seconds": 4}},
              {"assert": {"actor_visible": {"actor_index": guard, "hostile_to_party": False, "report_state": True,
                                            "combat_targeting_party": False}}},
              var("Hostile", 0)]
    for name, (event, number) in convert.EV_LETTERS.items():
        entry = props[name]
        steps += [{"note": {"text": f"{name}: the letter (BookLetter.scr DoLetter {number}) on a click."}},
                  scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                    distances=(90, 120), height=2, max_drop=140, avoid=everyone),
                  {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                  {"assert": {"dialog": {"active": True}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    bx, by, bz = at("dook")
    steps += [{"note": {"text": "Baron Dook (NPC415.scr :OnUse DoRude 415): a click opens MM9's dialogue 415."}},
              scenarios.look_at(floors, MAP, (bx, by, bz), 270, distances=(150, 200), height=60,
                                avoid=[a for a in everyone if a != (bx, by)]),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": RUDE_BARON}}},
              {"assert": {"dialog": {"active": True, "source_id": RUDE_BARON}}},
              {"press_action": {"action": "cancel_dialog"}}]
    box = report_box("SleepTrigger")
    sx, sy = (box[0][0] + box[1][0]) / 2, (box[0][1] + box[1][1]) / 2
    sz = floors.z(sx, sy, box[1][2])
    # the sargent's last marker, as the map script has it (local SMKR0, SMKR1 = {x, y, z}, {x, y, z})
    smkr1 = [int(v) for v in re.search(r"local SMKR0, SMKR1 = \{[^}]*\}, \{([^}]*)\}",
                                       (PROJECT / "work/runtime/dookscastle.lua").read_text())[1].split(",")]
    steps += [{"note": {"text": "SleepTrigger (DC_sargent.scr StartUp): the sargent walks to the four sleepers in turn, "
                                "wakes each and ends at SMkr1."}},
              pose(sx, sy - 300, floors.z(sx, sy - 300, sz + 60), math.pi / 2),
              {"advance_runtime": {"seconds": 1}}, var("FiredSleepTrigger", 0),
              scenarios.movement(MAP, (sx, sy - 300, floors.z(sx, sy - 300, sz + 60) + 1), 90, 0.5, (sx, sy, sz + 1),
                                 200, 30),
              {"advance_runtime": {"seconds": 1}}, var("FiredSleepTrigger", 1),
              {"advance_runtime": {"seconds": 40}}, var("SleepWoken", len(scripted["sleepers"]) + 2),
              {"assert": {"actor_visible": {"actor_index": index["SleepCaptain"],
                                            "near": {"x": smkr1[0], "y": smkr1[1], "max_distance": 120}}}}]
    for trigger in ("ScurryTrigger1", "ScurryTrigger0"):
        box = report_box(trigger)
        cx, cy, cz = [(box[0][k] + box[1][k]) / 2 for k in range(3)]
        floor = floors.z(cx, cy, cz + 40)
        members = [index[n] for n in convert.SCURRY[trigger]]
        steps += [{"note": {"text": f"{trigger}: its three small basilisks run off and vanish (ScurryCreature.scr Hide)."}},
                  *[{"assert": {"actor_visible": {"actor_index": i, "hidden": False}}} for i in members],
                  pose(cx, cy, floor, 0.0), {"advance_runtime": {"seconds": 1}},
                  var(trigger, 1),
                  *[{"assert": {"actor_visible": {"actor_index": i, "hidden": True}}} for i in members]]
    shield = props["Sheild0"]
    door = groups["doorslide"][0]["door_id"]
    sz = floors.z(shield["x"], shield["y"] - 160, shield["z"])
    steps += [{"note": {"text": "Sheild0 over the invisible Tempbutton: a click turns it (OpenTriggers: doorslide open, "
                                "Tempbutton lock); the secret door slides open and DOOK_HOSTILITY is gone."}},
              {"assert": {"mechanism": {"id": door, "state": "closed"}}},
              pose(shield["x"], shield["y"] - 160, sz, math.pi / 2, math.atan2(shield["z"] + 45 - (sz + EYE), 160)),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"advance_runtime": {"seconds": 5}},
              var("SecretOpen", 1), var("Hostile", 1),
              {"assert": {"mechanism": {"id": door, "state": "open"}}},
              {"note": {"text": f"Guard {guard} 1000 down the corridor now comes for the party and closes to within "
                                "500 (it holds about 400 off, where its targeting flag drops; the map reloaded: the "
                                "movement steps above froze the actors; Hostile stays set over the reload)."}},
              {"load_map": {"map": MAP}}, far, {"advance_runtime": {"seconds": 6}},
              {"assert": {"actor_visible": {"actor_index": guard, "hostile_to_party": True, "report_state": True,
                                            "near": {"x": int(gx), "y": int(gy - 1000), "max_distance": 500}}}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- the alarm --------------------------------------------------------------------------------------------------
    doc = header("alarm", "Dook's Castle (native BLV) - hurting a guard rings the alarm: every guard turns hostile")
    other = index["DooksGuardCaptain12"]
    doc["steps"] += [var("Hostile", 0),
                     {"assert": {"actor_visible": {"actor_index": other, "hostile_to_party": False}}},
                     {"damage_actor": {"actor_index": guard, "amount": 10}},
                     {"advance_runtime": {"seconds": 0.5}},
                     var("Hostile", 1),
                     {"assert": {"actor_visible": {"actor_index": other, "hostile_to_party": True}}}]
    scenarios.write(PROJECT / "scenario_alarm.yml", doc, "make_scenarios.py")
    return 0


_BOXES = None


def report_box(name):
    """A trigger's polled box (native low, high), as convert.py computes it."""
    global _BOXES
    if _BOXES is None:
        project = Project.load(PROJECT, install=False)
        from dungeon.source import Source
        import numpy as np
        source = Source(project)
        _BOXES = {}
        for trigger in ("SleepTrigger", *convert.EV_SCURRY):
            p = source.properties(trigger)
            centre, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
            low, high = project.native(centre - dims), project.native(centre + dims)
            _BOXES[trigger] = [np.minimum(low, high).tolist(), np.maximum(low, high).tolist()]
    return _BOXES[name]


if __name__ == "__main__":
    sys.exit(main())
