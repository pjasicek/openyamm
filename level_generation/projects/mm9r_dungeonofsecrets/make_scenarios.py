#!/usr/bin/env python3
"""
Write the Dungeon of Secrets' scenarios from the built map (work/runtime, work/doors.json, work/content.json,
work/build_report.json). Levers, doors and the entrance button are clicked for real (a pose in front of the model,
press_interact); trigger volumes and plates are walked into.

    python3 level_generation/projects/mm9r_dungeonofsecrets/make_scenarios.py
    bash level_generation/projects/mm9r_dungeonofsecrets/work/run_scenarios.sh
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
from dungeon import scenarios, water  # noqa: E402
from dungeon.source import SCALE, Project, Source  # noqa: E402
import convert  # noqa: E402

MAP = "dungeonofsecrets.blv"
WORK = PROJECT / "work"
EYE = scenarios.EYE


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.dungeonofsecrets_{name}", "title": title, "world": "mm9", "mode": "faithful",
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
        for m in doors:
            self.groups.setdefault(m["group"], []).append(m["door_id"])
        self.content = json.loads((WORK / "content.json").read_text())
        self.report = json.loads((WORK / "build_report.json").read_text())
        self.scene = yaml.load((WORK / f"runtime/{self.project.stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
        self.props = {e["source_name"]: e for e in json.loads(convert.PROPS.read_text())}
        self.boxes = self.report["scripted"]["boxes"]
        self.positions = {a["actor_index"]: a["position"] for a in self.scene["initial_state"]["actors"]}

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




def lt(x, z) -> tuple:
    return (x * SCALE, z * SCALE)


def qbit(key: int, on: bool = True) -> dict:
    return {"console": {"line": f"qbit {'set' if on else 'clear'} {90000 + key}"}}


def has_key(key: int) -> dict:
    return {"assert": {"qbit_set": [90000 + key]}}


def at(m: Map, x_lt, z_lt, query_lt, yaw_degrees=0.0) -> dict:
    x, y = lt(x_lt, z_lt)
    z = m.floors.z(x, y, query_lt * SCALE)
    if z is None:
        raise SystemExit(f"no floor at LT {x_lt} {z_lt}")
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                         "yaw": round(math.radians(yaw_degrees), 4), "pitch": 0.0}}


# The nine sections in MM9's order: (section, lever, the side the lever faces, run seconds from the lever to the end
# door at the party's run (768 units a second, the path's length measured on the plan), the side the party comes to
# the door from, a point past the door (LT x, z, floor query y)).
SECTIONS = [
    ("10", (0, -1), 0.6, (1, 0), (1480, -160, 100)),
    ("09", (-1, 0), 1.0, (1, 0), (1150, -330, 100)),
    ("08", (-1, 0), 3.0, (0, -1), (600, 60, 100)),
    ("01", (-1, 0), 4.0, (0, -1), (-928, 1860, 100)),
    ("02", (-1, 0), 5.0, (0, -1), (-256, 1650, 420)),
    ("03", (1, 0), 1.4, (0, 1), (600, 740, 420)),
    ("04", (0, -1), 3.0, (1, 0), (-560, 490, 420)),
    ("05", (0, -1), 1.2, (0, 1), (-688, -600, 100)),
    ("06", (0, 1), 6.5, (-1, 0), (1090, -690, 100)),
]


def section_steps(m: Map, k: str, lever_side, run, door_side, past, late: bool = False, pushed_to=None) -> list:
    g = m.groups
    lever = f"timer lever {k}"
    steps = [{"note": {"text": f"Section {k}: a click throws timer lever {k} (its axe trap locked while the lever creeps "
                               f"back); the party runs to axe door {k} ({run} s) and opens it with a click"
                               + (" too late: the axe swings, Chadwick marks a trap." if late else " in time.")}},
             *m.click(lever, side=lever_side, distance=110), var(f"Usedtimer_lever_{k}", 1)]
    lever_door = DOOR_FOR.get(k)
    steps += [wait(1.0), var(f"Laxe_trap_{k}", 1), wait(max(0.1, run - 1.0) if not late else 12.0)]
    centre, _, _ = m.model(f"axe door {k}")
    steps += [*m.click(f"axe door {k}", side=door_side, distance=110, query=centre[2]), wait(1.0),
              var(f"Saxe_door_{k}", 2)]
    if late:
        steps += [var(f"Saxe_trap_{k}", 2), var("Traps", 1), has_key(244)]
        if pushed_to is not None:
            steps += [{"note": {"text": f"The axe's DamageBrush (knockback{k}) pushed the party off the door, to native "
                                        f"({pushed_to[0]}, {pushed_to[1]}) (evt.PushParty; evt.Jump moved it 9 units)."}},
                      {"assert": {"party_position": {"x": pushed_to[0], "y": pushed_to[1], "radius": 48}}}]
    else:
        steps += [var(f"Saxe_trap_{k}", 0), var("Traps", 0), state(g[f"axe_door_{k}"][0], "open")]
    steps.append(at(m, past[0], past[1], past[2]))
    return steps


DOOR_FOR = {}


def trial(m: Map) -> dict:
    doc = header("trial", "Dungeon of Secrets: Chadwick's trial run clean through all nine sections by real clicks")
    steps = doc["steps"]
    g = m.groups
    steps += [wait(1.0), var("Loaded", 1),
              {"note": {"text": "RUDE 417 node 3 ('Yes'): the trial starts (key 243); the entrance button (from the east, "
                                "MM9's push side) opens the gate, clears the trap mark and unlocks axe door 10; the party "
                                "standing at it is in 'knockback off', which turns every knockback off."}},
              qbit(243), *m.click("entrance button", side=(1, 0), distance=110, query=0), wait(1.5),
              var("Lentrance_button", 1), var("Firedknockback_off", 1), var("Firedknockback_off1", 1),
              wait(4.0), state(g["entrance_gate"][0], "open")]
    for k, lever_side, run, door_side, past in SECTIONS:
        if k == "05":
            steps += [{"note": {"text": "Section 5's elevator: the party walks up the ramp onto the column (MM9: a jump "
                                        "onto its box); the touch takes it down 320 LT to the lower room."}},
                      at(m, -688, 120, 420, -90), m.walk(lt(-688, 120), -90, 1.05, (*lt(-688, -180), 860), 220, 60, z=655),
                      wait(0.5), var("Selevator", 1), wait(10.0), var("Selevator", 2), var("Lelevator", 1)]
        steps += section_steps(m, k, lever_side, run, door_side, past)
    steps += [{"note": {"text": "Past axe door 6 the party crosses the exit gate's open trigger: the gate opens and tells "
                                "Chadwick 'done': no trap went off, so key 245 and the quest sound."}},
              m.walk(lt(1080, -690), 0, 0.8, (*lt(1318, -690), -41), 160, 40), wait(2.5),
              var("Firedexit_gate_open_trigger", 1), var("Sexit_gate", 2), has_key(245), var("Traps", 0)]
    return doc


def box_pose(m: Map, box, query_z=None, yaw=0.0, z=None) -> dict:
    lo, hi = box
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    if z is None:
        z = m.floors.z(cx, cy, (query_z if query_z is not None else hi[2]) + 60)
    return {"set_pose": {"map": MAP, "x": int(round(cx)), "y": int(round(cy)), "z": int(round(z)) + 1,
                         "yaw": yaw, "pitch": 0.0}}


def traps(m: Map) -> dict:
    doc = header("traps", "Dungeon of Secrets: every kind of trap goes off as MM9 wires it, and marks the trial")
    steps = doc["steps"]
    g = m.groups
    boxes = m.report["scripted"]["boxes"]
    touch = m.report["scripted"]["touch"]
    away = at(m, 2100, -416, 100, 180)
    steps += [wait(1.0), qbit(243),
              {"note": {"text": "Perception hints (PerceptionBrush, PerceptionValue 15): hidden at Perception 1, shown at 30."}},
              {"console": {"line": "skill set Perception 1 B"}}, wait(3.5),
              *[var(f"Hint{c}", 1) for c in m.report["scripted"]["hints"].values()],
              {"console": {"line": "skill set Perception 30 G"}}, wait(3.5),
              *[var(f"Hint{c}", 2) for c in m.report["scripted"]["hints"].values()]]
    # The late door: section 10.
    steps += [*m.click("entrance button", side=(1, 0), distance=110, query=0), wait(5.0),
              *section_steps(m, "10", (0, -1), 0.0, (1, 0), (1480, -160, 100), late=True, pushed_to=(4238, -410)),
              {"note": {"text": "The axe's DamageBrush (knockback10, Current 800 along x) threw the party."}},
              var("Knockedknockback10", 1), wait(4.0), var("Saxe_trap_10", 0)]
    # Section 1's fire plates.
    steps += [{"note": {"text": "Section 1: stepping on plate trigger01 presses floor01 (6 LT down), whose OpenTrigger "
                                "turns shooter1 on: a fire bolt; the plate rises after a second and turns it off."}},
              away, wait(0.5), box_pose(m, boxes["trigger01"], z=0), wait(1.0), var("Firedtrigger01", 1),
              var("Sfloor01", 2), var("Shotshooter1", 1), var("Traps", 2), wait(3.0), var("Sfloor01", 0)]
    steps += [{"note": {"text": "The plate room's entrance (rat death start): the rat cameo's volley of the ratshooters "
                                "(MM9's rat objects are not in the DAT: their messages go nowhere)."}},
              away, wait(0.5), box_pose(m, boxes["rat death start"]), wait(14.0), var("Firedrat_death_start", 1),
              var("Sratdoortrigger", 2), var("Firedrattrigger03", 1), var("Shotratshooter08a", 1)]
    # Section 6's gauntlet.
    for trig, plate, trap, knock in (("gtrigger1", "gplate1", "gtrap1", "knockback12"),
                                     ("gtrigger3a", "gplate3", "gtrap3", "knockback14"),
                                     ("gtrigger4", "gplate4", "gtrap4", "knockback15"),
                                     ("gtrigger7", "gplate7", "gtrap7a", "knockback19"),
                                     ("gtrigger8a", "gplate8", "gtrap8a", "knockback23"),
                                     ("gtrigger9", "gplate9", "gtrap9", "knockback20")):
        # The plate is down 0.2 s after the poll sees the party and stays locked until its trap is back: gtrap3, the
        # quickest, is back 0.53 s later (0.13 out, 0.4 back), so the plate is checked 0.5 s after the pose (at 1.2 s
        # the old poll's slow ticks still showed it locked; with its true 0.1 s it is closing by then).
        steps += [{"note": {"text": f"Section 6: {trig} presses {plate}, which springs {trap} (locked down until the "
                                    "trap has gone back, which unlocks and lifts it)."}},
                  away, wait(0.5), box_pose(m, boxes[trig], z=-41), wait(0.5), var(f"Fired{trig}", 1),
                  var(f"S{plate}", 2), *([var(f"L{plate}", 1)] if trap != "gtrap7a" else []), wait(2.0),
                  var(f"Opened{trap}", 1), away, wait(12.0),
                  var(f"S{trap}", 2 if trap == "gtrap7a" else 0), var(f"L{plate}", 0), var(f"S{plate}", 0)]
        # gtrap7a/b are Sticky 360-degree wheels: one spin, they stay 'open' (the same pose), as in MM9.
    # Section 4's double axe.
    steps += [{"note": {"text": "Section 4: the upper plate (TouchToOpen) springs the double axe: the side door and the "
                                "floor panels open, the axes come out and swing, knockback11 throws a party in the corridor west of the plate east; the "
                                "side door shuts after 4 s and re-arms both plates."}},
              away, wait(0.5), box_pose(m, touch["doubleaxe upper trigger"]), wait(2.0),
              var("Sdoubleaxe_upper_trigger", 2), var("FiredDouble_Axe_Trap_Trigger", 1), var("OpenedSide_Door", 1),
              var("OpenedTop_Door", 1), var("OpenedBottom_Door", 1), var("OpenedPanel_Mover", 1),
              var("OpenedAxe_Mover", 1), var("OpenedTop_Axe", 1), var("OpenedBottom_Axe", 1),
              away, wait(12.0), var("SSide_Door", 0),
              var("Ldoubleaxe_upper_trigger", 0), var("Sdoubleaxe_upper_trigger", 0)]
    # Section 2's blade under the stairs.
    steps += [{"note": {"text": "Section 2: the box over the stair's foot (Trigger (BUS)) slides the panels open 1.5 s "
                                "later: the blade spins out and knockback22 goes on; Timer (BUS) re-arms the box 10 s on."}},
              away, wait(0.5), box_pose(m, boxes["Trigger (BUS)"]), wait(2.5), var("FiredTrigger__BUS_", 1),
              var("OpenedSliding_Panels", 1), var("Knockedknockback22", 0), away, wait(12.0), var("FiredTimer__BUS_", 1),
              var("TTrigger__BUS_", 1)]
    # Section 3's fake levers and the water grate.
    centre, _, _ = m.model("fake lever 7")
    steps += [{"note": {"text": "Section 3: a fake lever moves and does nothing else (axe trap 03 stays unlocked)."}},
              *m.click("fake lever 7", side=(1, 0.3), distance=130), var("Usedfake_lever_7", 1), wait(1.2),
              var("Sfake_lever_7", 3), var("Laxe_trap_03", 0),
              {"note": {"text": "The water grate (PushOpen): a click opens it and its opener, which lock open."}},
              *m.click("water grate", side=(-1, 0.2), distance=70, query=0), wait(4.0), var("Swater_grate", 2),
              var("Lwater_grate", 1)]
    steps += [var("Traps", 10), has_key(244)]   # the late door, a plate, six gauntlet plates, the double axe, the blade
    if water.swimming(m.project):
        # The submerged tunnel (ClearWater0), swum as MM9's (the shared water rule): down the open west shaft, east
        # along the tunnel under section 4's corridor, up the east shaft under the open water grate.
        bed = at(m, -295, 472, -100)["set_pose"]
        east_x, east_y = lt(296, 472)
        swim = dict(bed, yaw=0.0, pitch=0.0)
        steps += [{"note": {"text": "The submerged tunnel: on the west shaft's bed the party's eye is under water; it "
                                    "swims east along the tunnel and up the east shaft under the open water grate."}},
                  {"set_pose": bed}, wait(1.0), {"assert": {"water": {"state": "bed", "eye_under": True}}},
                  {"movement_segment": {"input": "forward", "seconds": 4.0, "actor_collision": False,
                                        "actor_ai": False, "start": swim,
                                        "expect_stop": dict(swim, x=int(round(east_x)), y=int(round(east_y))),
                                        "loose_tolerance": True, "tolerance_xy": 4000, "tolerance_z": 4000}},
                  {"assert": {"water": {"eye_under": True}}},
                  {"assert": {"party_position": {"x": int(round(east_x)), "y": int(round(east_y)), "radius": 200}}},
                  {"movement_segment": {"input": "none", "seconds": 2.5, "actor_collision": False, "actor_ai": False,
                                        "start": dict(swim, x=int(round(east_x)), y=int(round(east_y))),
                                        "expect_stop": dict(swim, x=int(round(east_x)), y=int(round(east_y))),
                                        "loose_tolerance": True, "tolerance_xy": 4000, "tolerance_z": 4000,
                                        "fly_up": True}},
                  {"assert": {"water": {"state": "surface", "eye_under": False, "breath_min": 0.99}}}]
    else:
        steps += [{"note": {"text": "A party that sinks into the open west shaft of the submerged tunnel comes up beside it "
                                    "(the same-map move is applied by the frame loop: the request is asserted)."}},
                  at(m, -295, 472, -100), wait(1.0), var("Surfaced", 1)]
    return doc


def doors_exits(m: Map) -> dict:
    doc = header("doors_exits", "Dungeon of Secrets: a shut door stops the party and opens on a click, the stair, "
                                "Chadwick's dialogue and reward, the exit to Frosgard")
    steps = doc["steps"]
    g = m.groups
    door = g["axe_door_10"][0]
    centre, _, _ = m.model("axe door 10")
    # The axe doors' knockbacks start on (MM9 StartOn); the party arriving from Frosgard crosses `knockback off` at
    # the hub's east end, which turns them off. The walks below start west of it, so it is crossed first: without
    # it knockback02 throws the party back down section 2's stair at axe door 2 (seen once the map's poll kept its
    # 0.1 s period, 2026-10-31).
    steps += [wait(1.0),
              {"note": {"text": "The arrival: the party coming in from Frosgard crosses `knockback off` at the hub's "
                                "east end, which turns off the axe doors' knockbacks (they start on in MM9)."}},
              m.stand_in("knockback off"), wait(0.5), var("Firedknockback_off", 1),
              {"note": {"text": "Axe door 10 (RotatingDoor): shut, it stops the party walking west from the lever corner; "
                                "a click opens it and the party walks through into section 9's room."}},
              state(door, "closed"),
              m.walk((centre[0] + 230, centre[1]), 180, 1.0, (centre[0] + 50, centre[1], -41), 60, 30),
              *m.click("axe door 10", side=(1, 0), distance=110, query=centre[2]), wait(1.5), state(door, "open"),
              m.walk((centre[0] + 230, centre[1]), 180, 1.0, (centre[0] - 530, centre[1], -41), 200, 40)]
    steps += [{"note": {"text": "Section 2's stair (8 LT risers, 256 LT up): "
                                "the party walks up from the corridor to axe door 2."}},
              m.walk(lt(-290, 960), 90, 3.2, (*lt(-290, 1530), 655), 260, 60, z=0)]
    steps += [{"note": {"text": "The flooded pool room under section 4 (floor -24 LT, water to -16): the party climbs out "
                                "west onto the corridor (floor 0) and east (floor 8) by the invisible steps where MM9's "
                                "player climbs out of the water."}},
              m.walk(lt(-380, 472), 180, 1.0, (*lt(-675, 472), 1), 200, 30, z=-61),
              m.walk(lt(380, 472), 0, 1.0, (*lt(675, 472), 20), 200, 30, z=-61),
]
    pos = m.positions[m.report["scripted"]["chadwick"]["actor_index"]]
    target = (pos["x"], pos["y"], pos["z"])
    # He stands in a ticket booth: the party talks to him through the gap between two window bars, from the east.
    booth = {"set_pose": {"map": MAP, "x": target[0] + 260, "y": target[1], "z": -40, "yaw": round(math.pi, 4),
                          "pitch": -0.05}}
    steps += [{"note": {"text": "Chadwick Boorsley (RUDE 417): a click opens his dialogue. With the reward topic taken "
                                "(key 246, RUDE node 417/3), the dialogue's exit runs NPC417.scr :OnRude: 10 000 "
                                "experience, the quest sound and key 247."}},
              booth, wait(0.2),
              {"press_interact": {}},
              {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": convert.RUDE_CHADWICK}}},
              {"press_action": {"action": "cancel_dialog"}}, wait(0.5),
              qbit(246), booth, wait(0.2),
              {"press_interact": {}},
              {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": convert.RUDE_CHADWICK}}},
              {"press_action": {"action": "cancel_dialog"}}, wait(1.0), has_key(247)]
    steps += [{"note": {"text": "ExitTrigger0 (to Frosgard, DungeonOfSecretsExit): the party walks east from the arrival "
                                "into it."}},
              m.walk(lt(1980, -416), 0, 0.75, (*lt(2150, -416), -40), 300, 120),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": 362}}}]
    return doc

def smoke(m: Map) -> dict:
    doc = header("smoke", "Dungeon of Secrets: the map Lua loads; the entrance button opens the gate")
    steps = doc["steps"]
    g = m.groups
    steps += [wait(1.0), var("Loaded", 1),
              *m.click("entrance button", side=(0, -1), distance=120, query=0), wait(4.0),
              var("Usedentrance_button", 1), var("Sentrance_button", 2), var("Lentrance_button", 1),
              var("Sentrance_gate", 2), wait(1.0), state(g["entrance_gate"][0], "open")]
    return doc


def main() -> int:
    m = Map()
    names = sys.argv[1:] or ["trial", "traps", "doors_exits"]
    for name in names:
        scenarios.write(PROJECT / f"scenario_{name}.yml", globals()[name](m), "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
