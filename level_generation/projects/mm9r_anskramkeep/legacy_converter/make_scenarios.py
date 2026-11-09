#!/usr/bin/env python3
"""
Write the keep's two population scenarios from the built map (work/runtime, work/content.json, props.json):

- scenario_chests.yml: stands in front of each of the 7 MM9 chests, looks at it and presses interact, expecting that
  chest to open (TreasureChest1 after its treasure panel slides up);
- scenario_scripted.yml: the gate (a switch is locked until PanelLever; SwitchLever0 uncovers the switches; a switch
  opens both gate doors and the party walks through), a shooter plate (sinks, a fire bolt flies), a ceiling crusher
  (drops, hurts the party on its plate, rises), a cage (its wall sinks when the party steps on its trigger) and an
  Imp gate (its trigger sends an Imp).

    python3 level_generation/projects/mm9r_anskramkeep/make_scenarios.py
    ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_anskramkeep/scenario_chests.yml
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
EYE = 160
WALK = 768                      # party speed in scenarios (always run: units per second)


class Floors:
    def __init__(self):
        source = convert.Source()
        plan = convert.classify_models(source, yaml.safe_load(convert.OVERRIDES.read_text()))
        # A trap's closed cross is the floor over its pit.
        traps = [name for name, rule in plan["movers"].items() if rule.get("carry")]
        polygons = [p for m in plan["static"] + traps for p in source.polygons(m)]
        self.floors = [p for p in polygons if p.normal[1] >= 0.7 and p.role == "static"]

    def z(self, x, y, z_from):
        """The floor (native z) under a native point, searched from z_from down."""
        found = convert.floor_below(self.floors, (x / convert.SCALE, z_from / convert.SCALE + 1, y / convert.SCALE))
        return None if found is None else found * convert.SCALE

    def clear(self, a, b, z) -> bool:
        """The floor from a toward b stays at height z (no step, no hole on the way); the last stretch is the
        target's own plate or pad, which may be a mover."""
        for t in np.linspace(0, 0.6, 7):
            p = np.asarray(a, float) + t * (np.asarray(b, float) - np.asarray(a, float))
            found = self.z(p[0], p[1], z + 40)
            if found is None or abs(found - z) > 2:
                return False
        return True


def walk_onto(floors, target, name, distance=220, avoid=()):
    """A short forward walk that ends on the target point, from the first side whose floor is level and clear."""
    x, y, z = target
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        start = (x + dx * distance, y + dy * distance)
        if any(math.dist(start, a) < 200 for a in avoid):
            continue
        floor = floors.z(start[0], start[1], z + 40)
        if floor is None or abs(floor - z) > 12 or not floors.clear(start, (x, y), z):
            continue
        yaw = math.degrees(math.atan2(-dy, -dx)) % 360
        pose = {"map": MAP, "x": int(round(start[0])), "y": int(round(start[1])), "z": int(round(z)) + 1,
                "yaw_degrees": round(yaw, 1), "pitch": 0}
        stop = dict(pose, x=int(round(x)), y=int(round(y)))
        return {"movement_segment": {"input": "forward", "seconds": round(distance / WALK, 2),
                                     "actor_collision": False, "actor_ai": False, "start": pose, "expect_stop": stop,
                                     "loose_tolerance": True, "tolerance_xy": 60, "tolerance_z": 16}}
    raise SystemExit(f"{name}: no level approach")


def floor_of(pad: dict) -> list:
    """A trigger pad's centre on the floor under it (pads stand content.PAD_LIFT over it)."""
    import content
    x, y, z = pad["centre"]
    return [x, y, z - content.PAD_LIFT]


