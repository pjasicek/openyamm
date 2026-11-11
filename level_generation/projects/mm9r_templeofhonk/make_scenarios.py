#!/usr/bin/env python3
"""
Write the Temple of Honk's scenarios from the built map (work/runtime, work/doors.json, work/content.json,
work/build_report.json, props.json):

- scenario_doors_exits.yml: a closed double door stops the party, opens on its event and lets it through; DoubleDoor13
  stays shut without the Golden Honk quest (key 343) and opens with it; the exit raises its MM9 exit trigger;
- scenario_chests.yml: the five chests open from in front of their models (the two treasury chests by their events,
  behind the secret door);
- scenario_scripted.yml: the accountant's key (item 445, key 7000), the HONK buttons (locked without the key, a wrong
  order sinks the stones again, H-O-N-K opens the secret door, which shuts after 10 s; the pad inside opens it), the
  Golden Honk (item 369, key 344 on the quest) and the Honks turning hostile;
- scenario_hostility.yml: the Honks are friends until the party hurts one, then all of them are hostile;
- scenario_swim.yml (with swimming, water.swimming): the party walks into the pool and wades (15 units of water: its eye
  never goes under, as in MM9); the fish swim in the pool's water volume, their feet held over the bed (a walker stands
  on it) and their body centres under the surface (the actor reports show it).

    python3 level_generation/projects/mm9r_templeofhonk/make_scenarios.py
    for s in doors_exits chests scripted hostility swim; do ./build/game/openyamm \\
        --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario \\
        level_generation/projects/mm9r_templeofhonk/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
from dungeon import scenarios  # noqa: E402
from dungeon.source import Project  # noqa: E402

import convert  # noqa: E402

MAP = "templeofhonk.blv"
WORK = PROJECT / "work"


def load():
    doors = {m["node"][5:]: m for m in json.loads((WORK / "doors.json").read_text())}
    content = json.loads((WORK / "content.json").read_text())
    report = json.loads((WORK / "build_report.json").read_text())
    portals = {p["name"]: p for p in report["portals"]}
    return doors, content, report, portals


def walk_axis(floors, start_xy, yaw_degrees, seconds, stop_xy, z_from):
    z = floors.z(start_xy[0], start_xy[1], z_from)
    if z is None:
        raise SystemExit(f"no floor at {start_xy}")
    stop_z = floors.z(stop_xy[0], stop_xy[1], z_from) or z
    return scenarios.movement(MAP, (start_xy[0], start_xy[1], z + 1), yaw_degrees, seconds,
                              (stop_xy[0], stop_xy[1], stop_z + 1), tolerance_xy=80, tolerance_z=24)


def doors_exits(floors) -> dict:
    doors, content, report, portals = load()
    dd9, dd13 = doors["DoubleDoorL9"], doors["DoubleDoorL13"]
    x9, y9, _ = portals["DoubleDoorPortal9"]["centre_native"]
    x13, y13, _ = portals["DoubleDoorPortal13"]["centre_native"]
    start = report["starts"][0]["position"]
    exit_id = next(int(t["id"].rsplit("/", 1)[1]) for t in report["transitions"] if t["source"] == MAP)
    steps = [{"load_map": {"map": MAP}},
             {"note": {"text": "DoubleDoor9 (main hall -> north-west corridor): the rotating leaves swing away "
                               "from the party; the closed door stops it."}},
             {"assert": {"mechanism": {"id": dd9["door_id"], "state": "closed"}}},
             walk_axis(floors, (x9, y9 - 500), 90, 1.0, (x9, y9 - 40), 300),
             {"execute_event": {"id": dd9["event"]}}, {"advance_runtime": {"seconds": 3}},
             {"assert": {"mechanism": {"id": dd9["door_id"], "state": "open"}}},
             walk_axis(floors, (x9, y9 - 500), 90, 1.0, (x9, y9 + 260), 300),
             {"note": {"text": "DoubleDoor13 (the corridor -> the entrance hall's gallery) is locked without the "
                               "Golden Honk quest (Honk.scr, key 343 = QBit 90343)."}},
             {"execute_event": {"id": dd13["event"]}}, {"advance_runtime": {"seconds": 3}},
             {"assert": {"mechanism": {"id": dd13["door_id"], "state": "closed"}}},
             walk_axis(floors, (x13, y13 - 300), 90, 0.8, (x13, y13 - 40), 300),
             {"setup_shortcut": {"kind": "set_qbit", "id": 90000 + convert.QUEST_KEY}},
             {"execute_event": {"id": dd13["event"]}}, {"advance_runtime": {"seconds": 3}},
             {"assert": {"mechanism": {"id": dd13["door_id"], "state": "open"}}},
             walk_axis(floors, (x13, y13 - 300), 90, 0.8, (x13, y13 + 300), 300),
             {"note": {"text": f"ExitTrigger0 (DAT object {exit_id}) north of the start: back to Guberland."}},
             walk_axis(floors, (start[0], start[1]), 90, 0.8, (start[0], start[1] + 300), start[2] + 200),
             {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": exit_id}}}]
    return {"id": "mm9r.templeofhonk_doors_exits", "title": "Temple of Honk (native BLV): a double door stops the "
            "party and opens, DoubleDoor13 needs the Golden Honk quest, the exit asks to leave", "world": "mm9",
            "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"], "steps": steps}


def chests(floors) -> dict | None:
    if not convert.PROPS.exists():
        return None
    _, content, _, _ = load()
    props = {e["source_name"]: e for e in json.loads(convert.PROPS.read_text())}
    treasury = {"TreasureChest2", "TreasureChest3"}
    steps = [{"load_map": {"map": MAP}},
             {"note": {"text": "TreasureChest2/3 stand in the treasury behind the secret door: opened by their events "
                               "(the HONK puzzle is scenario_scripted.yml)."}}]
    steps += scenarios.chest_steps(floors, MAP, content["chests"], props, direct=treasury)
    return {"id": "mm9r.templeofhonk_chests", "title": "Temple of Honk (native BLV): the five MM9 chests open",
            "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"], "steps": steps}


def props() -> dict:
    return {e["source_name"]: e for e in json.loads(convert.PROPS.read_text())} if convert.PROPS.exists() else {}


def actor_positions(copies: bool = True) -> list:
    """The scene's actors (x, y); without the density pass's copies (content.json `copy_of`) when copies is False."""
    scene = json.loads((WORK / "runtime/templeofhonk.scene.yml").read_text())
    copied = {a["actor_index"] for a in json.loads((WORK / "content.json").read_text())["actors"] if a.get("copy_of")}
    return [(a["position"]["x"], a["position"]["y"]) for a in scene["initial_state"]["actors"]
            if copies or a["actor_index"] not in copied]


def take(floors, anchor: str, event: int) -> list:
    """Pick up a quest object, a world item (dungeon/pickups.py), from in front of it (interact), or run its pickup
    event when the props are not built."""
    entry = props().get(anchor)
    if entry is None:
        return [{"execute_event": {"id": event}}, {"advance_runtime": {"seconds": 1}}]
    small = anchor == "key0"            # the key lies flat on the desk (1.3 high): look down on it from close by
    scene = json.loads((WORK / "runtime/templeofhonk.scene.yml").read_text())
    position = scenarios.world_item(scene, anchor)["position"]
    target = (position["x"], position["y"], position["z"])
    options = dict(distances=(80, 100) if small else (120, 160), height=1 if small else 10, max_drop=200)
    try:
        pose = scenarios.look_at(floors, MAP, target, entry["yaw_degrees"], avoid=actor_positions(), **options)
    except SystemExit:
        # The density pass's Elder Honk copies stand round the altar (work/density.json): the click looks down on
        # the Golden Honk past them (it is hit before anything beyond it)
        pose = scenarios.look_at(floors, MAP, target, entry["yaw_degrees"], avoid=actor_positions(copies=False),
                                 **options)
    return [pose, {"press_interact": {}}, {"advance_runtime": {"seconds": 1}}]


def held(item_id: int) -> list:
    """The picked-up item is in a pack (a world item goes to the packs, the hand only when they are full)."""
    return [{"assert": {"inventory_any_member": [{"item_id": item_id, "count": 1}]}}] if props() else []


def scripted(floors) -> dict:
    doors, content, report, portals = load()
    stones = {k: doors[f"{k}CornerStone"]["door_id"] for k in "HONK"}
    buttons = {k: doors[f"{k}Button"]["door_id"] for k in "HONK"}
    secret = doors["SecretDoor"]["door_id"]
    pad = next(p for p in content["pads"] if p["anchor"] == "UnlockDoorTrig")
    accountant = next(a for a in content["actors"] if a["anchor"] == "Accountant")
    honk = next(a for a in content["actors"] if a["anchor"] == "Honk0")
    press = lambda letters: [{"execute_event": {"id": convert.BUTTONS[k]}} for k in letters]   # noqa: E731
    state = lambda ids, s: [{"assert": {"mechanism": {"id": i, "state": s}}} for i in ids]       # noqa: E731
    steps = [{"load_map": {"map": MAP}},
             {"note": {"text": "Without the accountant's key (key 7000) the HONK buttons do not move."}}]
    steps += press("H") + [{"advance_runtime": {"seconds": 4}}] + state([stones["H"], buttons["H"]], "closed")
    steps += [{"assert": {"actor_visible": {"actor_index": accountant["actor_index"], "hostile_to_party": False}}},
              {"note": {"text": "The accountant's key (HonkKey.scr): item 445 and key 7000; the accountant stands by "
                                "it and sees the theft, so the Honks turn hostile."}},
              *take(floors, "key0", convert.KEY_EVENT),
              {"assert": {"qbit_set": [90000 + convert.HONK_KEY]}},
              *held(10000 + convert.HONK_KEY_ITEM),
              {"assert": {"state_dump_named_map_var": {"name": "HonksHostile", "value": 1}}},
              {"assert": {"actor_visible": {"actor_index": honk["actor_index"], "hostile_to_party": True}}},
              {"note": {"text": "A wrong order (N, H, O, K): the four stones rise, then all sink back."}}]
    steps += press("NHOK") + [{"advance_runtime": {"seconds": 3.6}}] + state([stones[k] for k in "HONK"], "open")
    steps += [{"advance_runtime": {"seconds": 4.4}}] + state([stones[k] for k in "HONK"] + [secret], "closed")
    steps += [{"note": {"text": "H, O, N, K: the secret door opens when the K stone has risen; it shuts after 10 s."}}]
    steps += press("HONK") + [{"advance_runtime": {"seconds": 6}}] + state([secret], "open")
    steps += [{"assert": {"state_dump_named_map_var": {"name": "VaultOpened", "value": 1}}},
              {"advance_runtime": {"seconds": 11}}] + state([secret], "closed")
    steps += [{"advance_runtime": {"seconds": 11}}] + state([stones[k] for k in "HONK"] + [buttons["H"]], "closed")
    steps += [{"note": {"text": "Inside the treasury the UnlockDoorTrig pad opens the secret door again."}},
              scenarios.walk_onto(floors, MAP, scenarios.floor_of(pad), "UnlockDoorTrig", distance=110),
              {"advance_runtime": {"seconds": 2}}] + state([secret], "open")
    steps += [{"note": {"text": "The Golden Honk on the altar (Honk.scr): on the quest (key 343) item 369 and key 344."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": 90000 + convert.QUEST_KEY}},
              *take(floors, "Honk", convert.GOLDEN_HONK_EVENT),
              {"assert": {"qbit_set": [90000 + convert.ON_QUEST_TAKEN],
                          "qbit_clear": [90000 + convert.OFF_QUEST_TAKEN]}},
              *held(10000 + convert.GOLDEN_HONK_ITEM)]
    return {"id": "mm9r.templeofhonk_scripted", "title": "Temple of Honk (native BLV): the accountant's key, the HONK "
            "buttons and secret door, the treasury pad, the Golden Honk", "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": steps}


def hostility(floors) -> dict:
    _, content, _, _ = load()
    honks = [a for a in content["actors"] if a["group"] == convert.HONK_GROUP]
    first, other = honks[0], honks[-1]
    steps = [{"load_map": {"map": MAP}},
             {"note": {"text": f"{len(honks)} Honks, all friends of the party (HonkHostility.inc: AddFriend Player)."}}]
    steps += [{"assert": {"actor_visible": {"actor_index": a["actor_index"], "hostile_to_party": False}}}
              for a in (first, other)]
    steps += [{"note": {"text": f"Hurting {first['anchor']} turns every Honk hostile ({other['anchor']} too)."}},
              {"damage_actor": {"actor_index": first["actor_index"], "amount": 5}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"state_dump_named_map_var": {"name": "HonksHostile", "value": 1}}},
              {"assert": {"actor_visible": {"actor_index": other["actor_index"], "hostile_to_party": True}}}]
    return {"id": "mm9r.templeofhonk_hostility", "title": "Temple of Honk (native BLV): the Honks are friends until "
            "the party hurts one", "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"],
            "steps": steps}


def swim(floors) -> dict | None:
    """The pool (BlueWater0, the scene's water volume): the party wades in, the fish stay in the water."""
    _, content, report, _ = load()
    fish = report.get("swim_fish") or []
    if not fish:
        return None
    scene = yaml.safe_load((WORK / "runtime" / f"{MAP[:-4]}.scene.yml").read_text())
    volume = next(v for v in scene["water_volumes"] if v["id"] == convert.POOL_MODEL)
    piece = volume["pieces"][0]
    xs = [x for x, _ in piece["polygon"]]
    ys = [y for _, y in piece["polygon"]]
    centre_x, centre_y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    bed = float(floors.z(centre_x, centre_y, piece["top"] + 40))
    # From the hall floor west of the pool, east over its rim into the channel.
    start_x = min(xs) - 60
    start_z = float(floors.z(start_x, centre_y, piece["top"] + 40))
    steps = [{"load_map": {"map": MAP}},
             {"note": {"text": f"The pool's water volume: surface {piece['top']}, channel bed {round(bed, 1)} (15 units "
                               "of water). The party walks off the hall floor over the rim into it and wades."}},
             {"set_pose": {"map": MAP, "x": int(start_x), "y": int(centre_y), "z": int(round(start_z + 1)),
                           "yaw": 0.0, "pitch": 0.0}},
             {"advance_runtime": {"seconds": 0.5}},
             {"assert": {"water": {"state": "dry", "eye_under": False}}},
             scenarios.movement(MAP, (start_x, centre_y, start_z + 1), 0.0, 0.3, (centre_x, centre_y, bed + 1),
                                tolerance_xy=120, tolerance_z=30),
             {"advance_runtime": {"seconds": 1}},
             {"assert": {"water": {"state": "wading", "eye_under": False, "breath_min": 0.99,
                                   "foot_z_max": piece["top"] - 5, "foot_z_min": round(bed - 2, 1)}}},
             {"advance_runtime": {"seconds": 20}},
             {"assert": {"water": {"state": "wading", "breath_min": 0.99, "drowning_ticks_max": 0}}},
             {"note": {"text": "The fish (AISwimFly, Fly S) start in the volume and are bound to it: after 20 s each is "
                               "still in the pool, its feet not under the bed (a fish that has moved rides at the "
                               "binding's clamp, 1 under the surface minus half the body; one that has idled all along "
                               "still rests on the bed where the map's load set it)."}}]
    for row in fish:
        steps.append({"assert": {"actor_visible": {
            "actor_index": row["actor_index"], "report_state": True,
            "near": {"x": centre_x, "y": centre_y, "max_distance": round(math.hypot(max(xs) - min(xs),
                                                                                   max(ys) - min(ys)) / 2),
                     "min_z": round(bed - 0.5, 1)}}}})    # Fish1 idles the whole 21 s (AI timing since 2026-11-06)
    return {"id": "mm9r.templeofhonk_swim", "title": "Temple of Honk (native BLV): wading in the pool, the fish swim in "
            "it", "world": "mm9", "mode": "faithful", "tags": ["mm9", "mm9_rework", "draft"], "steps": steps}


def main() -> int:
    floors = scenarios.Floors(Project.load(PROJECT))
    for name, builder in (("doors_exits", doors_exits), ("chests", chests), ("scripted", scripted),
                          ("hostility", hostility), ("swim", swim)):
        document = builder(floors)
        if document is None:
            print(f"scenario_{name}.yml: skipped (no props.json yet)")
            continue
        scenarios.write(PROJECT / f"scenario_{name}.yml", document, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
