#!/usr/bin/env python3
"""
Write the Yanmir's Fort scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json, work/runtime):

    scenario_doors_exits.yml   the west gate (TPS1) raises its MM9 exit trigger; a shut double door stops the party,
                               opens on a click and is walked through; the teleporter doors stay locked without
                               Yanmir's key; the key (a real click) unlocks them, they open and the teleporter (TPS2)
                               raises its exit; a cage opens with the key; the secret wall opens and stays open
    scenario_chests.yml        the eleven chests open from in front of their models (interact)
    scenario_scripted.yml      the perception hints, Yanmir asleep until SquishTrigger0 and immune to the party's
                               blows, the spawners (a touch volume and a Yeti's death), a Lobbercicle's respawn, the
                               six supports broken (one by 1 point of damage, five by clicks) in the basement, Yanmir lured onto the trap hall's floor
                               (the floor gives way, key 173 and the experience, Yanmir gone), the Forest Giants on
                               the next load, a child sent to the teleporter, a fall through the floor to Frosgard City

    python3 level_generation/projects/mm9r_yanmirsfort/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_yanmirsfort/scenario_$s.yml --scenario-no-color; done
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

MAP = "yanmirsfort.blv"
EXIT_TPS1, EXIT_TPS2 = 777, 599          # DAT object indices (map_transitions.txt rows of this map)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.yanmirsfort_{name}", "title": title, "world": "mm9", "mode": "faithful",
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
    scripted = report["scripted"]
    boxes, actors = scripted["boxes"], scripted["actors"]
    group_doors, group_event = {}, {}
    for m in movers:
        group_doors.setdefault(m["group"], []).append(m["door_id"])
        group_event[m["group"]] = m.get("event")
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(PROJECT / "work/runtime" / MAP)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    faces = {f["index"]: f for f in blv["faces"]}
    door_faces = {d["door_id"]: d["face_ids"] for d in scene["initial_state"]["doors"]}
    decorations = {d["anchor"]: d for d in content["decorations"]}
    placed = scene["initial_state"]["actors"]
    monsters = [(a["position"]["x"], a["position"]["y"]) for a in placed]

    def centre(group):
        points = np.concatenate([vertices[faces[f]["vertex_indices"]] for d in group_doors[group]
                                 for f in door_faces[d]])
        return (points.min(0) + points.max(0)) / 2

    def state(name, value):
        return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}

    def mech(group, value, k=0):
        return {"assert": {"mechanism": {"id": group_doors[group][k], "state": value}}}

    def face_point(target, stand, height=0.0, z_from=None):
        x, y = stand
        z = floors.z(x, y, target[2] + 120 if z_from is None else z_from)
        if z is None:
            raise SystemExit(f"no floor at {stand}")
        look = math.atan2(target[1] - y, target[0] - x)
        pitch = math.atan2(target[2] + height - (z + scenarios.EYE), math.dist((x, y), target[:2]))
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}

    def click_door(group, side, distance=130, height=0.0, z_from=None):
        c = centre(group)
        stand = (c[0] + side[0] * distance, c[1] + side[1] * distance)
        return [face_point(c, stand, height, z_from), {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]

    def click_decoration(anchor, distances=(90, 120, 160), height=25, max_drop=120, avoid=None):
        d = decorations[anchor]
        x, y, z = d["position"]
        yaw = props[anchor]["yaw_degrees"] if anchor in props else 0
        return [scenarios.look_at(floors, MAP, (x, y, z), yaw, distances=distances, height=height, max_drop=max_drop,
                                  avoid=monsters if avoid is None else avoid),
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

    def walk(stand, yaw, seconds, stop, xy=90, z_tol=40, z_from=1200):
        x, y = stand
        z = floors.z(x, y, z_from)
        sx, sy = stop
        return scenarios.movement(MAP, (x, y, z + 1), yaw, seconds, (sx, sy, z + 1), xy, z_tol)

    def lt(x, y, z):
        return project.native([x, y, z])

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Yanmir's Fort (native BLV) - the gates, a double door, the teleporter doors, a cage, "
                                "the secret wall")
    steps = doc["steps"]
    steps += [{"note": {"text": "TPS1 (DAT object 777): the west gate back to Frosgard, just west of the start."}},
              scenarios.movement(MAP, start, 180, 1.0, (start[0] - 400, start[1], start[2]), 500, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_TPS1}}},
              {"load_map": {"map": MAP}}]
    c = centre("DPortal18")
    south = (c[0], c[1] - 300)
    steps += [{"note": {"text": "Door1a8/Door1b8 (DPortal18, north of the entrance corridor) is shut and stops the party."}},
              mech("DPortal18", "closed"),
              walk(south, 90, 1.0, (c[0], c[1] - 60), 90, z_from=c[2] + 100),
              {"note": {"text": "A click on the leaves opens the pair; the party walks through to the north."}},
              *click_door("DPortal18", (0, -1)),
              {"advance_runtime": {"seconds": 1.6}},           # 90 degrees at 60/s; CloseWaitTime 1 s
              mech("DPortal18", "open"), mech("DPortal18", "open", 1),
              walk(south, 90, 1.0, (c[0], c[1] + 300), 200, z_from=c[2] + 100)]
    t = centre("DPortal37")
    steps += [{"note": {"text": "The teleporter doors (DPortal37, Locked) stay shut without Yanmir's key."}},
              *click_door("DPortal37", (0, -1), z_from=t[2] + 100),
              {"advance_runtime": {"seconds": 2}},
              mech("DPortal37", "closed"),
              {"note": {"text": "RotatingDoor64 (a cage in the children's room, Locked) stays shut too."}},
              *click_door("RotatingDoor64", (-1, 0), distance=110, z_from=t[2] + 100),
              {"advance_runtime": {"seconds": 2}},
              mech("RotatingDoor64", "closed")]
    if any(i["source_name"] == "Yanmir'sKey" for i in scene.get("world_items", [])):
        steps += [{"note": {"text": "Yanmir's key (YanmirKey.scr), a world item, picked up: item 570 and key 7001."}},
                  *scenarios.pick_up_steps(floors, MAP, scene, "Yanmir'sKey", distances=(70, 90, 110, 140)),
                  {"assert": {"qbit_set": [90000 + convert.KEY_CAGES]}},
                  {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_KEY, "count": 1}]}}]
    else:
        steps += [{"console": {"line": f"qbit set {90000 + convert.KEY_CAGES}"}}]
    steps += [{"note": {"text": "With the key the cage and the teleporter doors open; the party walks into TPS2."}},
              *click_door("RotatingDoor64", (-1, 0), distance=110, z_from=t[2] + 100),
              {"advance_runtime": {"seconds": 3}},
              mech("RotatingDoor64", "open"),
              *click_door("DPortal37", (0, -1), z_from=t[2] + 100),
              {"advance_runtime": {"seconds": 3}},
              mech("DPortal37", "open"),
              walk((t[0], t[1] - 200), 90, 2.0, (t[0], t[1] + 500), 600, 200, z_from=t[2] + 100),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_TPS2}}},
              {"load_map": {"map": MAP}}]
    s = centre("Secretdoor")
    steps += [{"note": {"text": "The secret wall (Secretdoor) opens on a click and stays open (OpenTrigger lock)."}},
              mech("Secretdoor", "closed"),
              *click_door("Secretdoor", (1, 0), distance=150, z_from=s[2] + 100),
              {"advance_runtime": {"seconds": 6}},
              state("SecretOpen", 1),
              mech("Secretdoor", "open"),
              {"advance_runtime": {"seconds": 20}},
              mech("Secretdoor", "open")]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    if props:
        doc = header("chests", "Yanmir's Fort (native BLV) - the eleven MM9 treasure chests open")
        doc["steps"] += [{"note": {"text": "The secret wall is opened first (the treasury beyond it)."}},
                         {"execute_event": {"id": convert.EV_SECRET}}, {"advance_runtime": {"seconds": 6}}]
        for chest in content["chests"]:
            entry = props[chest["anchor"]]
            doc["steps"] += [scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                               distances=(110, 150, 190, 230), avoid=monsters),
                             {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                             {"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                             {"press_action": {"action": "cancel_dialog"}}]
        scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")
    else:
        print("note: props.json is missing: no chest scenario")

    # --- scripted objects -----------------------------------------------------------------------------------------
    doc = header("scripted", "Yanmir's Fort (native BLV) - Yanmir, the trap, spawners, children, giants")
    steps = doc["steps"]
    yanmir = actors["Yanmir0"]
    yanmir_hp = next(a["hp"] for a in placed if a["actor_index"] == yanmir)
    steps += [{"note": {"text": "PerceptionBrush0/1 show at Perception 10 and not below (checked every 3 s)."}},
              {"console": {"line": "skill set Perception 1 B"}},
              {"advance_runtime": {"seconds": 4}},
              state("PerceptiveParty", 0),
              {"console": {"line": "skill set Perception 10 E"}},
              {"advance_runtime": {"seconds": 4}},
              state("PerceptiveParty", 1)]
    steps += [{"note": {"text": "Yanmir sleeps (YanmirBase.scr DisableWandering) until SquishTrigger0, between the "
                                "entrance and his hall."}},
              state("YanmirAwake", 0),
              in_box("SquishTrigger0", dx=-400),
              {"advance_runtime": {"seconds": 0.5}},
              in_box("SquishTrigger0"),
              {"advance_runtime": {"seconds": 0.5}},
              state("YanmirAwake", 1),
              {"note": {"text": "Nothing hurts Yanmir (YanmirBase.scr :Reset CanDamage FALSE)."}},
              {"party_attack": {"actor_index": yanmir, "count": 5}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"actor_visible": {"actor_index": yanmir, "current_hp": yanmir_hp}}}]
    steps += [{"note": {"text": "Trigger6 sends Spawner0's Yeti (once)."}},
              in_box("Trigger6", dy=-400),
              {"advance_runtime": {"seconds": 0.5}},
              in_box("Trigger6"),
              {"advance_runtime": {"seconds": 0.5}},
              state("SpawnedSpawner0", 1)]
    yeti = next(int(k) for k, v in scripted["death_spawn"].items() if v == "Spawner2")
    steps += [{"note": {"text": "A Yeti whose DeathTriggerTarget is Spawner2 dies: Spawner2 sends another."}},
              {"damage_actor": {"actor_index": yeti, "amount": 100000}},
              {"advance_runtime": {"seconds": 0.5}},
              state("SpawnedSpawner2", 1)]
    bug = next(int(k) for k, v in scripted["bug_respawn"].items() if v == "Respawn0")
    far = lt(-3100, 100, -960)
    steps += [{"note": {"text": "An Ice Lobbercicle of Respawn0 dies: it comes back 10-15 minutes later, the party away."}},
              {"damage_actor": {"actor_index": bug, "amount": 100000}},
              {"advance_runtime": {"seconds": 0.5}},
              state("BugsQueued", 1),
              pose(far[0], far[1], floors.z(far[0], far[1], far[2] + 200) + 1),
              {"advance_runtime": {"seconds": 920}},
              state("BugsRespawned", 1)]
    # The six supports in the basement under the trap hall, each clicked from in front. The party stands on Planks0
    # (a mover at -376 LT: not in the static floors).
    plank_z = -376 * SCALE

    def plank_point(target, stand):
        x, y = stand
        look = math.atan2(target[1] - y, target[0] - x)
        pitch = math.atan2(target[2] - (plank_z + scenarios.EYE), math.dist((x, y), target[:2]))
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(plank_z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}

    # The supports are scene destructibles (`motion: break`): the first by a weapon's damage (the console's blow, as a
    # hit), the others by a real click (the shared killing blow, or the hint round it: the same event)
    breakable = {d["name"]: d for d in scene.get("destructibles", [])}
    for k, name in enumerate(convert.SUPPORTS):
        c = np.array(breakable[name]["center"], float)
        stand = (c[0], c[1] + 160 if k in (0, 1) else c[1] - 160)
        if k == 0:
            steps += [{"note": {"text": f"{name}: one point of damage (HitPoints 1) breaks the support."}},
                      {"console": {"line": f"destructible {breakable[name]['id']} damage 1", "expect_contains": "damage"}}]
        else:
            steps += [{"note": {"text": f"{name}: a click breaks the support."}},
                      plank_point(c, stand),
                      {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]
        steps += [{"advance_runtime": {"seconds": 0.5}}, state(f"Support{k}", 1)]
    steps += [state("TrapArmed", 1)]
    # Lure Yanmir: the party is seen in his hall, then stands south of the trap's floor; the doors on his way open
    # (his door kicks); he walks over TriggerYanmirTrap.
    hall = lt(-700, 100, -900)
    steps += [{"note": {"text": "Yanmir sees the party in his hall; the party backs away in his sight, through the hall's "
                                "south door and over the trap hall's floor to its south end; Yanmir follows onto the "
                                "trap, which gives way (YanmirTrap.scr, YanmirBase.scr :OnTimeToDie)."}},
              pose(hall[0], hall[1], floors.z(hall[0], hall[1], hall[2] + 200) + 1, math.pi),
              {"advance_runtime": {"seconds": 3}},
              {"execute_event": {"id": group_event["DPortal19"]}}]
    for x, z in ((0, -1500), (192, -1900), (192, -2400), (192, -2900), (192, -3400), (192, -3900), (192, -4230)):
        p = lt(x, 0, z)
        floor = floors.z(p[0], p[1], 300)
        if floor is None or floor < -500:
            floor = 0.0                                   # the trap hall's floor (a mover)
        steps += [pose(p[0], p[1], floor + 1, math.pi / 2),
                  {"advance_runtime": {"seconds": 4}},
                  {"assert": {"actor_visible": {"actor_index": yanmir, "report_state": True}}}]
    steps += [{"advance_runtime": {"seconds": 20}},
              {"assert": {"actor_visible": {"actor_index": yanmir, "report_state": True}}},
              state("TrapFired", 1),
              {"advance_runtime": {"seconds": 4}},
              state("YanmirGone", 1),
              {"assert": {"qbit_set": [90000 + convert.KEY_FREE]}},
              {"assert": {"actor_visible": {"actor_index": yanmir, "hidden": True}}},
              mech("TrapFloor", "open")]
    giant = scripted["giants"][0]
    steps += [{"note": {"text": "The next load: the Forest Giants are there (YanmirHidden.scr :InitYanmirHidden)."}},
              {"assert": {"actor_visible": {"actor_index": giant, "hidden": True}}},
              {"load_map": {"map": MAP}},
              {"advance_runtime": {"seconds": 1}},
              state("GiantsOut", 1),
              {"assert": {"actor_visible": {"actor_index": giant, "hidden": False}}}]
    name, _, child = scripted["children"][0]
    a = next(x for x in placed if x["actor_index"] == child)
    cx, cy, cz = a["position"]["x"], a["position"]["y"], a["position"]["z"]
    others = [m for m in monsters if math.dist(m, (cx, cy)) > 1]
    steps += [{"note": {"text": f"{name} (YanmirChild.scr): with key 7001 a click sends the child to the teleporter."}},
              {"console": {"line": f"qbit set {90000 + convert.KEY_CAGES}"}},
              {"execute_event": {"id": convert.EV_CAGE + 3}},
              {"advance_runtime": {"seconds": 3}},
              scenarios.look_at(floors, MAP, (cx, cy, cz), 0, distances=(110, 150, 190), height=60, avoid=others),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
              {"advance_runtime": {"seconds": 0.5}},
              state(f"Escaped{name}", 1),
              {"assert": {"actor_visible": {"actor_index": child, "hidden": True}}}]
    fallen = lt(192, -399, -3200)
    steps += [{"note": {"text": "A party that falls through the trap hall's floor (onto the fallen floor, 399 LT down) "
                                "goes to Frosgard City (EndOfWorldTrigger -> PlayerExit)."}},
              {"advance_runtime": {"seconds": 3}},
              mech("TrapFloor", "open"),
              pose(fallen[0], fallen[1], fallen[2] + 2),
              {"advance_runtime": {"seconds": 1}},
              state("FellToCity", 1)]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