def door_tops(runtime: Path) -> dict:
    """door id -> the centre of its highest horizontal face (a plate's top), native."""
    sys.path.insert(0, str(convert.ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(runtime / MAP)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    faces = {f["index"]: f for f in blv["faces"]}
    scene = json.loads((runtime / f"{convert.STEM}.scene.yml").read_text())
    tops = {}
    for door in scene["initial_state"]["doors"]:
        best = None
        for fid in door["face_ids"]:
            points = vertices[faces[fid]["vertex_indices"]]
            if np.ptp(points[:, 2]) < 1 and (best is None or points[0, 2] > best[2]):
                best = points.mean(0)
        if best is not None:
            tops[door["door_id"]] = best
    return tops


def chests_scenario(floors) -> dict:
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    panel = next(m["door_id"] for m in json.loads((PROJECT / "work/doors.json").read_text())
                 if m["group"] == "PivotTreasurePanel1")
    steps = [{"load_map": {"map": MAP}}]
    for chest in content["chests"]:
        entry = props[chest["anchor"]]
        cx, cy, cz = entry["x"], entry["y"], entry["z"]
        yaw = math.radians(entry["yaw_degrees"])
        front = (-math.sin(yaw), math.cos(yaw))
        for distance, (fx, fy) in ((150, front), (150, (-front[1], front[0])), (150, (front[1], -front[0]))):
            x, y = cx + fx * distance, cy + fy * distance
            z = floors.z(x, y, cz + 200)
            if z is not None:
                break
        look = math.atan2(cy - y, cx - x)
        pitch = math.atan2(cz + 25 - (z + EYE), math.dist((x, y), (cx, cy)))
        pose = {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}
        if chest["anchor"] == "TreasureChest1":
            # Headless runs pick against the renderer's vertex copy, which follows door motion only while frames
            # render: the slid-up panel still takes the click there, so the chest's event runs directly.
            steps += [{"note": {"text": "TreasureChest1 sits behind PivotTreasurePanel1, which slides up (event 70); "
                                        "headless picking does not see moved doors, so the chest's event runs."}},
                      pose, {"press_interact": {}}, {"advance_runtime": {"seconds": 2}},
                      {"assert": {"mechanism": {"id": panel, "state": "open"}}},
                      {"execute_event": {"id": chest["event"]}}]
        else:
            steps += [pose, {"press_interact": {}}]
        steps += [{"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    return {"id": "mm9r.anskramkeep_chests", "title": "Anskram Keep (native BLV): the seven MM9 chests open from in "
            "front of their models", "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"],
            "steps": steps}


def scripted_scenario(floors) -> dict:
    content = json.loads((PROJECT / "work/content.json").read_text())
    doors = {m["node"][5:]: m["door_id"] for m in json.loads((PROJECT / "work/doors.json").read_text())}
    tops = door_tops(PROJECT / "work/runtime")
    pads = {p["anchor"]: p for p in content["pads"]}
    gate = [doors[n] for n in ("Outerdoor0", "Outerdoor1", "Innerdoor0", "Innerdoor1")]

    def walk(y0, seconds, y1):
        """A walk north along the keep's axis (x 0) from y0, expected to stop at y1."""
        return {"movement_segment": {
            "input": "forward", "seconds": seconds, "actor_collision": False, "actor_ai": False,
            "start": {"map": MAP, "x": 0, "y": y0, "z": -491, "yaw_degrees": 90, "pitch": 0},
            "expect_stop": {"map": MAP, "x": 0, "y": y1, "z": -491, "yaw_degrees": 90, "pitch": 0},
            "loose_tolerance": True, "tolerance_xy": 80, "tolerance_z": 16}}

    # MM9 authors the outer leaves apart and the inner ones shut; a switch shuts the outer gate and opens the inner
    # one, and the next press reverses it: an airlock. The outer leaves are built shut and start open (native
    # "closed" is the shut gate).
    steps = [{"load_map": {"map": MAP}},
             {"note": {"text": "The gate is an airlock: the outer leaves stand apart, the inner ones shut. Switch0/1 "
                               "are hidden until SwitchLever0 slides the lever panels and locked until PanelLever."}},
             walk(9300, 2.0, 10452),
             {"execute_event": {"id": 73}}, {"advance_runtime": {"seconds": 1}},
             {"assert": {"mechanism": {"id": gate[2], "state": "closed"}}},
             {"execute_event": {"id": 71}}, {"execute_event": {"id": 72}}, {"advance_runtime": {"seconds": 2}},
             {"assert": {"mechanism": {"id": doors["LeverPanel"], "state": "open"}}},
             {"assert": {"mechanism": {"id": doors["SwitchLever0"], "state": "open"}}},
             {"execute_event": {"id": 73}}, {"advance_runtime": {"seconds": 7}}]
    steps += [{"assert": {"mechanism": {"id": d, "state": state}}}
              for d, state in zip(gate, ("closed", "closed", "open", "open"))]
    steps += [{"note": {"text": "Now the outer gate is shut and the inner one open: from the vestibule the party walks "
                                "on north; from the south it stops at the outer gate."}},
              walk(9950, 1.25, 10910), walk(9300, 1.0, 9630)]

    plate = doors["ShooterPlate8"]
    others = [tops[doors[n]][:2] for n in ("ShooterPlate5", "ShooterPlate6", "ShooterPlate7")]
    steps += [{"note": {"text": "ShooterPlate8 sinks under the party and Shooter8 fires a fire bolt (event 63; ShotsFired counts the bolts the engine accepted)."}},
              walk_onto(floors, tops[plate], "ShooterPlate8", distance=320, avoid=others),
              {"assert": {"mechanism": {"id": plate, "state": "open"}}},
              {"assert": {"state_dump_named_map_var": {"name": "ShotsFired", "value": 1}}},
              {"advance_runtime": {"seconds": 4}},
              {"assert": {"mechanism": {"id": plate, "state": "closed"}}}]

    crusher, crush_plate = doors["CeilingCrush1"], doors["CeilingCrushPlate1"]
    steps += [{"note": {"text": "CeilingCrushPlate1: CeilingCrush1 drops and strikes the party on its plate (event 66, CrushHits; the headless party regenerates the 20 at once), then rises after 3 s."}},
              walk_onto(floors, tops[crush_plate], "CeilingCrushPlate1", distance=220),
              {"advance_runtime": {"seconds": 1.2}},
              {"assert": {"mechanism": {"id": crusher, "state": "open"}}},
              {"assert": {"state_dump_named_map_var": {"name": "CrushHits", "value": 1}}},
              {"advance_runtime": {"seconds": 6}},
              {"assert": {"mechanism": {"id": crusher, "state": "closed"}}}]

    cage = pads["TriggerNagateBust"]
    steps += [{"note": {"text": "TriggerNagateBust: CritterBreakOut0 sinks and the caged Nagate Hatchlings get out."}},
              {"assert": {"mechanism": {"id": doors["CritterBreakOut0"], "state": "closed"}}},
              walk_onto(floors, floor_of(cage), "TriggerNagateBust", distance=200),
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": doors["CritterBreakOut0"], "state": "open"}}}]

    closet = pads["TriggerClosetGate1"]
    steps += [{"note": {"text": "TriggerClosetGate1 starts ImpGateSpawner1: an Imp (9079) appears at its gate (5 placed Imps count; the hidden Giant Imp does not)."}},
              {"assert": {"actor_count": {"monster_id": 9079, "max": 5}}},
              walk_onto(floors, floor_of(closet), "TriggerClosetGate1", distance=200),
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"state_dump_named_map_var": {"name": "ImpsSummoned", "value": 1}}},
              {"assert": {"actor_count": {"monster_id": 9079, "min": 6}}}]
    return {"id": "mm9r.anskramkeep_scripted", "title": "Anskram Keep (native BLV): MM9's gate, plates, crushers, "
            "cages and Imp gates as native events", "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": steps}


def rotating_scenario() -> dict:
    """MM9's swinging doors, the first pivot trap, its ladder and hatch (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md)."""
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    doors = {m["node"][5:]: m["door_id"] for m in movers}
    event_of = {m["node"][5:]: m["event"] for m in movers}
    scene = json.loads((PROJECT / "work/runtime/anskramkeep.scene.yml").read_text())
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder4")
    pit_z, floor_z = ladder["bottom"][2], -491
    leaves = [doors["DoubleDoorL15"], doors["DoubleDoorR15"]]
    trap, hatch = doors["PivotWallTrap1"], doors["TrapExitDoor1"]

    def walk(x0, y0, z0, yaw, seconds, x1, y1, z1, xy=60, tz=16, input_="forward"):
        return {"movement_segment": {
            "input": input_, "seconds": seconds, "actor_collision": False, "actor_ai": False,
            "start": {"map": MAP, "x": x0, "y": y0, "z": z0, "yaw_degrees": yaw, "pitch": 0},
            "expect_stop": {"map": MAP, "x": x1, "y": y1, "z": z1, "yaw_degrees": yaw, "pitch": 0},
            "loose_tolerance": True, "tolerance_xy": xy, "tolerance_z": tz}}

    # Native positions: LT (x, y, z) * 2.56 = (x, z, y). The trap's trigger half is around LT (1344, 708).
    on_trap = [int(round(1344 * convert.SCALE)), int(round(708 * convert.SCALE)), floor_z]
    foot = [int(round(ladder["bottom"][0] + 41)), int(round(ladder["bottom"][1])), int(round(pit_z))]
    top = [int(round(v)) for v in ladder["top_exit"]]
    steps = [{"load_map": {"map": MAP}},
             {"note": {"text": "DoubleDoor15: shut, a leaf stops the party; a click swings both leaves away from it."}},
             {"assert": {"mechanism": {"id": leaves[0], "state": "closed"}}},
             walk(0, 102, -491, 90, 1.5, 0, 420, -491),
             {"execute_event": {"id": event_of["DoubleDoorL15"]}},
             {"advance_runtime": {"seconds": 2}}]
    steps += [{"assert": {"mechanism": {"id": leaf, "state": "open"}}} for leaf in leaves]
    steps += [walk(0, 102, -491, 90, 1.5, 0, 1254, -491),
              {"note": {"text": "The leaves shut themselves after 7 s (MM9 CloseWaitTime)."}},
              {"advance_runtime": {"seconds": 9}}]
    steps += [{"assert": {"mechanism": {"id": leaf, "state": "closed"}}} for leaf in leaves]
    steps += [{"note": {"text": "With the party in the doorway the closing leaves reverse (MM9 ReopenOnContact)."}},
              {"execute_event": {"id": event_of["DoubleDoorL15"]}},
              {"advance_runtime": {"seconds": 2}},
              walk(0, 490, -491, 90, 0.3, 0, 490, -491, xy=20, input_="none"),
              {"advance_runtime": {"seconds": 7.0}},
              {"advance_runtime": {"seconds": 3.0}}]
    steps += [{"assert": {"mechanism": {"id": leaf, "state": "open"}}} for leaf in leaves]
    steps += [{"note": {"text": "PivotWallTrap1: stepping on its floor tips the party into the pit (MM9 90 degrees at "
                                "100/s), onto the spike pit."}},
              {"assert": {"mechanism": {"id": trap, "state": "closed"}}},
              walk(on_trap[0], on_trap[1], on_trap[2] + 2, 0, 3.0, on_trap[0], on_trap[1], int(round(pit_z)),
                   xy=260, tz=100, input_="none"),
              {"assert": {"mechanism": {"id": trap, "state": "open"}}},
              {"assert": {"state_dump_named_map_var": {"name": "SpikeHits", "value": 1}}},
              {"note": {"text": "The trap turns back after 5 s."}},
              {"advance_runtime": {"seconds": 8}},
              {"assert": {"mechanism": {"id": trap, "state": "closed"}}},
              {"note": {"text": "Ladder4: with the hatch shut the party climbs until its head meets it."}},
              walk(foot[0] + 40, foot[1], foot[2], 180, 3.0, foot[0], foot[1], -512 - 160, xy=60, tz=40),
              {"note": {"text": "TrapExitDoor1 opens on its click; the party climbs out beside it."}},
              {"execute_event": {"id": event_of["TrapExitDoor1"]}},
              {"advance_runtime": {"seconds": 2}},
              {"assert": {"mechanism": {"id": hatch, "state": "open"}}},
              walk(foot[0] + 40, foot[1], foot[2], 180, 4.0, top[0], top[1], top[2], xy=400, tz=16),
              {"note": {"text": "The hatch shuts itself after 5 s."}},
              {"advance_runtime": {"seconds": 7}},
              {"assert": {"mechanism": {"id": hatch, "state": "closed"}}},
              {"note": {"text": "A save in the middle of a swing keeps the leaves' pose and side: they finish opening."}},
              {"load_map": {"map": MAP}},
              walk(0, 102, -491, 90, 0.2, 0, 102 + 150, -491, xy=200),
              {"execute_event": {"id": event_of["DoubleDoorL15"]}},
              {"advance_runtime": {"seconds": 0.5}},
              {"save_game": "rotating_swing"},
              {"load_game": "rotating_swing"},
              {"advance_runtime": {"seconds": 2}}]
    steps += [{"assert": {"mechanism": {"id": leaf, "state": "open"}}} for leaf in leaves]
    steps += [walk(0, 102, -491, 90, 1.5, 0, 1254, -491)]
    return {"id": "mm9r.anskramkeep_rotating", "title": "Anskram Keep (native BLV): swinging doors, a pivot trap, a "
            "ladder and a hatch", "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"],
            "steps": steps}


def main() -> int:
    floors = Floors()
    for name, document in (("scenario_chests.yml", chests_scenario(floors)),
                           ("scenario_scripted.yml", scripted_scenario(floors)),
                           ("scenario_rotating.yml", rotating_scenario())):
        path = PROJECT / name
        path.write_text(f"# Written by make_scenarios.py from the built map; rerun it after convert.py.\n"
                        + yaml.safe_dump(document, sort_keys=False, width=120))
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
