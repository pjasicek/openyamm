#!/usr/bin/env python3
"""
Write the Thousand Terrors scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
the scene, the BLV, props.json):

    scenario_doors_exits.yml   both exits raise their transitions (ExitTrigger0 by a walk from the start); a shut door
                               stops a walk, opens on a real click and is walked through; every clickable door group
                               opens on a real click (or its event where no floor stands in front of it)
    scenario_chests.yml        the fourteen chests open by real clicks
    scenario_scripted.yml      the button puzzle (trap volume, a real click on a block, MM9's lights-out rule, the
                               solve hides the wall, the pull resets), the gear lift, the hidden button, lever 17's trap
                               doors, a shooter plate, the demon statues' spawns, a death trigger, the chess squares,
                               Njam's taunt with key 108, the win switch with and without key 108, the genie lamp and
                               the chess note by real clicks

    python3 level_generation/projects/mm9r_1000terrors/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_1000terrors/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import ROOT, Project  # noqa: E402
import convert  # noqa: E402

MAP = "1000terrors.blv"
PROBE = {} if "--probe" in sys.argv else None
PROBE_ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
CLICKS_PATH = PROJECT / "work/click_poses.json"
CLICKS = json.loads(CLICKS_PATH.read_text()) if CLICKS_PATH.exists() and PROBE is None else {}
EYE = 160


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.1000terrors_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def pose(x, y, z, yaw_radians, pitch=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                         "yaw": round(yaw_radians, 4), "pitch": round(pitch, 4)}}


def var(name: str, value: int) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def wait(seconds: float) -> dict:
    return {"advance_runtime": {"seconds": seconds}}


def lights_out_solution() -> list[int]:
    """The presses that turn the 4 x 4 wall from all out to all in (ButtonPad.scr: a press toggles the block and its
    four neighbours), by Gaussian elimination over GF(2)."""
    n = 16
    a = np.zeros((n, n + 1), np.uint8)
    for k in range(n):
        col, row = k % 4, k // 4
        for j in [k] + ([k - 1] if col > 0 else []) + ([k + 1] if col < 3 else []) + \
                ([k - 4] if row > 0 else []) + ([k + 4] if row < 3 else []):
            a[j, k] = 1
        a[k, n] = 1
    r = 0
    pivots = []
    for c in range(n):
        p = next((i for i in range(r, n) if a[i, c]), None)
        if p is None:
            continue
        a[[r, p]] = a[[p, r]]
        for i in range(n):
            if i != r and a[i, c]:
                a[i] ^= a[r]
        pivots.append(c)
        r += 1
    x = [0] * n
    for i, c in enumerate(pivots):
        x[c] = int(a[i, n])
    return [k for k in range(n) if x[k]]


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    global SOURCE
    from dungeon.source import Source
    SOURCE = Source(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = yaml.load((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    scripted = report["scripted"]
    boxes, points, actors = scripted["boxes"], scripted["points"], scripted["actors"]
    actor_pos = [(a["position"]["x"], a["position"]["y"]) for a in scene["initial_state"]["actors"]]
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / f"work/runtime/{MAP}")["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    faces = {f["index"]: f for f in blv["faces"]}
    door_faces = {d["door_id"]: d["face_ids"] for d in scene["initial_state"]["doors"]}

    def door_centre(door_id) -> np.ndarray:
        pts = np.concatenate([vertices[np.asarray(faces[f]["vertex_indices"])] for f in door_faces[door_id]])
        return (pts.min(0) + pts.max(0)) / 2

    groups = {}
    for m in movers:
        groups.setdefault(m["group"], []).append(m)

    def open_time(m) -> float:
        if m["motion"] == "rotate":       # MM9's Speed: degrees per second
            speed = float(SOURCE.properties(m["dat_models"][0]).get("Speed") or 30)
            return abs(m["mover"]["rotation"]["open_degrees"]) / max(1.0, speed) + 1.6
        return m["move_length"] / max(1, m["open_speed"]) + 0.6

    def click_door(group: str, steps: list, wait_open=True) -> None:
        """A real click on the group's first leaf from a floor in front of it; its event if no floor stands there."""
        m = groups[group][0]
        pts = np.concatenate([vertices[np.asarray(faces[f]["vertex_indices"])] for f in door_faces[m["door_id"]]])
        c = (pts.min(0) + pts.max(0)) / 2
        size = pts.max(0) - pts.min(0)
        facing = -90 if size[0] < size[1] else 0          # stand off the leaf's thin axis, not along its plane
        target = (c[0], c[1], min(c[2], pts.min(0)[2] + 60))
        small = size.max() < 90                           # levers, pulls, buttons: aim at the middle, stand close
        if small:
            target = tuple(c)
        if PROBE is not None:
            if PROBE_ONLY is None or group in PROBE_ONLY:
                PROBE[group] = candidates(target, facing, (70, 100, 50, 130) if small else (130, 90, 180),
                                          (0, 10, -10) if small else (0, 30))
            return
        if group in CLICKS and CLICKS[group] is not None:
            steps += [CLICKS[group], wait(0.2), {"press_interact": {}}]
        elif group in CLICKS:
            steps += [{"note": {"text": f"{group}: no click pose picks it headless (work/click_poses.json): its event"}},
                      {"execute_event": {"id": m["event"]}}]
        else:
            raise SystemExit(f"{group}: not probed; run make_scenarios.py --probe")
        # 1500: since the path planner change of 2026-10-31 the crypt's Terrors (1 174-1 418 from LowerDoor17) reach a door
        # the party clicks and hold a leaf in its swing
        near = [a for a in actor_pos if math.dist(a, c[:2]) < 1500]
        if wait_open and near:
            # a monster stands by the door: its body can hold a leaf in the swing, so the click is proved by the
            # leaf starting to move
            steps += [wait(0.3), {"assert": {"mechanism": {"id": m["door_id"], "state": "opening"}}}]
            return
        if wait_open:
            steps.append(wait(max(open_time(x) for x in groups[group])))
            # the first leaf: a monster standing in a swing can hold the other leaf half open (LowerDoor15-18's
            # Desert Terrors), which says nothing about the door
            steps.append({"assert": {"mechanism": {"id": groups[group][0]["door_id"], "state": "open"}}})

    def candidates(target, facing, distances=(130, 90, 180), heights=(0, 30)) -> list:
        """Poses on both sides of the leaf's thin axis at 130, 90 and 180 units, looking at its lower middle and a
        little higher (one floor query per spot)."""
        out = []
        cx, cy, cz = target
        axis = (1.0, 0.0) if facing == -90 else (0.0, 1.0)
        for distance in distances:
            for side in (1, -1):
                x, y = cx + side * axis[0] * distance, cy + side * axis[1] * distance
                z = floors.z(x, y, cz + 200)
                if z is None or abs(z - cz) > 250:
                    continue
                for height in heights:
                    pitch = math.atan2(cz + height - (z + EYE), distance)
                    out.append(pose(x, y, z, math.atan2(cy - y, cx - x), pitch))
        return out[:12]

    def stand_in(box) -> dict:
        (x0, y0, z0), (x1, y1, z1) = box
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
        z = floors.z(x, y, z1 + 10)
        return pose(x, y, z if z is not None else z0, 0)

    # --- doors and exits ----------------------------------------------------------------------------------------
    doc = header("doors_exits", "Thousand Terrors (native BLV) - the two exits, a shut door stops the party, every "
                                "door group opens on a real click")
    steps = doc["steps"]
    start = report["starts"][0]["position"]
    # the map's exit rows from the review root's table (build_report's list holds only the rows a build changed)
    rows = (ROOT / "output/mm9_rework/assets_dev/worlds/mm9/data_tables/map_transitions.txt").read_text().splitlines()
    head = rows[0].split("\t")
    exits = {}
    for row in rows[1:]:
        cells = dict(zip(head, row.split("\t")))
        if cells.get("SourceMapFile") == MAP:
            exits[cells["SourceName"]] = {"centre": [cells["CenterX"], cells["CenterY"], cells["CenterZ"]]}
    e0 = [int(v) for v in exits["ExitTrigger0"]["centre"]]
    yaw = math.degrees(math.atan2(e0[1] - start[1], e0[0] - start[0]))
    steps += [{"note": {"text": "ExitTrigger0 (to Arslegard City): a walk from StartPoint0 into the exit volume."}},
              scenarios.movement(MAP, start, yaw, 1.0, e0[:2] + [start[2]], 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": 442}}},
              {"load_map": {"map": MAP}}]
    # LowerDoor3/4 (LowerPortal2): shut, it stops a walk; a click opens it; the party walks through.
    portals = {p["name"]: p for p in report["portals"]}
    cx, cy, cz = portals["LowerPortal2"]["centre_native"]
    floor = floors.z(cx, cy - 300, cz)
    ids = [m["door_id"] for m in groups["LowerDoor3"]]
    steps += [{"note": {"text": "LowerDoor3/4: shut, they stop a walk; a click opens both leaves; the party walks "
                                "through LowerPortal2."}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in ids],
              scenarios.movement(MAP, (cx, cy - 300, floor + 1), 90, 1.0, (cx, cy - 60, floor + 1), 60, 20),
              pose(cx, cy - 200, floor, math.pi / 2, math.atan2(cz - (floor + EYE), 200)),
              wait(0.2), {"press_interact": {}}, wait(3.5),
              *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in ids],
              scenarios.movement(MAP, (cx, cy - 300, floor + 1), 90, 0.8, (cx, cy + 300, floor + 1), 140, 20),
              {"load_map": {"map": MAP}}, wait(12)]
    own = set(convert.ThousandTerrors.mover_events)
    plain = sorted(g for g, ms in groups.items() if ms[0]["event"] and g not in own and g != "LowerDoor3")
    for group in plain:
        steps.append({"note": {"text": f"{group}: a click opens it."}})
        click_door(group, steps)
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ----------------------------------------------------------------------------------------------------
    doc = header("chests", "Thousand Terrors (native BLV) - the fourteen MM9 treasure chests open by a click")
    doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted ----------------------------------------------------------------------------------------------------
    doc = header("scripted", "Thousand Terrors (native BLV) - button puzzle, gear lift, hidden button, trap doors, "
                             "shooter plate, demon statues, death trigger, chess, Njam's taunt, the win switch, lamp, note")
    steps = doc["steps"]
    # StairGate0 (convert.py EV_STAIR_GATE0, DoorLock.scr "600; 1"): a real click from the landing opens it; a hostile
    # monster beside it pushes it open (MM9's AITriggerable, the map poll). MM9 raises it slowly (Speed 10 LT/s: 12.8 s).
    # First in the scripted scenario: from a fresh load StairGate is shut (the doors scenario clicks it open).
    gate0 = groups["StairGate0"][0]["door_id"]
    gate = groups["StairGate"][0]["door_id"]
    steps += [{"note": {"text": "StairGate0: shut; a real click from the landing opens it (event 369); StairGate stays "
                                "shut."}},
              {"assert": {"mechanism": {"id": gate0, "state": "closed"}}},
              {"assert": {"mechanism": {"id": gate, "state": "closed"}}}]
    click_door("StairGate0", steps)
    cx, cy, cz = (float(v) for v in door_centre(gate0))
    land = floors.z(cx, cy + 250, cz + 200)
    # The gate shuts by itself (CloseWaitTime 10 after its rise), so its event only ever opens it: a second use keeps
    # it rising. The party steps back first: a closing StairGate0 that touches a body opens again (ReopenOnContact 1,
    # the mover's `bodies: reverse`, 2026-11-05). About 23 s on it has shut and its open flag cleared; a native
    # monster drawn to the party reaches it about 28 s on, so the spawned demon pushes it before that.
    steps += [{"assert": {"mechanism": {"id": gate, "state": "closed"}}}, var("OpenStairGate0", 1),
              {"note": {"text": "A second use of StairGate0 keeps it rising; it shuts by itself (CloseWaitTime), and a "
                                "hostile Lesser Demon beside it pushes it open."}},
              pose(cx, cy + 450, land, -math.pi / 2, 0),
              {"execute_event": {"id": convert.EV_STAIR_GATE0}}, wait(3.0),
              {"assert": {"mechanism": {"id": gate0, "state": "opening"}}}, var("OpenStairGate0", 1),
              wait(24.0),
              {"assert": {"mechanism": {"id": gate0, "state": "closed"}}}, var("OpenStairGate0", 0),
              var("Gate0ByMonster", 0)]
    steps += [pose(cx, cy + 450, land, -math.pi / 2, 0),
              {"spawn_actor": {"monster_id": 9241, "count": 1, "x": round(cx), "y": round(cy + 200), "z": round(land),
                               "group": 77}},
              wait(2.5), var("Gate0ByMonster", 1), var("OpenStairGate0", 1),
              {"assert": {"mechanism": {"id": gate0, "state": "opening"}}}]
    pad, root = "ButtonTrigger", "PuzzleDoor"
    steps += [{"note": {"text": "The button puzzle: the wall is hidden until the party steps into TriggerPuzzleDoor0 "
                                "(SetTrap); every block shut."}},
              var(f"{pad}State", 0), stand_in(boxes["TriggerPuzzleDoor0"]), wait(0.8), var(f"{pad}State", 1)]
    # a real click on block 5 from inside the treasure room (the trap side), then again to undo it
    block = groups[f"{root}5"][0]
    c = door_centre(block["door_id"])
    look = None
    for d in (160, 220, 120):
        for sx in (-1, 1):
            x, y = c[0] + sx * d, c[1]
            z = floors.z(x, y, c[2] + 40)
            if z is not None and abs(z - (c[2] - 120)) < 200:
                look = pose(x, y, z, math.atan2(0, -sx), math.atan2(c[2] - (z + EYE), d))
                break
        if look:
            break
    if look:
        steps += [{"note": {"text": "A real click on PuzzleDoor5 pushes it and its four neighbours (1, 4, 6, 9) in; a "
                                    "second click pushes them out again."}},
                  look, wait(0.2), {"press_interact": {}}, wait(0.6),
                  var(f"{pad}_5", 1), var(f"{pad}_1", 1), var(f"{pad}_4", 1), var(f"{pad}_6", 1), var(f"{pad}_9", 1),
                  var(f"{pad}_0", 0), {"press_interact": {}}, wait(0.6), var(f"{pad}_5", 0)]
    solution = lights_out_solution()
    steps.append({"note": {"text": f"MM9's lights-out rule: the presses {solution} push all sixteen in; the wall "
                                   "opens (MoveAway: hidden, untouchable)."}})
    for k in solution:
        steps += [{"execute_event": {"id": convert.EV_BLOCK_BASE + k}}, wait(0.3)]
    steps += [wait(1.5), var(f"{pad}State", 2)]
    # Pull2 resets puzzle B after its trap
    steps += [{"note": {"text": "Puzzle B: the trap, a press, then Pull2 (OpenTrigger0 ButtonTrigger0 Reset) shuts every "
                                "block again."}},
              stand_in(boxes["TriggerPuzzleDoor1"]), wait(0.8), var("ButtonTrigger0State", 1),
              {"execute_event": {"id": convert.EV_BLOCK_BASE + 16 + 5}}, wait(0.5), var("ButtonTrigger0_5", 1)]
    click_door("Pull2", steps, wait_open=False)
    steps += [wait(1.0), var("ButtonTrigger0_5", 0)]
    # the gear lift
    lift = groups["GearElevator"][0]
    steps += [{"note": {"text": "LowerLever (the gear lift's lower lever): a click sends GearElevator up 912 LT."}},
              {"assert": {"mechanism": {"id": lift["door_id"], "state": "closed"}}}]
    click_door("LowerLever", steps, wait_open=False)
    steps += [wait(open_time(lift) + 0.5), {"assert": {"mechanism": {"id": lift["door_id"], "state": "open"}}}]
    # the hidden button and the treasure doors
    steps.append({"note": {"text": "HiddenButton1: a click opens TreasureDoor and TreasureDoor0."}})
    click_door("HiddenButton1", steps, wait_open=False)
    steps.append(wait(max(open_time(m) for g in ("TreasureDoor", "TreasureDoor0") for m in groups[g])))
    steps += [{"assert": {"mechanism": {"id": m["door_id"], "state": "open"}}}
              for g in ("TreasureDoor", "TreasureDoor0") for m in groups[g]]
    # lever 17 and the trap doors
    steps.append({"note": {"text": "Rotating Lever 17: a click opens TrapDoor1/2 over the water pit."}})
    click_door("Lever17", steps, wait_open=False)
    steps.append(wait(max(open_time(m) for m in groups["TrapDoor"]) + 1))
    steps += [{"assert": {"mechanism": {"id": m["door_id"], "state": "open"}}} for m in groups["TrapDoor"]]
    # a shooter plate
    plate = groups["ShooterPlate1"][0]
    steps += [{"note": {"text": "Trigger5: stepping in sinks ShooterPlate1 and Shooter5/6 fire; it rises after 4 s."}},
              stand_in(boxes["Trigger5"]), wait(0.6), var("FiredTrigger5", 1),
              {"assert": {"mechanism": {"id": plate["door_id"], "state": "open"}}}, wait(5),
              {"assert": {"mechanism": {"id": plate["door_id"], "state": "closed"}}}]
    # the demon statues
    steps += [{"note": {"text": "Trigger18 fires SpawnTrigger0-3: four demons from the four statues, which crumble."}},
              stand_in(boxes["Trigger18"]), wait(0.6), var("SpawnSpawnLoc0", 1), var("SpawnSpawnLoc1", 1),
              var("SpawnSpawnLoc2", 1), var("SpawnSpawnLoc3", 1), var("DestroyedSpawnPiece0", 1),
              var("DestroyedSpawnPiece3", 1)]
    # the skeleton head (1000T_SkeletonHead.scr): TrigSkelHeadOn0's Go, its 1 s turn, then both eye shooters fire
    steps += [{"note": {"text": "TrigSkelHeadOn0: the skeleton head turns (1 s) and SkelHeadShooter0/1 fire five "
                                "bolts each."}},
              var("SkullGoSkeletonHead", 0), stand_in(boxes["TrigSkelHeadOn0"]), wait(1.6),
              var("SkullGoSkeletonHead", 1), wait(5.5)]
    # death trigger
    steps += [{"note": {"text": "GreaterDemon1's DeathTrigger (Spawner8 default): a Lesser Demon spawns and EndCount "
                                "counts it."}},
              {"damage_actor": {"actor_index": actors["GreaterDemon1"], "amount": 100000}}, wait(1.0), var("EndCount", 1)]
    # chess
    square = scripted["chess_squares"][0]
    lt = project.native(np.array(_square_lt(project, square), float))
    zq = floors.z(lt[0], lt[1], lt[2] + 120)
    steps += [{"note": {"text": f"Chess: BoardObj{square} is attacked by a piece; stepping onto it hurts the party."}},
              var("ChessHits", 0), pose(lt[0], lt[1], zq, 0), wait(0.6), var("ChessHits", 1),
              {"console": {"line": "cinematic list", "expect_contains": f"playing chess_capture_{square}"}},
              wait(2.5)]   # its 2 s chess_capture cinematic (ChessCamera.scr, cinematics_1000t.py)
    # Njam's taunt and the switch
    door0 = groups["Door0"]
    njam_hp = next(a["hp"] for a in scene["initial_state"]["actors"]
                   if a["actor_index"] == actors["NjamtheMeddler0"])
    steps += [{"note": {"text": "WinMan without key 108: only the lightning (SwitchThrown)."}}]
    switch = props["WinMan"]
    steps += [scenarios.look_at(floors, MAP, (switch["x"], switch["y"], switch["z"]), switch["yaw_degrees"],
                                distances=(120, 160, 90), height=40, max_drop=200, avoid=actor_pos),
              wait(0.2), {"press_interact": {}}, wait(0.3), var("SwitchThrown", 1),
              {"note": {"text": "TauntMan with key 108 (Trigger19): the cinematic njam_taunt (cinematics_1000t.py): "
                                "key 497, Door0 opens at 1 s, Njam at TauntMarker, Door0 shut, Njam gone at the end."}},
              {"console": {"line": "qbit set 90108"}},
              stand_in(boxes["Trigger19"]), wait(0.8), {"assert": {"qbit_set": [90497]}},
              {"console": {"line": "cinematic list", "expect_contains": "playing njam_taunt"}},
              wait(0.5 + max(open_time(m) for m in door0)),
              *[{"assert": {"mechanism": {"id": m["door_id"], "state": "open"}}} for m in door0],
              wait(max(0.0, 6.5 - 1.3 - max(open_time(m) for m in door0))),
              {"assert": {"actor_visible": {"actor_index": actors["NjamtheMeddler0"], "near": {
                  "x": points["TauntMarker"][0], "y": points["TauntMarker"][1], "max_distance": 300}}}},
              wait(13.0),
              {"assert": {"actor_visible": {"actor_index": actors["NjamtheMeddler0"], "hidden": True}}},
              {"note": {"text": "Njam1000.inc :Init SetPropNumber CanDamage FALSE: no blow of any kind hurts the "
                                "hunting Njam (scene mm9_can_receive_damage false)."}},
              {"lua_event": {"source": f"evt.SetMonsterBit({actors['NjamtheMeddler0']}, ActorAttribute.Invisible, 0)"}},
              {"damage_actor": {"actor_index": actors["NjamtheMeddler0"], "amount": 100000, "expect": "refused"}},
              wait(0.3),
              {"assert": {"actor_visible": {"actor_index": actors["NjamtheMeddler0"], "dead": False,
                                            "hp": njam_hp}}},
              {"lua_event": {"source": f"evt.SetMonsterBit({actors['NjamtheMeddler0']}, ActorAttribute.Invisible, 1)"}},
              var("OpenDoor0", 0),
              {"note": {"text": "WinMan with key 108: the cinematic njam_freeze_win: 234 000 experience, the monsters "
                                "gone, at its end key 109 and the level change."}},
              scenarios.look_at(floors, MAP, (switch["x"], switch["y"], switch["z"]), switch["yaw_degrees"],
                                distances=(120, 160, 90), height=40, max_drop=200, avoid=actor_pos),
              wait(0.2), {"press_interact": {}}, wait(0.5),
              {"console": {"line": "cinematic list", "expect_contains": "playing njam_freeze_win"}},
              {"assert": {"qbit_clear": [90109]}},
              {"advance_runtime": {"seconds": 37, "follow_map_move": True}},
              {"assert": {"qbit_set": [90109]}}, {"assert": {"map_arrived": {"map": "hallofthegods.blv"}}},
              {"load_map": {"map": MAP}}]
    # the genie lamp and the chess note
    e = props["Genielamp"]
    steps += [{"note": {"text": "Genielamp: a real click."}},
              scenarios.look_at(floors, MAP, (e["x"], e["y"], e["z"]), e["yaw_degrees"], distances=(80, 110, 140),
                                height=5, max_drop=200, avoid=actor_pos),
              wait(0.2), {"press_interact": {}}, wait(0.3), var("GenieUsed", 1)]
    # the note lies at the foot of the shut ToLowerTombGate (moved 16 units south by convert.py): a steep click
    e = props["ChessNote0"]
    ny = e["y"] - 16
    z = floors.z(e["x"], ny - 45, e["z"] + 60)
    steps += [{"note": {"text": "ChessNote0 (at the foot of ToLowerTombGate), a world item: picked up from the south."}},
              pose(e["x"], ny - 45, z, math.pi / 2, math.atan2(e["z"] + 1 - (z + EYE), 45)),
              wait(0.2), {"press_interact": {}}, wait(0.3),
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_CHESS_NOTE, "count": 1}]}}]
    if PROBE is not None:
        probe(PROBE)
        return 0
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")

    # --- the finale: the end demon opens the gate before the win switch ---------------------------------------------
    # EndCount.scr: the third counted spawn (GreaterDemon1 -> Spawner8, its DEATH; Oculus9 -> Spawner13; the actor
    # sending TP5 spawn) brings EndDemon.scr's Greater Demon; its death opens Door0/Door1 (EndDemon.scr :OnDeath), the
    # party walks through the gate and throws the win switch from its side of the wall.
    doc = header("finale", "Thousand Terrors (native BLV) - the end demon's death opens Door0/Door1; the party walks "
                           "through to the win switch and leaves for the Hall of the Gods")
    steps = doc["steps"]
    death = {int(i): target for i, (target, _) in scripted["death"].items()}
    counted = [i for i, target in sorted(death.items()) if target in ("Spawner8", "Spawner13", "TP5")]
    placed = len(scene["initial_state"]["actors"])
    demon = placed + len(counted)            # the three counted spawns, then the end demon (summons append)
    gate_ids = [m["door_id"] for g in ("Door0", "Door1") for m in groups[g]]
    # Door0 (LT x 3072-3296) slides 112 LT west: the way through is LT x 3184-3296; WinMan stands on the wall's north
    # face between the two doorways (LT x 3296-3680 is wall)
    gx, _, _ = project.native(np.array([3240.0, 1100.0, -3682.0]))
    _, gy, gz = door_centre(groups["Door0"][0]["door_id"])
    min_y = cinema_min_y()
    south, north = min_y - 260, min_y + 220
    zs, zn = floors.z(gx, south, gz + 150), floors.z(gx, north, gz + 150)
    steps += [{"console": {"line": "qbit set 90108"}}, {"console": {"line": "qbit set 90497"}},
              {"note": {"text": "Door0/Door1 shut: a walk north through the gate stops at it."}},
              *[{"assert": {"mechanism": {"id": i, "state": "closed"}}} for i in gate_ids],
              scenarios.movement(MAP, (gx, south, zs + 1), 90, 1.5,
                                 (gx, gy - 50, floors.z(gx, gy - 50, gz + 150) + 1), 80, 60),
              {"note": {"text": f"The three counted deaths ({counted}) bring the end demon (actor {demon})."}}]
    for i in counted:
        steps += [{"damage_actor": {"actor_index": i, "amount": 100000}}, wait(1.0)]
    steps += [var("EndCount", 3), var(f"EndDemon{demon}", 1),
              {"assert": {"mechanism": {"id": gate_ids[0], "state": "closed"}}},
              {"damage_actor": {"actor_index": demon, "amount": 1000000}}, wait(1.0),
              var("EndDemonDead", 1), wait(4.0),
              *[{"assert": {"mechanism": {"id": i, "state": "open"}}} for i in gate_ids],
              {"note": {"text": "The party walks through the open gate to the switch's side of the wall."}},
              scenarios.movement(MAP, (gx, south, zs + 1), 90, round((north - south) / scenarios.WALK, 2), (gx, north, zn + 1), 120, 60)]
    switch = props["WinMan"]
    # the party steps up to the switch (the scripted scenario's pose in front of it, on this side of the wall)
    steps += [scenarios.look_at(floors, MAP, (switch["x"], switch["y"], switch["z"]), switch["yaw_degrees"],
                                distances=(120, 160, 90), height=40, max_drop=200, avoid=actor_pos),
              wait(0.2), {"press_interact": {}}, wait(0.5),
              {"console": {"line": "cinematic list", "expect_contains": "playing njam_freeze_win"}},
              {"advance_runtime": {"seconds": 37, "follow_map_move": True}},
              {"assert": {"qbit_set": [90109]}}, {"assert": {"map_arrived": {"map": "hallofthegods.blv"}}}]
    scenarios.write(PROJECT / "scenario_finale.yml", doc, "make_scenarios.py")
    return 0


