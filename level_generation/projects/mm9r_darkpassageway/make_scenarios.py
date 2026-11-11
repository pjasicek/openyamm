#!/usr/bin/env python3
"""
Write Dark Passageway's scenarios from the built map (work/runtime, work/doors.json, work/content.json,
work/build_report.json, props.json). Doors, statues, mirrors, the gemstone, the painting, the scroll and chests are
clicked for real (a pose in front of the model, press_interact); trigger and teleporter volumes are walked into or
stood in.

- scenario_doors_exits.yml: the ladders (Ladder5 from the first bridge up to the start corridor, Ladder1 out of the
  lake, Ladder0 out of the spike pit); ExitRoomDoor stops the party shut and opens on a click; TeleportDoor0 stays
  locked; every teleporter (and, without swimming, the tube room's dive) raises its move; the exit room's riser
  (ExitTrigger2 -> 0 -> 1 -> 3); the flame cage keeps the party off ExitPoint until the Wyrde's talk opens it, then the exit to Guberland;
- scenario_chests.yml: the painting's hidden room (TreasureChest0-2) after a click on the painting; the four cage
  chests after the mirror puzzle releases the cages;
- scenario_swim.yml (swimming, the shared water rule; devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md): the party
  falls into the bridge lake, goes under and swims up to its surface; swims from the tube room down the flooded tube and
  shaft (MM9's current) and drops into the ocean; climbs onto the island; SeaMonsterFemale0 stays in the ocean while
  the party stands on the island;
- scenario_scripted.yml: the perception hints; the bridge puzzle solved by clicks on the four ice statues in MM9's
  order ADCBDCBA (and the reset statue); the forest ambush; the canyon statue's banshee eyes and doors; the magic
  carpet; the spike trap; Njam's cameo; the scroll.

    python3 level_generation/projects/mm9r_darkpassageway/make_scenarios.py
    for s in doors_exits chests scripted swim; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_darkpassageway/scenario_$s.yml --scenario-no-color; done
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
from dungeon.source import SCALE, Project, Source  # noqa: E402
import convert  # noqa: E402

MAP = "darkpassageway.blv"
WORK = PROJECT / "work"
EYE = scenarios.EYE


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.darkpassageway_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def var(name: str, value: int) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def state(door_id: int, value: str) -> dict:
    return {"assert": {"mechanism": {"id": door_id, "state": value}}}


def wait(seconds: float) -> dict:
    return {"advance_runtime": {"seconds": seconds}}


def native(p) -> list:
    return [p[0] * SCALE, p[2] * SCALE, p[1] * SCALE]


class Map:
    def __init__(self):
        self.project = Project.load(PROJECT, install=False)
        self.source = Source(self.project)
        self.floors = scenarios.Floors(self.project)
        doors = json.loads((WORK / "doors.json").read_text())
        self.groups = {}
        self.boxes_by_door = {}
        for m in doors:
            self.groups.setdefault(m["group"], []).append(m["door_id"])
            self.boxes_by_door[m["door_id"]] = m.get("box")
        self.content = json.loads((WORK / "content.json").read_text())
        self.report = json.loads((WORK / "build_report.json").read_text())
        self.scene = yaml.load((WORK / f"runtime/{self.project.stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
        self.props = {e["source_name"]: e for e in json.loads(convert.PROPS.read_text())}
        self.ladders = {entry["id"]: entry for entry in self.scene["ladders"]}
        self.boxes = self.report["scripted"]["boxes"]
        self.actor = self.report["scripted"]["actors"]
        self.positions = {a["actor_index"]: a["position"] for a in self.scene["initial_state"]["actors"]}
        self.volumes = {v["id"]: v for v in self.scene.get("water_volumes", [])}
        self.swim = bool(self.volumes)

    def model(self, name: str):
        points = np.array(self.source.models[name].points, float)
        low, high = self.project.native(points.min(0)), self.project.native(points.max(0))
        return (low + high) / 2, np.minimum(low, high), np.maximum(low, high)

    def pose(self, target, stand, floor_z=None, query=None) -> dict:
        x, y = stand
        z = floor_z if floor_z is not None else self.floors.z(x, y, (query if query is not None else target[2]) + 100)
        if z is None:
            raise SystemExit(f"no floor at {stand}")
        look = math.atan2(target[1] - y, target[0] - x)
        pitch = math.atan2(target[2] - (z + EYE), math.dist((x, y), target[:2]))
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}

    def click(self, name: str, side, distance: float = 140, query=None, floor_z=None) -> list:
        centre, _, _ = self.model(name)
        direction = np.asarray(side, float)
        stand = centre[:2] + direction / np.linalg.norm(direction) * distance
        return [self.pose(centre, stand, query=query, floor_z=floor_z), wait(0.2), {"press_interact": {}}, wait(0.3)]

    def click_prop(self, name: str, side, distance: float = 110, floor_z=None, height: float = 40, shift_z=0.0) -> list:
        e = self.props[name]
        target = (e["x"], e["y"], e["z"] + shift_z + height)
        direction = np.asarray(side, float)
        stand = np.array([e["x"], e["y"]]) + direction / np.linalg.norm(direction) * distance
        z = e["z"] + shift_z if floor_z is None else floor_z
        return [self.pose(target, stand, floor_z=z), wait(0.2), {"press_interact": {}}, wait(0.3)]

    def walk(self, start, yaw_degrees, seconds, stop, tolerance_xy=80, tolerance_z=30, query=None, z=None) -> dict:
        if z is None:
            z = self.floors.z(start[0], start[1], query if query is not None else stop[2] + 100)
        return scenarios.movement(MAP, (start[0], start[1], z + 1), yaw_degrees, seconds, stop,
                                  tolerance_xy=tolerance_xy, tolerance_z=tolerance_z)

    def climb(self, ladder_id: str, seconds: float = 5.0, back: float = 70.0, foot_z=None, tolerance_xy=250) -> dict:
        ladder = self.ladders[ladder_id]
        yaw = ladder["facing_degrees"]
        fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        foot = [ladder["bottom"][0] - fx * back, ladder["bottom"][1] - fy * back,
                ladder["bottom"][2] if foot_z is None else foot_z]
        pose = {"map": MAP, "x": int(round(foot[0])), "y": int(round(foot[1])), "z": int(round(foot[2])) + 1,
                "yaw_degrees": round(yaw, 1), "pitch": 0}
        top = [int(round(v)) for v in ladder["top_exit"]]
        return {"movement_segment": {"input": "forward", "seconds": seconds, "actor_collision": False,
                                     "actor_ai": False, "start": pose,
                                     "expect_stop": dict(pose, x=top[0], y=top[1], z=top[2]),
                                     "loose_tolerance": True, "tolerance_xy": tolerance_xy, "tolerance_z": 60}}

    def stand_in(self, name: str, z=None) -> dict:
        lo, hi = self.boxes[name]
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        z = z if z is not None else self.floors.z(cx, cy, hi[2] + 50)
        return {"set_pose": {"map": MAP, "x": int(round(cx)), "y": int(round(cy)), "z": int(round(z)) + 1,
                             "yaw": 0.0, "pitch": 0.0}}

    def away(self) -> dict:
        """A neutral spot (the start room) between volume visits, so the next box counts as a new entry."""
        start = self.report["starts"][0]["position"]
        return {"set_pose": {"map": MAP, "x": start[0], "y": start[1], "z": start[2], "yaw": 0.0, "pitch": 0.0}}


def doors_exits(m: Map) -> dict:
    doc = header("doors_exits", "Dark Passageway (native BLV): ladders, a door by click, the locked teleport door, the "
                                "teleporters and the dive, the exit room's riser, the flame cage and the exit")
    steps = doc["steps"]
    g = m.groups
    # swimming: the party swims at Ladder1 with its feet at the lake's surface pose
    lake_surface_foot = (max(piece["top"] for piece in m.volumes["BlueWater0"]["pieces"]) + SURFACE_EYE - EYE_HEIGHT
                         if m.swim else None)
    exits = {t["name"]: int(t["id"].rsplit("/", 1)[1]) for t in m.report["transitions"] if t["source"] == MAP}
    steps += [
        {"note": {"text": "Ladder5 (rungs WorldObject10): from the first bridge's deck (Bridge0, built up) up to the "
                          "start corridor."}},
        state(g["Bridge0"][0], "closed"),
        m.climb("Ladder5", seconds=5.0, foot_z=-1229, tolerance_xy=900),
        {"note": {"text": "Ladder1: from the lake (swimming at its surface) up onto Bridge0."}},
        m.climb("Ladder1", seconds=5.0, foot_z=lake_surface_foot if m.swim else -1531),
        {"note": {"text": "Ladder0: the spike trap tips the party into its pit; the ladder takes it out onto the "
                          "corridor north of it."}},
        m.stand_in("SpikeTrigger1", z=-328), wait(3.0), var("SpikesOpen", 1),
        m.climb("Ladder0", seconds=4.0, foot_z=-773),
    ]
    door = g["ExitRoomDoor"][0]
    centre, _, _ = m.model("ExitRoomDoor")
    steps += [
        {"note": {"text": "ExitRoomDoor (Door, 96 LT up at 70): shut, it stops the party coming up the corridor from "
                          "the desert arrival; a click opens it and the party walks into the exit room."}},
        state(door, "closed"),
        m.walk((centre[0], centre[1] - 330), 90, 1.0, (centre[0], centre[1] - 40, -1159), 70, 40, query=centre[2]),
        *m.click("ExitRoomDoor", side=(0, -1), distance=150, query=centre[2]), wait(2.5),
        state(door, "open"),
        m.walk((centre[0], centre[1] - 330), 90, 1.0, (centre[0], centre[1] + 400, -1188), 150, 60, query=centre[2]),
    ]
    tp = g["TeleportDoor0"][0]
    steps += [
        {"note": {"text": "TeleportDoor0 (MM9 Locked): a click before the bridge puzzle is solved says it is locked."}},
        *m.click("TeleportDoor0", side=(0, 1), distance=170, floor_z=-1229), wait(1.0),
        state(tp, "closed"), var("PuzzleSolved", 0),
    ]
    for name in convert.TELEPORTERS:
        steps += [{"note": {"text": f"{name} (Teleporter, TouchNotify): the party in its box goes to "
                                    f"{convert.TELEPORTERS[name]} (a same-map move: the frame loop applies it, so the "
                                    "request is asserted)."}},
                  m.away(), wait(0.5), m.stand_in(name), wait(0.6), var(f"LastTeleport{name}", 1)]
    if "Dive" in m.boxes and not m.swim:
        steps += [
            {"note": {"text": "The tube room's dive (MM9 swims down the flooded tube into the ocean hall)."}},
            m.away(), wait(0.5), m.stand_in("Dive", z=-979), wait(0.6), var("Dives", 1),
        ]
    riser = g["ExitRiser"][0]
    steps += [{"note": {"text": "The exit room: ExitTrigger2 (StartOn) -> 0 -> 1 -> 3 (on the riser): the riser rises "
                                "228 LT and the ramp runs out to the upper door."}},
              m.away(), wait(0.5), state(riser, "closed")]
    # ExitTrigger3 lies over the riser: the party stands on its plate (8 units over the floor the trigger's floor
    # probe finds), so the rising riser carries it (a party sunk into the plate holds the riser, MM9's hold rule).
    riser_top = m.boxes_by_door[riser][1][2]
    for k in (2, 0, 1, 3):
        steps += [m.stand_in(f"ExitTrigger{k}", z=riser_top if k == 3 else None), wait(0.6)]
    steps += [var("RiserUp", 1), wait(6.0), state(riser, "open"),
              {"note": {"text": "The Switch (-> ExitReset) puts the riser back."}},
              *m.click("Switch", side=(0, -1), distance=120, query=-1000), wait(1.0), var("Resets", 1), var("RiserUp", 0)]
    cage = g["FlameCage"][0]
    lo, hi = m.boxes["FlameDamage"]
    exit_x, exit_y = 492, 6349
    wyrde_event = 50000 + m.source.by_name["wyrdeoftheunknown0"]["index"]
    steps += [
        {"note": {"text": "The flame cage (FlameCage) stands round ExitPoint: the party walking at the exit stops at "
                          "its slab, in the fire (FlameDamage)."}},
        state(cage, "closed"),
        m.walk((exit_x - 420, exit_y), 0, 1.0, (exit_x - 170, exit_y, -573), 80, 40, query=-400),
        var("CageOpen", 0),
        {"note": {"text": "The Wyrde of the Unknown (NPC338.scr :OnRude, on RUDE 338's exit): the first talk gives keys "
                          "476 and 187, 92 000 experience, and opens the cage; ExitPoint then takes the party to "
                          "Guberland."}},
        scenarios.look_at(m.floors, MAP, tuple(m.positions[m.actor["WyrdeoftheUnknown0"]][k] for k in "xyz"), 0,
                          distances=(150, 200), height=60), wait(0.2), {"press_interact": {}},
        {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": convert.RUDE_WYRDE}}},
        {"press_action": {"action": "cancel_dialog"}}, wait(9.5),
        var("CageOpen", 1), {"assert": {"qbit_set": [90000 + convert.KEY_ACTIVATED, 90000 + convert.KEY_MET]}},
        state(cage, "open"),
        {"note": {"text": "The party walks onto the water barrel at ExitPoint (the cage gone)."}},
        {"set_pose": {"map": MAP, "x": exit_x - 60, "y": exit_y, "z": -572, "yaw": 0.0, "pitch": 0.0}}, wait(0.5),
        {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": exits["ExitPoint"]}}},
    ]
    return doc


def chests(m: Map) -> dict:
    doc = header("chests", "Dark Passageway (native BLV): the painting's hidden room and the four cage chests")
    steps = doc["steps"]
    g = m.groups
    centre, _, _ = m.model("Painting")
    steps += [
        {"note": {"text": "The painting (RotatingDoor): a click swings it and opens DoubleDoorL40/R40 into the hidden "
                          "room behind it (TreasureChest0-2)."}},
        *m.click("Painting", side=(-1, 0), distance=160, query=0), wait(4.0),
        var("PaintingOpen", 1), state(g["DoubleDoor40"][0], "open"),
    ]
    hidden = [c for c in m.content["chests"] if c["anchor"] in ("TreasureChest0", "TreasureChest1", "TreasureChest2")]
    steps += scenarios.chest_steps(m.floors, MAP, hidden, m.props)
    steps += [{"note": {"text": "The mirror puzzle (scenario_scripted.yml clicks it): here the mirrors are turned by "
                                "their events and the gemstone is clicked; the cages open."}}]
    for k, (name, (angle, _)) in enumerate(convert.MIRRORS.items()):
        steps += [{"execute_event": {"id": convert.EV_MIRROR[name]}} for _ in range(angle // 10)]
    steps += [*m.click_prop("Gemstone", side=(1, 0), distance=120, height=20), wait(5.0), var("CagesOpen", 1)]
    cages = [c for c in m.content["chests"] if c["anchor"] not in ("TreasureChest0", "TreasureChest1", "TreasureChest2")]
    avoid = [tuple(m.positions[m.actor[name]][k] for k in ("x", "y")) for name in convert.CAGES]
    for chest in cages:
        entry = m.props[chest["anchor"]]
        steps += [scenarios.look_at(m.floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                    distances=(110, 150), avoid=avoid), {"press_interact": {}},
                  {"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    return doc


def scripted(m: Map) -> dict:
    doc = header("scripted", "Dark Passageway (native BLV): perception hints, the bridge puzzle, the painting, the "
                             "mirror puzzle, the forest ambush, the canyon statue, the magic carpet, the spike trap, "
                             "Njam's cameo, the scroll")
    steps = doc["steps"]
    g = m.groups
    hints = m.report["scripted"]["hints"]
    steps += [
        {"note": {"text": "The PerceptionBrushes show to a party with enough Perception."}},
        {"console": {"line": "skill set Perception 1 B"}}, wait(3.5),
        *[var(f"Hint{c}", 1) for c in hints.values()],
        {"console": {"line": "skill set Perception 30 G"}}, wait(3.5),
        *[var(f"Hint{c}", 2) for c in hints.values()],
    ]
    # The bridge puzzle: MM9's sequence ADCBDCBA from 14 (DarkP_initMyStuff.inc).
    steps += [{"note": {"text": "The bridge puzzle: the four ice statues ride the bridges; clicks in MM9's order "
                                "ADCBDCBA raise every bridge and open TeleportDoor0. First the reset statue on a "
                                "changed state."}}]
    statue = {v: k for k, v in convert.SWITCH_LETTER.items()}
    puzzle = convert.PUZZLE_START

    def statue_click(name, state_now):
        k = convert.STATUE_BRIDGE[name]
        down = (state_now >> (4 - k)) & 1 == 1
        moved = down == convert.BRIDGE_BUILT_UP[k]
        shift = 0.0
        if moved:
            shift = (-160.0 if convert.BRIDGE_BUILT_UP[k] else 160.0) * SCALE
        deck = (-480.0 * SCALE) + shift          # the bridge's plank deck (WoodPlanks, -480 LT up, -640 down)
        return m.click_prop(name, side=(0, 1), distance=110, shift_z=shift, height=30, floor_z=deck)

    def clip_wait(name):
        """The statue's Use clip and a little: its end tells the puzzle (DarkP_RaisingSwitch.scr :TriggerScrObj)."""
        use = convert.SWITCH_STATUES[name][2]
        return wait(round(convert.statue_clips(m.props[name]["prop"])[use] + 0.6, 1))

    steps += [*statue_click("SwitchCreature0", puzzle), wait(0.5), var("StatueBusy0", 1),
              var("PuzzleSet", 0), clip_wait("SwitchCreature0"), var("Puzzle", convert.PUZZLE["A"][puzzle]),
              *m.click_prop("SwitchCreature5", side=(0, -1), distance=110, height=30), clip_wait("SwitchCreature5"),
              var("Puzzle", convert.PUZZLE_START)]
    for letter in "ADCBDCBA":
        name = statue[letter]
        steps += [*statue_click(name, puzzle), clip_wait(name)]
        puzzle = convert.PUZZLE[letter][puzzle]
        steps.append(var("Puzzle", puzzle))
    steps += [var("PuzzleSolved", 1), wait(7.0), state(g["TeleportDoor0"][0], "open"),
              *[state(g[f"Bridge{k}"][0], "open" if not convert.BRIDGE_BUILT_UP[k] else "closed") for k in range(5)]]
    # The mirrors: two real clicks, the rest by event; then a real click on the gemstone.
    steps += [{"note": {"text": "The mirror puzzle: a click turns a mirror 10 degrees (two real clicks, the rest by its "
                                "event); with every mirror on its target the gemstone's light releases the cages and "
                                "opens DesertDoor0."}},
              *m.click_prop("Gemstone", side=(1, 0), distance=120, height=20), wait(1.0),
              var("Shines", 1), var("CagesOpen", 0),
              *m.click("Mirror1", side=(1, 0), distance=120, query=-300), var("Mirror2", 1),
              *m.click("Mirror0", side=(1, 0), distance=120, query=-300), var("Mirror1", 1)]
    for name, (angle, _) in convert.MIRRORS.items():
        done = 1 if name in ("Mirror0", "Mirror1") else 0
        steps += [{"execute_event": {"id": convert.EV_MIRROR[name]}} for _ in range(angle // 10 - done)]
    steps += [*m.click_prop("Gemstone", side=(1, 0), distance=120, height=20), wait(1.0), var("CagesOpen", 1),
              wait(4.0), state(g["DesertDoor0"][0], "open"), *[state(g[f"Door{k}"][0], "open") for k in range(1, 7)]]
    # Forest.
    steps += [
        {"note": {"text": "The forest: TriggerDoor0 unlocks and opens ForestDoor0; TriggerAttack0 slams it shut behind "
                          "the party, the Colloidal Warrior strikes the adventurer down and wakes; TeleportDoor1 stays "
                          "locked while he lives."}},
        # ForestDoor0 rises 96 LT at 70 LT/s (1.4 s): still opening 1 s after the trigger, open 2 s later.
        m.stand_in("TriggerDoor0"), wait(1.0), var("ForestUnlocked", 1), state(g["ForestDoor0"][0], "opening"),
        wait(2.0), state(g["ForestDoor0"][0], "open"),
        m.stand_in("TriggerAttack0"), wait(0.6), var("ForestLocked", 1), wait(2.0), var("AdventurerDead", 1),
        *m.click("TeleportDoor1", side=(0, 1), distance=170, query=0), wait(1.0), state(g["TeleportDoor1"][0], "closed"),
    ]
    # Canyon.
    steps += [
        {"note": {"text": "The canyon statue (DarkP_CanyonSwitch.scr): a click from its ledge plays its four clips, "
                          "each one's end waking a pair of banshee eyes, and the last opens the canyon doors; TriggerBansheeOff0 by the mountain teleporter stops the "
                          "eyes."}},
        *m.click_prop("SwitchCreature4", side=(1, -0.3), distance=110, floor_z=31, height=30), wait(1.2),
        var("CanyonStep", 2), var("EyesOn", 2), var("CanyonOpen", 0), wait(4.8),
        var("EyesOn", 8), var("CanyonOpen", 1), wait(4.0), state(g["CanyonDoor"][0], "open"),
        m.stand_in("TriggerBansheeOff0"), wait(0.6), var("EyesOff", 1),
    ]
    carpet, low, high = m.model("ElevatorObj")
    cx = carpet[0] + convert.CARPET_SHIFT_LT[0] * SCALE
    cy = carpet[1] + convert.CARPET_SHIFT_LT[1] * SCALE
    top = high[2] - convert.CARPET_DROP_LT * SCALE
    # From the pit's floor south of it: walking stops at its edge (over a step), a running jump lands on it.
    south = cy - (high[1] - low[1]) / 2
    pit = m.floors.z(cx, south - 240, top)
    start = {"map": MAP, "x": int(round(cx)), "y": int(round(south - 240)), "z": int(round(pit)),
             "yaw_degrees": 90.0, "pitch": 0}
    on_carpet = {"assert": {"party_position": {"x": int(round(cx)), "y": int(round(cy)), "radius": 200,
                                               "z_min": int(round(top)) - 3, "z_max": int(round(top)) + 3}}}
    steps += [
        {"note": {"text": "The magic carpet from the pit's floor (lowered for it, README Deviations): walking stops at "
                          "its edge, a running jump lands on it."}},
        scenarios.movement(MAP, (cx, south - 240, pit), 90.0, 0.6, (cx, south - 37, pit), tolerance_xy=20,
                           tolerance_z=4),
        {"movement_segment": {"input": "forward", "jump": True, "seconds": 0.5, "actor_collision": False,
                              "actor_ai": False, "start": start,
                              "expect_stop": dict(start, y=int(round(south + 140)), z=int(round(top))),
                              "loose_tolerance": True, "tolerance_xy": 150, "tolerance_z": 120}},
        wait(1.0), on_carpet,
        {"note": {"text": "The magic carpet (MagicCarpet.scr): a click from the carpet lifts it from the pit's floor to "
                          "the statue's ledge (12 LT); from its top the party walks onto the ledge."}},
        {"set_pose": {"map": MAP, "x": int(round(cx)), "y": int(round(cy)), "z": int(round(top)) + 1,
                      "yaw": 0.0, "pitch": -1.3}},
        wait(0.3), {"press_interact": {}}, wait(0.5), var("CarpetUp", 1), wait(5.5), state(g["ElevatorObj"][0], "open"),
        scenarios.movement(MAP, (cx, cy, 31 + 1), math.degrees(math.atan2(-6600 * SCALE - cy, -7600 * SCALE - cx)), 0.8,
                           (-7600 * SCALE, -6600 * SCALE, 31), tolerance_xy=250, tolerance_z=40),
    ]
    # Spike trap.
    flap = g["SpikeDoor1"][0]
    steps += [
        {"note": {"text": "The spike trap (SpikeTrigger1): stepping onto the flaps tips all four down into the pit."}},
        state(flap, "closed"), m.stand_in("SpikeTrigger1", z=-328), wait(0.6), var("SpikesOpen", 1), wait(1.5),
        state(flap, "open"),
        {"note": {"text": "Njam the Meddler's cameo (Trigger1): the effect a second later, he appears two more "
                          "later and walks; after 10-20 s the map sends him away (stage 4)."}},
        m.stand_in("Trigger1"), wait(3.5), var("NjamShown", 1), var("NjamStage", 3), wait(21.0),
        var("NjamStage", 4),
        {"note": {"text": "The scroll (Givetake.scr '483'), a world item, picked up: the Scrap of Book."}},
        *scenarios.pick_up_steps(m.floors, MAP, m.scene, "Prop38", distances=(90, 120)),
        {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.KEY_SCROLL_ITEM, "count": 1}]}},
    ]
    return doc


