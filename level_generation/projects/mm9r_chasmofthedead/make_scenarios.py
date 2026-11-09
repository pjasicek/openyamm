#!/usr/bin/env python3
"""
Write the Chasm of the Dead scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json):

    scenario_doors_exits.yml   the exit to Drangheim raises its MM9 exit trigger; a closed door stops the party, opens
                               on its click, the party walks through (a top tomb and a deep door)
    scenario_chests.yml        the sixteen chests open from in front of their models (interact)
    scenario_scripted.yml      each scripted class: shooter plate, hidden shooter, closing walls, spike wave, crusher,
                               pendulums, acid grate, mummy chains, buried zombies, apparitions, the Lich Instructions
                               and the Crona Kiga
    scenario_pivot.yml         the pivot trap tips the party into the spike pit, the ladder and hatch lead out

    python3 level_generation/projects/mm9r_chasmofthedead/make_scenarios.py
    for s in doors_exits chests scripted pivot; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_chasmofthedead/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "chasmofthedead.blv"
EXIT_OBJECT = 1114                  # ExitTrigger0 (DAT object index; map_transitions.txt row of this map)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.chasmofthedead_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def native(x, z):
    return int(round(x * SCALE)), int(round(z * SCALE))


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())} if (PROJECT / "props.json").exists() else {}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    door = {m["node"][5:]: m for m in movers}
    group_doors = {}
    for m in movers:
        group_doors.setdefault(m["group"], []).append(m["door_id"])
    tops = scenarios.door_tops(PROJECT / "work/runtime", MAP, project.stem)
    start = report["starts"][0]["position"]
    boxes = report["scripted"]["boxes"]

    def state(name, value):
        return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}

    def plate(name, distance=220, avoid=()):
        """A walk onto a pressure plate's top."""
        top = [float(v) for v in tops[door[name]["door_id"]]]
        return scenarios.walk_onto(floors, MAP, top, name, distance=distance, avoid=avoid)

    def pose(x, y, z, yaw=0):
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)), "yaw": yaw, "pitch": 0}}

    def in_box(name, drop=0):
        low, high = boxes[name]
        x, y = (low[0] + high[0]) / 2, (low[1] + high[1]) / 2
        z = floors.z(x, y, high[2] + 40)
        return pose(x, y, (z if z is not None else low[2]) + 1 + drop)

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Chasm of the Dead (native BLV) - the exit to Drangheim and tomb doors")
    steps = doc["steps"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 1114): the entrance to Drangheim, just north of the start."}},
              scenarios.movement(MAP, start, 90, 0.8, (start[0], start[1] + 300, start[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    # Door15 (Doorportal0, the entry tomb's south door) and Door35 (the gate from the chasm to the deep halls).
    for name, (sx, sy), yaw, stop, through, axis in (("Door15", native(-5152, 9420), 270, 9192 * SCALE + 60,
                                                      8900 * SCALE, 1),
                                                     ("Door35", native(2720, 5456), 0, 2952 * SCALE - 60,
                                                      3120 * SCALE, 0)):
        m = door[name]
        z = floors.z(sx, sy, 3000 if name == "Door15" else -3400)
        target = (stop, sy) if axis == 0 else (sx, stop)
        beyond = (through, sy) if axis == 0 else (sx, through)
        steps += [{"note": {"text": f"{name} (door {m['door_id']}, event {m['event']}) is shut."}},
                  {"assert": {"mechanism": {"id": m["door_id"], "state": "closed"}}},
                  scenarios.movement(MAP, (sx, sy, z + 1), yaw, 1.0, (target[0], target[1], z + 1), 90, 70),
                  {"execute_event": {"id": m["event"]}},
                  {"advance_runtime": {"seconds": 3.5}},
                  {"assert": {"mechanism": {"id": m["door_id"], "state": "open"}}},
                  scenarios.movement(MAP, (sx, sy, z + 1), yaw, 1.9, (beyond[0], beyond[1], z + 1), 700, 400)]
    # A stair walked upward (16 LT risers, 41 native: the party climbs them, monsters' path planner stops at 40).
    sx, sy = native(-4080, 5010)
    z = floors.z(sx, sy, 1500)
    ex, ey = native(-4780, 5150)
    ez = floors.z(ex, ey, 1500)
    steps += [{"note": {"text": "The long stair from the plate passage up to the first hall."}},
              scenarios.movement(MAP, (sx, sy, z + 1), 168.7, 2.6, (ex, ey, ez + 1), 200, 40)]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Chasm of the Dead (native BLV) - the sixteen MM9 treasure chests open")
    if props:
        doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props, direct={"TreasureChest1"})
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Chasm of the Dead (native BLV) - traps, mummies, zombies, apparitions and quest objects")
    steps = doc["steps"]
    plates = group_doors["ShooterPlate5"][0]
    steps += [
        {"note": {"text": "ShooterPlate5 sinks and Shooter2 fires one bolt; the plate rises after 1 s."}},
        plate("ShooterPlate5", avoid=[tops[door["ShooterPlate6"]["door_id"]][:2], tops[door["ShooterPlate7"]["door_id"]][:2]]),
        state("ShotsFired", 1),
        {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"mechanism": {"id": plates, "state": "closed"}}},
        {"note": {"text": "HSP1: the plate opens the SD1 and SD2 shutters (rotating) and their shooters fire."}},
        plate("HSP1"),
        state("ShotsFired", 3),
        {"advance_runtime": {"seconds": 0.4}},
        {"assert": {"mechanism": {"id": group_doors["SD1"][0], "state": "open"}}},
        {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"mechanism": {"id": group_doors["SD1"][0], "state": "closed"}}},
        {"note": {"text": "CWPlate1: both pairs of walls slam in, the party between them is hurt; they draw back."}},
        pose(*tops[door["CWPlate1"]["door_id"]][:2], tops[door["CWPlate1"]["door_id"]][2] + 2),
        {"execute_event": {"id": convert.EV_CLOSING_WALLS}},
        {"advance_runtime": {"seconds": 0.5}},
        state("WallHits", 1),
        {"assert": {"mechanism": {"id": group_doors["CWR1"][0], "state": "open"}}},
        {"advance_runtime": {"seconds": 5.5}},
        {"assert": {"mechanism": {"id": group_doors["CWR1"][0], "state": "closed"}}},
        {"note": {"text": "SpikeRowPlate1: the spike wave runs the stair's length and the plate resets."}},
        pose(*tops[door["SpikeRowPlate1"]["door_id"]][:2], tops[door["SpikeRowPlate1"]["door_id"]][2] + 2),
        {"execute_event": {"id": convert.EV_SPIKE_PLATE}},
        {"advance_runtime": {"seconds": 3.5}},
        state("SpikeWave", 0),
        {"note": {"text": "CeilingCrushPlate3: the ceiling drops on the party (20) and rises after 3 s."}},
        pose(*tops[door["CeilingCrushPlate3"]["door_id"]][:2], tops[door["CeilingCrushPlate3"]["door_id"]][2] + 2),
        {"execute_event": {"id": convert.EV_CRUSHER["CeilingCrushPlate3"]}},
        {"advance_runtime": {"seconds": 0.6}},
        state("CrushHits", 1),
        {"assert": {"mechanism": {"id": group_doors["CeilingCrush3"][0], "state": "open"}}},
        {"advance_runtime": {"seconds": 5.5}},
        {"assert": {"mechanism": {"id": group_doors["CeilingCrush3"][0], "state": "closed"}}},
        {"note": {"text": "PendulumTrigger1: both blades swing through (rotating, sticky); the party in the band is hurt."}},
        in_box("PendulumTrigger1"),
        {"advance_runtime": {"seconds": 2.6}},
        state("PendulumHits", 1),
        {"assert": {"mechanism": {"id": group_doors["Pendulum1"][0], "state": "open"}}},
        {"note": {"text": "GratetrapTrigger0: the grate slides away, the party drops into the acid and is hauled out."}},
        pose((boxes["GratetrapTrigger0"][0][0] + boxes["GratetrapTrigger0"][1][0]) / 2,
             (boxes["GratetrapTrigger0"][0][1] + boxes["GratetrapTrigger0"][1][1]) / 2, -2082 * SCALE + 2),
        {"advance_runtime": {"seconds": 1.2}},
        {"assert": {"mechanism": {"id": group_doors["Gratetrap0"][0], "state": "open"}}},
        # the party swims in the pit right under the grate (the shared water rule); the third second's lift
        # (evt.MoveToMap from the poll timer) happens as in the game's frame, so the grate shuts behind it
        {"advance_runtime": {"seconds": 5, "follow_map_move": True}},
        state("AcidLifts", 1),
        # the grate shuts 5.5 s after the trigger; the skeletons chasing the party fall through the open grate and one
        # under its closing edge opens it again (bodies: reverse, MM9 ReopenOnContact) until its 5 s auto-close
        {"wait_until": {"timeout_runtime_seconds": 12,
                        "assert": {"mechanism": {"id": group_doors["Gratetrap0"][0], "state": "closed"}}}},
        {"note": {"text": "Trigger7 awakens its four mummies; the Crona Kiga wakes PetrifiedMummy16 and its chain of 14."}},
        in_box("Trigger7"),
        {"advance_runtime": {"seconds": 0.5}},
        state("MummiesAwake", 4),
        *scenarios.pick_up_steps(floors, MAP, scene, "CronaKiga"),
        state("MummiesAwake", 18),
        {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_CRONA, "count": 1}]}},
        {"assert": {"qbit_set": [90000 + convert.KEY_CRONA_FOUND]}},
        {"note": {"text": "Trigger2: its zombies rise. Trigger6 only arms after Trigger5 (MM9 StartOn 0)."}},
        in_box("Trigger2"),
        {"advance_runtime": {"seconds": 0.5}},
        state("ZombiesRisen", 1),
        in_box("Trigger6"),
        {"advance_runtime": {"seconds": 0.5}},
        state("ZombiesRisen", 1),
        in_box("Trigger5"),
        {"advance_runtime": {"seconds": 0.5}},
        state("ZombiesRisen", 2),
        in_box("Trigger6"),
        {"advance_runtime": {"seconds": 0.5}},
        state("ZombiesRisen", 3),
        {"note": {"text": "Apparition13: the ghost spawner's first marker raises an Apparition (9139)."}},
        in_box("Apparition13"),
        {"advance_runtime": {"seconds": 1.5}},
        state("GhostsSpawned", 1),
        {"assert": {"actor_count": {"monster_id": convert.APPARITION, "min": 1}}},
        {"note": {"text": "The Lich Instructions, a world item, picked up: item 447 and key 296 (LichInstructions.scr)."}},
        *scenarios.pick_up_steps(floors, MAP, scene, "LichInstructions"),
        {"assert": {"qbit_set": [90000 + convert.KEY_INSTRUCTIONS]}},
        {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_INSTRUCTIONS, "count": 1}]}},
    ]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- the pivot trap -------------------------------------------------------------------------------------------
    doc = header("pivot", "Chasm of the Dead (native BLV) - the pivot trap, its spike pit, ladder and hatch")
    steps = doc["steps"]
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder4")
    trap, hatch = group_doors["PivotWallTrap1"][0], group_doors["TrapExitDoor1"][0]
    floor_z = int(round(-1728 * SCALE))
    pit_z = int(round(ladder["bottom"][2]))
    on_trap = native(992, -1776)
    foot = [int(round(ladder["bottom"][0])), int(round(ladder["bottom"][1])) - 60, pit_z]
    top = [int(round(v)) for v in ladder["top_exit"]]

    def walk(x0, y0, z0, yaw, seconds, x1, y1, z1, xy=60, tz=16, input_="forward"):
        return {"movement_segment": {
            "input": input_, "seconds": seconds, "actor_collision": False, "actor_ai": False,
            "start": {"map": MAP, "x": x0, "y": y0, "z": z0, "yaw_degrees": yaw, "pitch": 0},
            "expect_stop": {"map": MAP, "x": x1, "y": y1, "z": z1, "yaw_degrees": yaw, "pitch": 0},
            "loose_tolerance": True, "tolerance_xy": xy, "tolerance_z": tz}}

    steps += [{"note": {"text": "PivotWallTrap1: the floor half tips the party into the pit."}},
              {"assert": {"mechanism": {"id": trap, "state": "closed"}}},
              walk(on_trap[0] + 40, on_trap[1] - 250, floor_z + 2, 90, 0.6, on_trap[0] + 40, on_trap[1], floor_z, xy=400, tz=900),
              {"advance_runtime": {"seconds": 2.5}},
              {"assert": {"mechanism": {"id": trap, "state": "open"}}},
              {"assert": {"state_dump_named_map_var": {"name": "PivotTrap", "value": 1}}},
              {"note": {"text": "The trap turns back after 5 s."}},
              {"advance_runtime": {"seconds": 8}},
              {"assert": {"mechanism": {"id": trap, "state": "closed"}}},
              {"note": {"text": "TrapExitDoor1 opens on its click; the party climbs Ladder4 out beside it."}},
              {"execute_event": {"id": convert.EV_HATCH}},
              {"advance_runtime": {"seconds": 2}},
              {"assert": {"mechanism": {"id": hatch, "state": "open"}}},
              walk(foot[0], foot[1], foot[2], 90, 3.7, top[0], top[1], top[2], xy=1500, tz=100),
              {"note": {"text": "The hatch shuts itself after 5 s."}},
              {"advance_runtime": {"seconds": 7}},
              {"assert": {"mechanism": {"id": hatch, "state": "closed"}}}]
    scenarios.write(PROJECT / "scenario_pivot.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