def cinema_min_y() -> float:
    """The win switch's TELP guard (cinematics_1000t.switch_min_y): the native y below which it refuses the party."""
    import cinematics_1000t as cinema
    return cinema.switch_min_y(cinema.Frame(PROJECT))


def probe(groups: dict) -> None:
    """Each click target's candidate poses as one tiny scenario each (load, pose, interact), run headless; the first
    pose whose interact picks a target is kept in work/click_poses.json (null: none did, the scenario runs the event)."""
    import subprocess
    out = json.loads(CLICKS_PATH.read_text()) if CLICKS_PATH.exists() else {}
    folder = PROJECT / "work/probe"
    folder.mkdir(exist_ok=True)
    for group, poses in groups.items():
        out[group] = None
        for k, pose_step in enumerate(poses):
            doc = header(f"probe_{group}_{k}", f"click probe {group} {k}")
            doc["steps"] += [pose_step, wait(0.2), {"press_interact": {}}]
            path = folder / "probe.yml"
            path.write_text(yaml.safe_dump(doc, sort_keys=False))
            result = subprocess.run([str(ROOT / "build/game/openyamm"), "--asset-root",
                                     str(ROOT / "output/mm9_rework/assets_dev"), "--headless-run-scenario", str(path),
                                     "--scenario-no-color"], capture_output=True, text=True, cwd=ROOT, timeout=300)
            if "Scenario passed" in result.stdout + result.stderr:
                out[group] = pose_step
                break
        print(group, "ok" if out[group] else "none", flush=True)
        CLICKS_PATH.write_text(json.dumps(out, indent=1) + "\n")


def _square_lt(project, square: int) -> list:
    from dungeon.source import Source
    return Source(project).properties(f"BoardObj{square}")["Pos"]


if __name__ == "__main__":
    sys.exit(main())