# Swimming. The eye point is the eye less 25.6; the surface pose holds it 1 over the water (engine IndoorWater).
SURFACE_EYE = 1.0 + 25.6
EYE_HEIGHT = 160.0


def swim(m: Map) -> dict:
    doc = header("swim", "Dark Passageway (native BLV) - swimming: into the lake and up, down the flooded tube into "
                         "the ocean, onto the island; the female sea monster stays in the ocean")
    steps = doc["steps"]

    def top(volume: str) -> float:
        return max(piece["top"] for piece in m.volumes[volume]["pieces"])

    def surface_foot(volume: str) -> float:
        return top(volume) + SURFACE_EYE - EYE_HEIGHT

    def water(**fields):
        return {"assert": {"water": {key: round(float(v), 1) if isinstance(v, float) else v
                                     for key, v in fields.items()}}}

    def pose(x, y, z, yaw=0.0, pitch=0.0):
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)), "yaw": yaw,
                             "pitch": pitch}}

    def segment(start, yaw, seconds, stop, keys=None, tolerance=2000, tolerance_z=2000, pitch=0.0):
        start_pose = {"map": MAP, "x": int(round(start[0])), "y": int(round(start[1])), "z": int(round(start[2])),
                      "yaw": round(yaw, 4), "pitch": round(pitch, 4)}
        step = {"input": "forward", "seconds": seconds, "actor_collision": False, "actor_ai": False,
                "start": start_pose, "expect_stop": dict(start_pose, x=int(round(stop[0])), y=int(round(stop[1])),
                                                         z=int(round(stop[2]))),
                "loose_tolerance": True, "tolerance_xy": tolerance, "tolerance_z": tolerance_z}
        step.update(keys or {})
        return {"movement_segment": step}

    def deepest(volume: str, margin: float = 250.0):
        """A point of the volume with open water over a deep bed and the same bed `margin` round it."""
        best = None
        surface = top(volume)
        for piece in m.volumes[volume]["pieces"]:
            ring = np.array(piece["polygon"], float)
            (x0, y0), (x1, y1) = ring.min(0) + margin, ring.max(0) - margin
            for x in np.arange(x0, x1, 200.0):
                for y in np.arange(y0, y1, 200.0):
                    beds = [m.floors.z(x + dx, y + dy, surface - 1) for dx in (-margin, 0, margin)
                            for dy in (-margin, 0, margin)]
                    over = m.floors.z(x, y, surface + 600)
                    if None in beds or over is None or abs(over - beds[4]) > 1 or max(beds) - min(beds) > 40:
                        continue
                    if best is None or beds[4] < best[2]:
                        best = (float(x), float(y), float(beds[4]))
        if best is None:
            raise SystemExit(f"{volume}: no open deep water")
        return best

    lake = deepest("BlueWater0")
    steps += [
        {"note": {"text": f"The bridge lake (BlueWater0, top {top('BlueWater0')}, bed {lake[2]:.0f} here): dropped "
                          "over the open water the party falls in, its eye goes under, it sinks."}},
        pose(lake[0], lake[1], top("BlueWater0") + 150),
        wait(2.5),
        water(eye_under=True, foot_z_max=top("BlueWater0") - EYE_HEIGHT),
        {"note": {"text": "Up (Fly Up held): it rises at 384 a second and holds at the surface, its eye out, breath "
                          "full."}},
        segment((lake[0], lake[1], top("BlueWater0") - 400), 0.0, 2.0,
                (lake[0], lake[1], surface_foot("BlueWater0")), {"input": "none", "fly_up": True}),
        water(state="surface", eye_under=False, breath_min=0.99, foot_z_min=surface_foot("BlueWater0") - 4,
              foot_z_max=surface_foot("BlueWater0") + 4),
    ]
    # The flooded tube: from the tube room's water (TubeRoomWater0) east along the tube (between its floor and its
    # ceiling, in TubeRoomWater from x -10158) into the shaft (convert.SHAFT_SKY), down with MM9's current and out of
    # its bottom (the ocean hall's non-solid sky) into the ocean.
    (sx0, sz0), (sx1, sz1) = convert.SHAFT_SKY[1], convert.SHAFT_SKY[2]
    shaft = native(((sx0 + sx1) / 2, 0.0, (sz0 + sz1) / 2))
    tube_floor = m.floors.z(shaft[0] - 500, shaft[1], top("TubeRoomWater") - 1)
    start = (shaft[0] - 900, shaft[1], tube_floor + 60)
    ocean = top("Ocean")
    steps += [
        {"note": {"text": "The flooded tube (TubeRoomWater, MM9's current 90 LT/s down): under water in the tube room's "
                          "end, the party swims east along the tube to the shaft and sinks down it with the current; "
                          "at its bottom (ShaftExit) it is moved under the ocean hall's non-solid sky and falls into "
                          "the ocean."}},
        pose(*start, yaw=0.0),
        wait(0.3),
        water(eye_under=True),
        segment(start, 0.0, 3.0, (shaft[0], shaft[1], tube_floor)),
        {"advance_runtime": {"seconds": 5.0, "follow_map_move": True}},
        var("ShaftDrops", 1),
        wait(4.0),
        water(eye_under=True, foot_z_max=ocean - EYE_HEIGHT + 20),
    ]
    # The island: its sand (Terrain3) ends 21 to 64 over the water above steep flanks. The party at the surface off the
    # lowest stretch of its edge (searched round the cage on the DAT floors; 160 out, past the flank under the surface
    # pose's feet) swims at it with a fresh Jump (the surface jump: the feet rise about 190) and lands on the sand.
    cage, _, _ = m.model("DB_TeleporterCage0")
    best = None
    for k in range(16):
        a = 2 * math.pi * k / 16
        previous = None
        for r in range(200, 2000, 5):
            z = m.floors.z(cage[0] + r * math.cos(a), cage[1] + r * math.sin(a), ocean + 300)
            if z is None or z < ocean:
                if previous is not None and (best is None or previous < best[2]):
                    best = (a, r - 5, previous)
                break
            previous = z
    if best is None:
        raise SystemExit("no island edge round the teleporter cage")
    a, edge, _ = best
    x, y = cage[0] + (edge - 150) * math.cos(a), cage[1] + (edge - 150) * math.sin(a)
    z = m.floors.z(x, y, ocean + 300)
    off = (cage[0] + (edge + 160) * math.cos(a), cage[1] + (edge + 160) * math.sin(a))
    female = m.actor["SeaMonsterFemale0"]
    spawn = m.positions[female]
    steps += [
        {"note": {"text": "Out onto the island: at the surface 160 off the sand's lowest edge the party swims at it with a "
                          "fresh Jump (the surface jump) and lands on the sand."}},
        # 0.6 s: the jump lands about 0.45 s in, 290 on; held longer, forward runs on up the sloping sand (the jump
        # no longer stops at the sand's edge touched from the side, 2026-11-07), 450 in and 97 higher at 1.0 s.
        segment((off[0], off[1], surface_foot("Ocean")), a + math.pi, 0.6, (x, y, z), {"jump": True},
                tolerance=450, tolerance_z=60),
        water(state="dry", eye_under=False, foot_z_min=ocean),
        {"note": {"text": "SeaMonsterFemale0 (a swimmer: its box centre at MM9's position, under the surface), hit by "
                          "the party on the island, stays in the ocean (bound to its volume)."}},
        pose(x, y, z + 1, yaw=math.atan2(spawn["y"] - y, spawn["x"] - x)),
        {"damage_actor": {"actor_index": female, "amount": 1}},
        wait(8.0),
        {"assert": {"actor_visible": {"actor_index": female, "report_state": True,
                                      "near": {"x": spawn["x"], "y": spawn["y"], "max_distance": 2600,
                                               "min_z": float(np.floor(m.floors.z(spawn["x"], spawn["y"], ocean)))}}}},
        water(state="dry"),
    ]
    return doc


def main() -> int:
    m = Map()
    builders = [("doors_exits", doors_exits), ("chests", chests), ("scripted", scripted)]
    if m.swim:
        builders.append(("swim", swim))
    for name, builder in builders:
        scenarios.write(PROJECT / f"scenario_{name}.yml", builder(m), "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
