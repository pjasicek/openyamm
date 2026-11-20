#!/usr/bin/env python3
"""
Write the Training Hall's scenarios from the built map (work/runtime, work/doors.json, work/content.json,
work/build_report.json, props.json). Doors, levers, boards, the bar and chests are clicked for real (a pose in front of
the model, press_interact); the archery rings are hit by a cast Fire Bolt; the trigger volumes are walked into.

- scenario_doors_exits.yml: the front door's exit; the chain from the chandelier up to the roof; the party takes
  the chain at the roof's hole and climbs down onto the chandelier, which drops into the lobby; a lobby door stops the
  party, opens on a click and lets it through; the lobby's steel ladder and a pole of the pole room; the end door: shut
  by its bar, the bar breaks on a click (key 301) and the exit then takes the party to Thjorgard;
- scenario_chests.yml: the crate's back board breaks on a click and the Blackbox opens; the four other chests;
- scenario_scripted.yml: the perception hints, the lobby ghouls, the joust lever, the Mean Trellborg's joust, the
  second horse through the wooden wall, the archery range (targets down and up, a ring hit by a Fire Bolt pays its
  prize once), a crate board, the pole room's beams, a locked reset lever.

    python3 level_generation/projects/mm9r_traininghall/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_traininghall/scenario_$s.yml --scenario-no-color; done
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

MAP = "traininghall.blv"
WORK = PROJECT / "work"
EYE = scenarios.EYE
FIRE_BOLT = 2


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.traininghall_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def var(name: str, value: int) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def state(door_id: int, value: str) -> dict:
    return {"assert": {"mechanism": {"id": door_id, "state": value}}}


def wait(seconds: float) -> dict:
    return {"advance_runtime": {"seconds": seconds}}


def native(p) -> list:
    """LithTech (x, y, z) to native (x, y, z)."""
    return [p[0] * SCALE, p[2] * SCALE, p[1] * SCALE]


class Map:
    def __init__(self):
        self.project = Project.load(PROJECT, install=False)
        self.source = Source(self.project)
        self.floors = scenarios.Floors(self.project)
        doors = json.loads((WORK / "doors.json").read_text())
        self.doors = {m["node"][5:]: m for m in doors}
        self.groups = {}
        for m in doors:
            self.groups.setdefault(m["group"], []).append(m["door_id"])
        self.content = json.loads((WORK / "content.json").read_text())
        self.report = json.loads((WORK / "build_report.json").read_text())
        self.scene = yaml.load((WORK / "runtime/traininghall.scene.yml").read_text(), Loader=yaml.CSafeLoader)
        self.props = {e["source_name"]: e for e in json.loads(convert.PROPS.read_text())}
        self.ladders = {entry["id"]: entry for entry in self.scene["ladders"]}
        self.boxes = self.report["scripted"]["boxes"]

    def model(self, name: str):
        """Native (centre, low, high) of a DAT world model."""
        points = np.array(self.source.models[name].points, float)
        low, high = self.project.native(points.min(0)), self.project.native(points.max(0))
        return (low + high) / 2, np.minimum(low, high), np.maximum(low, high)

    def pose(self, target, stand, floor_z=None, query=None) -> dict:
        """Stand at `stand` (native x, y; the floor under it, or floor_z) and look at `target` (native x, y, z)."""
        x, y = stand
        z = floor_z if floor_z is not None else self.floors.z(x, y, (query if query is not None else target[2]) + 100)
        if z is None:
            raise SystemExit(f"no floor at {stand}")
        look = math.atan2(target[1] - y, target[0] - x)
        pitch = math.atan2(target[2] - (z + EYE), math.dist((x, y), target[:2]))
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}

    def click(self, name: str, side, distance: float = 140, query=None) -> list:
        """A real click on a model: stand `distance` from its centre on `side` (native unit x, y), look at it,
        press interact."""
        centre, _, _ = self.model(name)
        direction = np.asarray(side, float)
        stand = centre[:2] + direction / np.linalg.norm(direction) * distance
        return [self.pose(centre, stand, query=query), wait(0.2), {"press_interact": {}}, wait(0.3)]

    def walk(self, start, yaw_degrees, seconds, stop, tolerance_xy=80, tolerance_z=30, query=None, z=None) -> dict:
        if z is None:
            z = self.floors.z(start[0], start[1], query if query is not None else stop[2] + 100)
        return scenarios.movement(MAP, (start[0], start[1], z + 1), yaw_degrees, seconds, stop,
                                  tolerance_xy=tolerance_xy, tolerance_z=tolerance_z)

    def climb(self, ladder_id: str, seconds: float = 5.0, back: float = 70.0) -> dict:
        """Forward from the foot of a ladder strip: grab, climb, step off at its top exit."""
        ladder = self.ladders[ladder_id]
        yaw = ladder["facing_degrees"]
        fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        foot = [ladder["bottom"][0] - fx * back, ladder["bottom"][1] - fy * back, ladder["bottom"][2]]
        pose = {"map": MAP, "x": int(round(foot[0])), "y": int(round(foot[1])), "z": int(round(foot[2])) + 1,
                "yaw_degrees": round(yaw, 1), "pitch": 0}
        top = [int(round(v)) for v in ladder["top_exit"]]
        return {"movement_segment": {"input": "forward", "seconds": seconds, "actor_collision": False,
                                     "actor_ai": False, "start": pose,
                                     "expect_stop": dict(pose, x=top[0], y=top[1], z=top[2]),
                                     "loose_tolerance": True, "tolerance_xy": 250, "tolerance_z": 60}}

    def climb_from_air(self, ladder_id: str, start_height_lt: float, back: float = 90.0, seconds: float = 3.0) -> dict:
        """Forward from a point in the air in front of a ladder strip: the party falls, takes hold, climbs, steps off."""
        ladder = self.ladders[ladder_id]
        yaw = ladder["facing_degrees"]
        fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        pose = {"map": MAP, "x": int(round(ladder["bottom"][0] - fx * back)),
                "y": int(round(ladder["bottom"][1] - fy * back)), "z": int(round(start_height_lt * SCALE)),
                "yaw_degrees": round(yaw, 1), "pitch": 0}
        top = [int(round(v)) for v in ladder["top_exit"]]
        return {"movement_segment": {"input": "forward", "seconds": seconds, "actor_collision": False,
                                     "actor_ai": False, "start": pose,
                                     "expect_stop": dict(pose, x=top[0], y=top[1], z=top[2]),
                                     "loose_tolerance": True, "tolerance_xy": 250, "tolerance_z": 60}}

    def stand_in(self, name: str, z=None) -> dict:
        """Set the party down in the middle of a trigger box (on the floor under it)."""
        lo, hi = self.boxes[name]
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        z = z if z is not None else self.floors.z(cx, cy, hi[2] + 50)
        return {"set_pose": {"map": MAP, "x": int(round(cx)), "y": int(round(cy)), "z": int(round(z)) + 1,
                             "yaw": 0.0, "pitch": 0.0}}


def doors_exits(m: Map) -> dict:
    doc = header("doors_exits", "Training Hall (native BLV): the front door, the chain, the chandelier's fall, a lobby "
                                "door by click, the ladders, the end door's bar and its exit")
    steps = doc["steps"]
    start = m.report["starts"][0]["position"]
    exits = {t["name"]: int(t["id"].rsplit("/", 1)[1]) for t in m.report["transitions"] if t["source"] == MAP}
    groups = m.groups
    steps += [
        {"note": {"text": f"ExitTrigger1 (DAT object {exits['ExitTrigger1']}) in the roof room's east door: back to "
                          "Thjorgard."}},
        m.walk((215, 0), 0, 0.5, (373, 0, start[2] + 1), 150, 60, z=start[2]),     # east of the hole
        {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger",
                                                 "source_id": exits["ExitTrigger1"]}}},
        {"load_map": {"map": MAP}},
    ]
    drop = groups["drop"][0]
    steps += [
        {"note": {"text": "The roof room's hole: walking into it the party takes the chain at its top and climbs down "
                          "onto the chandelier, which creaks, cracks and falls 432 LT into the lobby's pool with the "
                          "party (dropsequence, cracktrigger1-5, droptrigger, DestructableBrush6, Door 'drop')."}},
        state(drop, "closed"),
        # The chain is taken at its top (grab_at_top since 2026-11-10; its reach of 140 covers the hole, which ends
        # about 200 from it): forward from the rim grabs it, glides on and climbs down; 3.5 s ends on the chandelier.
        m.walk((100, 330), 270, 3.5, (100, -50, 1100), 250, 60, z=1639),
        # the fall onto the wheel (about 1 s), the poll (0.25 s), MM9's SendDelays from dropsequence to droptrigger
        # (0.5 + 0.35 + 0.35 + 0.25 + 1.25 + 1.0 = 3.7 s) and the door's 432 LT at 750 LT/s (0.6 s)
        wait(7.0),
        var("DropDone", 1), state(drop, "open"),
    ]
    door = groups["LobbyDoorE"]
    centre, _, _ = m.model("RotatingDoor0")
    steps += [
        {"note": {"text": "LobbyDoorE (RotatingDoor0/2, doorportal0): shut, it stops the party; a click swings it "
                          "open and the party walks into the east corridor."}},
        state(door[0], "closed"),
        m.walk((800, 0), 0, 1.0, (1150, 0, 1), 60, 30, query=100),
        *m.click("RotatingDoor0", side=(-1, 0), distance=150, query=100), wait(2.5),
        state(door[0], "open"), state(door[1], "open"),
        m.walk((800, 0), 0, 1.2, (1700, 0, 1), 150, 30, query=100),
    ]
    steps += [
        {"note": {"text": "Ladder0 (the lobby's west steel ladder) up to its crow's nest (TreasureChest1)."}},
        m.climb("Ladder0", seconds=5.0),
        {"note": {"text": "Ladder13 (the pole room's lowest pole, WorldObject17): from the water surface up onto the "
                          "beam it hangs from."}},
        m.climb("Ladder13_0", seconds=3.0),
        {"note": {"text": "The poles take a party in the air (grab_in_air): falling past Ladder9's pole (WorldObject13, "
                          "416-712 LT, over the water) while moving toward it, the party takes hold, climbs and steps "
                          "off on the platform above (736 LT)."}},
        m.climb_from_air("Ladder9_1", start_height_lt=600.0, seconds=1.0),     # with the glide onto the top exit
    ]
    centre, _, _ = m.model("DestructableBrush12")
    steps += [
        {"note": {"text": "The end door (TrainingEnter.scr): ExitTrigger0 starts off; the bar's slab keeps the party "
                          "out of its volume. A click breaks the bar (a scene destructible: the click's killing "
                          "blow): key 301, the reward, and the door is an exit."}},
        m.walk((0, -3000), 270, 1.2, (0, -3410, 1), 100, 30, query=100),
        var("BarBroken", 0),
        m.pose(centre, (0, -3300), query=100), wait(0.2), {"press_interact": {}}, wait(1.0),
        var("BarBroken", 1), {"assert": {"qbit_set": [90000 + convert.KEY_TRAINED]}},
        m.walk((0, -3200), 270, 1.0, (0, -3600, 1), 300, 60, query=100),
        {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger",
                                                 "source_id": exits["ExitTrigger0"]}}},
    ]
    return doc


def chests(m: Map) -> dict:
    doc = header("chests", "Training Hall (native BLV): the crate's back board breaks and the Blackbox opens; the four "
                           "other chests open from in front of them")
    steps = doc["steps"]
    centre, _, _ = m.model("DestructableBrush8")
    chest = m.props["Blackbox"]
    blackbox = next(c for c in m.content["chests"] if c["anchor"] == "Blackbox")
    steps += [
        {"note": {"text": "DestructableBrush8, the crate's south board: a click breaks it (crateopentrigger: "
                          "PerceptionBrush8 off)."}},
        *m.click("DestructableBrush8", side=(0, -1), distance=150, query=100), wait(1.0),
        var("BrokenDestructableBrush8", 1),
        {"note": {"text": "Headless picking does not follow a moved board (playbook): the Blackbox opens by its "
                          "event."}},
        {"execute_event": {"id": blackbox["event"]}},
        {"assert": {"chest_opened": {"chest_id": blackbox["container_id"]}}},
        {"press_action": {"action": "cancel_dialog"}},
    ]
    # TreasureChest1 stands in the crow's nest (96 LT across): a close look.
    nest = next(c for c in m.content["chests"] if c["anchor"] == "TreasureChest1")
    entry = m.props["TreasureChest1"]
    steps += [scenarios.look_at(m.floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                distances=(70, 90, 110)), {"press_interact": {}},
              {"assert": {"chest_opened": {"chest_id": nest["container_id"]}}},
              {"press_action": {"action": "cancel_dialog"}}]
    others = [c for c in m.content["chests"] if c["anchor"] not in ("Blackbox", "TreasureChest1")]
    steps += scenarios.chest_steps(m.floors, MAP, others, m.props)
    return doc


def scripted(m: Map) -> dict:
    doc = header("scripted", "Training Hall (native BLV): perception hints, the lobby ghouls, the joust, the Mean "
                             "Trellborg, the second horse and the wooden wall, the archery range, a crate board, the "
                             "pole room's beams, a reset lever")
    steps = doc["steps"]
    groups = m.groups
    hints = m.report["scripted"]["hints"]
    low = [hints["PerceptionBrush0"], hints["PerceptionBrush1"]]
    high = [hints[f"PerceptionBrush{k}"] for k in range(2, 9)]
    steps += [
        {"note": {"text": "The pole room's beams loop from the map's load: Pusher0 starts out after MoveDelay 2 s, "
                          "130 LT at 40 LT/s, waits 3 s, comes back."}},
        wait(2.75), state(groups["Pusher0"][0], "opening"), wait(3.0), state(groups["Pusher0"][0], "open"),
        wait(3.5), state(groups["Pusher0"][0], "closing"),
        {"note": {"text": "The chain (MM9 Ladder 'Chain Ladder'): from the chandelier's top a climber goes up the "
                          "chain through the roof's hole and steps off on the roof room's floor (the chandelier falls "
                          "behind him: standing on it set off dropsequence; TriggerLobbyGhouls fired too)."}},
        m.climb("ChainLadder_1", seconds=4.0, back=40),
        wait(1.5), var("DropDone", 1), var("GhoulsUp", 1),
        {"note": {"text": "The PerceptionBrushes: the chandelier's bar and the wooden wall show at Perception 12, the "
                          "crate's boards at 17."}},
        {"console": {"line": "skill set Perception 1 B"}}, wait(3.5),
        *[var(f"Hint{c}", 1) for c in low + high[:1]],
        {"console": {"line": "skill set Perception 12 B"}}, wait(3.5),
        *[var(f"Hint{c}", 2) for c in low], var(f"Hint{high[0]}", 1),
        {"console": {"line": "skill set Perception 17 B"}}, wait(3.5), var(f"Hint{high[0]}", 2),
    ]
    dragon = groups["dragonroomdoor"]
    steps += [
        {"note": {"text": "TriggerLobbyGhouls (on the chain over the chandelier): the sauna ghouls go to their perch "
                          "over the pole room's entrance and the dragon door opens; TriggerGhoulsAttack in its "
                          "corridor drops them and shuts the door."}},
        m.stand_in("TriggerGhoulsAttack", z=553), wait(1.0), var("GhoulsDropped", 1),
        wait(3.0), state(dragon[0], "closed"),
    ]
    lever2 = groups["d2lever"][0]
    horse2 = groups["Horse2"][0]
    steps += [
        {"note": {"text": "d2lever (Switch): a click sends the training horse down its lane; a second brings it back."}},
        *m.click("d2lever", side=(0, 1), distance=150, query=-500), wait(2.0),
        var("Horse2Out", 1), state(horse2, "open"), state(lever2, "open"),
        *m.click("d2lever", side=(0, 1), distance=150, query=-500), wait(7.0),
        var("Horse2Out", 0), state(horse2, "closed"),
        {"note": {"text": "TriggerTrellborgOn0 (the east stair down): the Mean Trellborg starts jousting: after his "
                          "stand, two fidgets and a taunt (7 s) he pulls the lever and the horse rides; TriggerTrellborgOff0 above stops him."}},
        m.stand_in("TriggerTrellborgOn0", z=m.floors.z(1894, -1024, 0)), wait(1.0), var("Jousting", 1),
        wait(7.0), var("Launches", 1), var("Horse2Out", 1),
        m.stand_in("TriggerTrellborgOff0", z=m.floors.z(1884, -584, 200)), wait(1.0), var("Jousting", 0),
        {"note": {"text": "TriggerOrcTraining / TriggerOrcsStop: the orcs' drill, their commander and observer (the "
                          "scene routines) start and stop."}},
        m.stand_in("TriggerOrcTraining"), wait(1.0), var("OrcTraining", 1),
        m.stand_in("TriggerOrcsStop"), wait(1.0), var("OrcTraining", 0),
    ]
    steps += [
        {"note": {"text": "d4lever0: the second horse rides through the wooden wall at the lane's east end; the wall's "
                          "pieces (woodexplosion, upperbreak1/2, lowerbreak1/2) are gone and its hint goes off."}},
        *m.click("d4lever0", side=(0, 1), distance=150, query=-500), wait(2.5),
        var("WallBroken", 1), state(groups["Horse4"][0], "open"),
        var(f"HintOff{hints['PerceptionBrush1']}", 1),
    ]
    off_lo, off_hi = m.boxes["TriggerTargetsOff"]
    on_lo, on_hi = m.boxes["TriggerTargetsOn"]
    x = 1350 * SCALE                # east of the counters (x 912-1232 LT with a pillar in the middle)
    target1 = groups["target1"][0]
    ring = m.model("Rank8000a")[0]
    steps += [
        {"note": {"text": "The archery range: past TriggerTargetsOff the targets lie down, back past TriggerTargetsOn "
                          "they stand."}},
        state(target1, "closed"),
        m.walk((x, (on_lo[1] + off_hi[1]) / 2), 270, 0.6, (x, off_lo[1], 1), 250, 40, query=100),
        wait(3.0), var("TargetsDown", 1), state(target1, "open"),
        m.walk((x, off_lo[1] - 150), 90, 1.8, (x, on_hi[1] + 300, 1), 300, 40, query=100),
        wait(3.0), var("TargetsDown", 0), state(target1, "closed"),
        {"note": {"text": "A ring hit (MM9 OnDamage of TH_TargetRing.scr) on target 1's bullseye (Rank8000a): the "
                          "bell, its prize of 8000 gold once (key 7010), and the target lies flat for good. The ring's "
                          "event runs here: a scenario cannot aim a missile at a point (README, not checked)."}},
        {"execute_event": {"id": convert.EV_RINGS["Rank8000a"]}}, wait(2.0),
        var("Prize1", 8000),
        var("RingHits", 1), {"assert": {"qbit_set": [90000 + convert.KEY_WON + 1]}},
        state(target1, "open"), var("TargetLocked1", 1),
    ]
    steps += [
        {"note": {"text": "A crate board (DestructableBrush0, north face), its hint showing (Perception 17): a click "
                          "on the glow breaks the board and the hint goes off."}},
        *m.click("DestructableBrush0", side=(0, 1), distance=150, query=100), wait(1.0),
        var("BrokenDestructableBrush0", 1),
        var(f"HintOff{hints['PerceptionBrush2']}", 1),
        {"note": {"text": "DestructableBrush1 (25 HP, a scene destructible): 24 damage leave it standing, one more "
                          "breaks it (a weapon's route) and its hint goes off."}},
        {"console": {"line": f"destructible {m.source.by_name['destructablebrush1']['index']} damage 24",
                     "expect_contains": "damage"}}, wait(0.3), var("BrokenDestructableBrush1", 0),
        {"console": {"line": f"destructible {m.source.by_name['destructablebrush1']['index']} damage 1",
                     "expect_contains": "damage"}}, wait(0.3), var("BrokenDestructableBrush1", 1),
        var(f"HintOff{hints['PerceptionBrush3']}", 1),
        {"note": {"text": "resetlever1 (MM9 Locked): a click does nothing but say so."}},
        *m.click("resetlever1", side=(0, 1), distance=120, query=100),
        state(groups["resetlever1"][0], "closed"),
    ]
    return doc


def main() -> int:
    m = Map()
    for name, builder in (("doors_exits", doors_exits), ("chests", chests), ("scripted", scripted)):
        scenarios.write(PROJECT / f"scenario_{name}.yml", builder(m), "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
