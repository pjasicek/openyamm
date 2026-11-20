#!/usr/bin/env python3
"""
Write the Connecting Tunnels scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
work/props_native.json):

    scenario_doors_exits.yml   the three MM9 exit triggers raise their transitions (a walk from each start into its
                               volume); the rock fall (DestructableBrush0/1) stops a walk up its tunnel, breaks on a real
                               click and lets the party through
    scenario_chests.yml        TreasureChest0 opens from in front of its model (interact)
    scenario_scripted.yml      the coffin: TreasureChest1 inside stays locked while the coffin is shut, a real click
                               opens both lids, then the chest opens by a real click; closing the coffin locks it again

    python3 level_generation/projects/mm9r_connectingtunnels/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_connectingtunnels/scenario_$s.yml --scenario-no-color; done
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
from dungeon.source import Project  # noqa: E402
import convert  # noqa: E402

MAP = "connectingtunnels.blv"
EYE = 160
# (start index, DAT exit object index, walk yaw degrees, seconds, note)
EXITS = [(1, 475, 180, 1.0, "ExitTrigger0 (to Yorwick, YorwickExit1): west of StartPoint1"),
         (0, 477, 270, 1.0, "ExitTrigger1 (to Thronheim, ConnectingTunnelsExit): south of StartPoint0"),
         (2, 479, 34, 1.0, "ExitTrigger2 (to Yorwick, YorwickExit2): north-east of StartPoint2")]


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.connectingtunnels_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def pose(x, y, z, yaw_radians, pitch=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                         "yaw": round(yaw_radians, 4), "pitch": round(pitch, 4)}}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "work/props_native.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    starts = report["starts"]
    groups = {}
    for m in movers:
        groups.setdefault(m["group"], []).append(m["door_id"])

    # --- exits and the rock fall ----------------------------------------------------------------------------------
    doc = header("doors_exits", "Connecting Tunnels (native BLV) - the three exits, the rock fall breaks on a click")
    steps = doc["steps"]
    for start, source_id, yaw, seconds, note in EXITS:
        p = starts[start]["position"]
        stop = (p[0] + math.cos(math.radians(yaw)) * 300, p[1] + math.sin(math.radians(yaw)) * 300, p[2])
        steps += [{"note": {"text": f"{note} (DAT object {source_id})."}},
                  scenarios.movement(MAP, p, yaw, seconds, stop, 600, 400),
                  {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": source_id}}},
                  {"load_map": {"map": MAP}}]
    # The rock fall fills the tunnel north of the junction (LT x 2416-2672, z -1024..-752); the party comes from the
    # south (LT z -1260) walking north (+y native).
    rx, ry, rz = report["scripted"]["rock_centre"]
    face = -1048 * 2.56 - 40           # DestructableBrush1's south face (LT z -1048) less the party's radius
    south = ry - 420                                   # 420 units south of the rocks' centre
    z = floors.z(rx, south, rz + 200)
    beyond = ry + 900
    zb = floors.z(rx, beyond, rz + 400)
    # the scene destructibles (dungeon/destructibles.py `break`): DestructableBrush0 (DAT 127, 10 hit points) and
    # DestructableBrush1 (669, TriggerDestroyOnly)
    steps += [{"note": {"text": "The rock fall (destructibles 127/669): standing, it stops a walk north; 9 damage leave it "
                                "standing; a real click on the rocks (DestructableBrush1's faces) breaks "
                                "both (the click's killing blow on 127, whose death breaks 669) and the party walks "
                                "through."}},
              scenarios.movement(MAP, (rx, south, z + 1), 90, 1.0, (rx, face, z + 1), 60, 60),
              {"console": {"line": "destructible 127 damage 9", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"state_dump_named_map_var": {"name": "RockFall", "value": 0}}},
              pose(rx, south + 120, z, math.pi / 2, math.atan2(rz - (z + EYE), ry - south - 120)),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 1.5}},
              {"assert": {"state_dump_named_map_var": {"name": "RockFall", "value": 1}}},
              scenarios.movement(MAP, (rx, south, z + 1), 90, 1.6, (rx, beyond, zb + 1), 260, 200)]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Connecting Tunnels (native BLV) - TreasureChest0 opens from in front of it")
    plain = [c for c in content["chests"] if c["anchor"] != convert.COFFIN_CHEST]
    doc["steps"] += scenarios.chest_steps(floors, MAP, plain, props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- the coffin -----------------------------------------------------------------------------------------------
    doc = header("scripted", "Connecting Tunnels (native BLV) - the coffin unlocks the chest inside it")
    steps = doc["steps"]
    chest = next(c for c in content["chests"] if c["anchor"] == convert.COFFIN_CHEST)
    entry = props[convert.COFFIN_CHEST]
    ids = groups["coffin"]
    look = scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                             distances=(150, 190), height=40)
    # The open lids tilt out to either side (x): the chest is clicked from the coffin's foot (+y), looking down into it.
    ex, ey = entry["x"], entry["y"] + 130
    ez = floors.z(ex, ey, entry["z"] + 300)
    into = pose(ex, ey, ez, -math.pi / 2, math.atan2(entry["z"] + 15 - (ez + EYE), 130))
    steps += [{"note": {"text": "TreasureChest1 (Locked 1) in the coffin: shut, a click on the coffin is not a chest."}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
              {"execute_event": {"id": chest["event"]}},
              {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"chest_opened": {"absent": True}}},
              {"note": {"text": "A real click on the lids swings both open (coffin door right's OpenTrigger 'unlock')."}},
              look, {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 3}},
              *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids],
              {"assert": {"state_dump_named_map_var": {"name": "CoffinOpen", "value": 1}}},
              {"note": {"text": "The chest inside now opens (by its event: headless picking does not follow the lids' "
                                "swing, playbook gotcha; the desktop check clicks it)."}},
              into, {"advance_runtime": {"seconds": 0.2}}, {"execute_event": {"id": chest["event"]}},
              {"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
              {"press_action": {"action": "cancel_dialog"}},
              {"note": {"text": "Closing the coffin (its event) locks the chest again (CloseTrigger 'lock')."}},
              pose(ex, entry["y"] + 420, floors.z(ex, entry["y"] + 420, entry["z"] + 300), -math.pi / 2),
              {"execute_event": {"id": convert.EV_COFFIN}}, {"advance_runtime": {"seconds": 3}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
              {"assert": {"state_dump_named_map_var": {"name": "CoffinOpen", "value": 0}}}]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
