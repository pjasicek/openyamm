#!/usr/bin/env python3
"""
Write the Ruined Temple's scenarios from the built map (work/runtime, work/doors.json, work/content.json,
work/build_report.json, props.json). Doors, buttons, chests, the Tree of Life, the lamp and the genie are clicked for
real (a pose in front of the model, press_interact); only what headless picking cannot reach is run by its event.

- scenario_doors_exits.yml: the exit asks to leave; the skylight's glass box over the hole breaks when the party comes
  near (Trigger1) and the party drops through the hole into the hall below; a plain door stops the party, opens on a
  click and lets it through; LeftDoor is locked until SunButton4 has opened HiddenDoor2; the ladder;
- scenario_chests.yml: the three chests open from in front of their models;
- scenario_scripted.yml: the sun buttons and hidden doors (both sides, the 10 s close), HiddenButton, the elevator puzzle,
  the crypt (counterbalance, lid, dirt plugs, the escape door and the cell), the Tree of Life and the second cave-in,
  the first cave-in, the scrolls, the perception hints, the lamp and the genie's wish (dialogue 435).

    python3 level_generation/projects/mm9r_ruinedtemple/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_ruinedtemple/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import csv
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
from dungeon.source import Project, Source  # noqa: E402
import convert  # noqa: E402

MAP = "ruinedtemple.blv"
WORK = PROJECT / "work"
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
EYE = scenarios.EYE


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.ruinedtemple_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def key(raw: int) -> int:
    return 90000 + raw


def var(name: str, value: int) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def state(door_id: int, value: str) -> dict:
    return {"assert": {"mechanism": {"id": door_id, "state": value}}}


def wait(seconds: float) -> dict:
    return {"advance_runtime": {"seconds": seconds}}


def choose(rude: int, node: int, label: str) -> dict:
    """The dialogue row `label` of a RUDE node (its action id is the row's place in the file)."""
    with open(RUDE / f"NPC{rude}.rude", newline="", encoding="latin-1") as stream:
        rows = list(csv.reader(stream))
    index = next(k for k, row in enumerate(rows) if int(row[1]) == node and row[3] == label)
    return {"select_topic": {"action_id": index, "match_label": label}}


class Map:
    def __init__(self):
        self.project = Project.load(PROJECT, install=False)
        self.source = Source(self.project)
        self.floors = scenarios.Floors(self.project)
        self.doors = {m["node"][5:]: m for m in json.loads((WORK / "doors.json").read_text())}
        self.content = json.loads((WORK / "content.json").read_text())
        self.report = json.loads((WORK / "build_report.json").read_text())
        self.scene = yaml.load((WORK / "runtime/ruinedtemple.scene.yml").read_text(), Loader=yaml.CSafeLoader)
        self.props = {e["source_name"]: e for e in json.loads(convert.PROPS.read_text())} \
            if convert.PROPS.exists() else {}
        genie = (self.report["scripted"].get("genie") or {}).get("actor")
        self.actors = [(a["position"]["x"], a["position"]["y"]) for i, a in enumerate(self.scene["initial_state"]["actors"])
                       if i != genie]       # the genie stands hidden on the lamp until it is called

    def model(self, name: str):
        """(native centre, native push direction) of a DAT world model (the direction its MoveDir pushes it)."""
        points = np.array(self.source.models[name].points, float)
        centre = self.project.native((points.min(0) + points.max(0)) / 2)
        move = self.source.properties(name).get("MoveDir") or [0.0, 0.0, 0.0]
        return centre, np.array([move[0], move[2], move[1]], float)

    def pose(self, target, stand, query=None) -> dict:
        """Stand at `stand` (native x, y; the floor under it) and look at `target` (native x, y, z)."""
        x, y = stand
        z = self.floors.z(x, y, (query if query is not None else target[2]) + 100)
        if z is None:
            raise SystemExit(f"no floor at {stand}")
        look = math.atan2(target[1] - y, target[0] - x)
        pitch = math.atan2(target[2] - (z + EYE), math.dist((x, y), target[:2]))
        return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(look, 4), "pitch": round(pitch, 4)}}

    def click(self, name: str, distance: float = 140, side=None, query=None) -> list:
        """A real click on a wall button or door: stand `distance` in front of its pressed face (against MoveDir, or
        on `side`: a native unit vector from the model), look at its centre, press interact."""
        centre, push = self.model(name)
        direction = np.asarray(side, float) if side is not None else -push
        stand = centre[:2] + direction[:2] / (np.linalg.norm(direction[:2]) or 1) * distance
        return [self.pose(centre, stand, query), wait(0.2), {"press_interact": {}}, wait(0.3)]

    def click_prop(self, anchor: str, distances=(120, 160), height=10, max_drop=200) -> list:
        entry = self.props[anchor]
        return [scenarios.look_at(self.floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                  distances=distances, height=height, max_drop=max_drop, avoid=self.actors),
                wait(0.2), {"press_interact": {}}, wait(0.5)]

    def walk(self, start, yaw_degrees, seconds, stop, tolerance_xy=80, tolerance_z=30, query=None) -> dict:
        z = self.floors.z(start[0], start[1], query if query is not None else (start[2] if len(start) > 2 else stop[2]) + 100)
        return scenarios.movement(MAP, (start[0], start[1], z + 1), yaw_degrees, seconds, stop,
                                  tolerance_xy=tolerance_xy, tolerance_z=tolerance_z)


def doors_exits(m: Map) -> dict:
    doc = header("doors_exits", "Ruined Temple (native BLV): the exit, the skylight over the hole, a door by click, "
                                "LeftDoor's lock, the ladder")
    steps = doc["steps"]
    start = m.report["starts"][0]["position"]
    # the exit's transition row id is its DAT object index (map_transitions.txt mm9:transition/ruinedtemple/<index>)
    exit_id = next(o["index"] for o in m.source.objects if o["class"] == "ExitTrigger")
    d = m.doors
    hole_floor = m.floors.z(0, -1800, -1800)
    steps += [
        {"note": {"text": f"ExitTrigger0 (DAT object {exit_id}) just north of the start: back to Frosgard."}},
        m.walk((start[0], start[1]), 90, 0.8, (start[0], start[1] + 300, start[2] + 1), 200, 60),
        {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": exit_id}}},
        {"load_map": {"map": MAP}},
        {"note": {"text": "South of the start the skylight's glass box stands over a hole in the floor; Trigger1 "
                          "(the party near it) breaks the glass and its wooden frame (DestructableBrush6, glass1-8)."}},
        state(d["DestructableBrush6"]["door_id"], "closed"),
        wait(3.5),          # the trigger volumes are polled from the map's first timer tick on
        m.walk((start[0] + 70, start[1]), 270, 0.85, (start[0] + 70, start[1] - 560, start[2] + 1), 300, 800),
        wait(2.0),
        var("FloorFallen", 1),
        state(d["DestructableBrush6"]["door_id"], "open"),
        state(d["glass6"]["door_id"], "open"),
        {"note": {"text": f"The party walks into the hole and lands in the hall below (floor {hole_floor:.0f})."}},
        m.walk((start[0], start[1] - 480), 270, 1.0, (0, -1950, hole_floor + 1), 400, 40, query=start[2] + 100),
    ]
    # A plain door by click: AltarDoor between the entrance hall and the temple.
    altar = d["AltarDoorLeft"]
    centre, _ = m.model("AltarDoorLeft")
    steps += [
        {"note": {"text": f"AltarDoor (doors {altar['door_id']}/{d['AltarDoorRight']['door_id']}, event "
                          f"{altar['event']}): shut, it stops the party; a click opens it; the party walks through."}},
        state(altar["door_id"], "closed"),
        m.walk((0, -800), 90, 1.2, (0, -380, m.floors.z(0, -380, -2000) + 1), 80, 30, query=-2000),
        *m.click("AltarDoorLeft", side=(0, -1, 0), distance=160),
        wait(2.0),
        state(altar["door_id"], "open"),
        m.walk((0, -800), 90, 1.5, (0, 200, m.floors.z(0, 200, -2000) + 1), 200, 40, query=-2000),
    ]
    # LeftDoor: locked until SunButton4 has opened HiddenDoor2.
    left, hidden2 = d["LeftDoor"], d["HiddenDoor2"]
    steps += [
        {"note": {"text": "LeftDoor (MM9 Locked) stays shut on a click; SunButton4 on HiddenDoor2 opens that door and "
                          "unlocks LeftDoor (HiddenDoor2's OpenTrigger), which then opens on its click."}},
        *m.click("LeftDoor", side=(-1, 0, 0), distance=160),
        wait(2.0),
        state(left["door_id"], "closed"),
        *m.click("SunButton4", distance=130),
        wait(1.5),
        state(hidden2["door_id"], "open"),
        var("LeftDoorUnlocked", 1),
        *m.click("LeftDoor", side=(-1, 0, 0), distance=160),
        wait(2.0),
        state(left["door_id"], "open"),
    ]
    # The ladder: from the crypt floor up through the hole to the floor above.
    ladder = next(entry for entry in m.scene.get("ladders", []) if entry["id"] == "Ladder")
    foot = [int(round(ladder["bottom"][0])), int(round(ladder["bottom"][1] + 70)), int(round(ladder["bottom"][2]))]
    top = [int(round(v)) for v in ladder["top_exit"]]
    pose = {"map": MAP, "x": foot[0], "y": foot[1], "z": foot[2] + 1, "yaw_degrees": 270, "pitch": 0}
    steps += [
        {"note": {"text": "Ladder (DAT Ladder): forward climbs from the crypt floor through the hole onto the floor "
                          "above."}},
        {"movement_segment": {"input": "forward", "seconds": 4.0, "actor_collision": False, "actor_ai": False,
                              "start": pose, "expect_stop": dict(pose, x=top[0], y=top[1], z=top[2]),
                              "loose_tolerance": True, "tolerance_xy": 200, "tolerance_z": 40}},
    ]
    return doc


def chests(m: Map) -> dict | None:
    if not m.props:
        return None
    doc = header("chests", "Ruined Temple (native BLV): the three MM9 chests open from in front of them")
    doc["steps"] += scenarios.chest_steps(m.floors, MAP, m.content["chests"], m.props)
    return doc


def scripted(m: Map) -> dict:
    doc = header("scripted", "Ruined Temple (native BLV): sun buttons, hidden doors, the elevator puzzle, the crypt, "
                             "the Tree of Life, the cave-ins, the scrolls, the perception hints, the genie")
    steps = doc["steps"]
    d = m.doors
    hd, hd3 = d["HiddenDoor"]["door_id"], d["HiddenDoor3"]["door_id"]
    hints = m.report["scripted"]["hints"]
    # The doors reopen on contact: the actors within 1200 of HiddenDoor die before its timed close is checked.
    door1, _ = m.model("HiddenDoor")
    near_door1 = [i for i, a in enumerate(m.scene["initial_state"]["actors"])
                  if (a["position"]["x"] - door1[0]) ** 2 + (a["position"]["y"] - door1[1]) ** 2 <= 1200 ** 2]
    steps += [
        {"note": {"text": "The PerceptionBrushes' glow shows at Perception 8 and not below (checked every 3 s)."}},
        {"console": {"line": "skill set Perception 1 B"}}, wait(3.5), var("PerceptionHints", 1),
        {"console": {"line": "skill set Perception 8 E"}}, wait(3.5), var("PerceptionHints", 2),
        {"note": {"text": "SunButton2, on the elevator room's side, is SunButton's DoubleDoorName pair: it opens "
                          "HiddenDoor too (the way back out), which shuts after 10 s. SunButton opens it with both "
                          "buttons riding it, the hint goes off, and 10 s later the door shuts again."}},
        *[{"damage_actor": {"actor_index": i, "amount": 100000, "skip_dead": True}} for i in near_door1],
        *m.click("SunButton2", distance=130), wait(1.5), state(hd, "open"), wait(11), state(hd, "closed"),
        *m.click("SunButton", distance=130), wait(1.5), state(hd, "open"),
        state(d["SunButton"]["door_id"], "open"), state(d["SunButton2"]["door_id"], "open"),
        var(f"HintOff{hints['PerceptionBrush0']}", 1),
        wait(11), state(hd, "closed"), var(f"HintOff{hints['PerceptionBrush0']}", 0),
    ]
    # HiddenDoor3 reopens on contact (MM9's door rule), so a skeleton wandering into its swing keeps it open and the
    # timed close is only checked with the doorway clear: the actors within 1200 of the door die first.
    door3, _ = m.model("HiddenDoor3")
    near_door3 = [i for i, a in enumerate(m.scene["initial_state"]["actors"])
                  if (a["position"]["x"] - door3[0]) ** 2 + (a["position"]["y"] - door3[1]) ** 2 <= 1200 ** 2]
    steps += [
        {"note": {"text": "HiddenButton opens HiddenDoor3 (10 s). The actors near it die first: the door reopens on "
                          "contact, so one standing in its swing would hold it open."}},
        *[{"damage_actor": {"actor_index": i, "amount": 100000, "skip_dead": True}} for i in near_door3],
        *m.click("HiddenButton", distance=110), wait(1.5), state(hd3, "open"),
        wait(11), state(hd3, "closed"),
    ]
    # The elevator puzzle. The party stands on the lift (its top at the temple floor) to press the main button.
    lift = d["MainElevator"]["door_id"]
    centre, _ = m.model("MainElevator")
    button, _ = m.model("MainButton")
    on_lift = (centre[0] + 60, centre[1] - 100)
    # The cab's floor under the stand point (the lift's own upward faces; Floors holds the static floors only).
    stand_lt = m.project.lt_from_native((on_lift[0], on_lift[1], 0))
    cab = [p for p in m.source.polygons("MainElevator") if p.normal[1] > 0.7
           and p.points[:, 0].min() <= stand_lt[0] <= p.points[:, 0].max()
           and p.points[:, 2].min() <= stand_lt[2] <= p.points[:, 2].max()]
    lift_top = int(round(max(p.points[:, 1].max() for p in cab) * 2.56))
    look = math.atan2(button[1] - on_lift[1], button[0] - on_lift[0])
    pitch = math.atan2(button[2] - (lift_top + EYE), math.dist(on_lift, button[:2]))
    press_main = [{"set_pose": {"map": MAP, "x": int(round(on_lift[0])), "y": int(round(on_lift[1])), "z": lift_top + 1,
                                "yaw": round(look, 4), "pitch": round(pitch, 4)}},
                  wait(0.2), {"press_interact": {}}, wait(0.3)]
    steps += [
        {"note": {"text": "The elevator (SunTempleButtons.scr): with no symbol pressed the main button does nothing."}},
        *press_main, wait(1), state(lift, "closed"), var("LiftTrips", 0),
        {"note": {"text": "MoonButton2 pressed: still wrong. Released, then StarButton1 and DiamondButton2 (the two "
                          "the hints mark): the main button sends the lift down with the party on it."}},
        *m.click("MoonButton2", distance=110, query=-2100), var("SymMoon2", 1),
        *press_main, wait(1), state(lift, "closed"),
        *m.click("MoonButton2", distance=110, query=-2100), var("SymMoon2", 0),
        *m.click("StarButton1", distance=110, query=-2100), var("SymStar1", 1),
        var(f"HintOff{hints['PerceptionBrush2']}", 1),
        *m.click("DiamondButton2", distance=110, query=-2100), var("SymDiamond2", 1),
        *press_main, wait(6), state(lift, "open"), var("LiftTrips", 1),
        {"note": {"text": "SecondButton at the foot of the shaft sends the lift back up."}},
        *m.click("SecondButton", distance=120, query=-2700), wait(6), state(lift, "closed"), var("LiftTrips", 2),
    ]
    # The crypt.
    cb = d["WO_CounterBalance"]["door_id"]
    breakable = {e["name"]: e for e in m.scene["destructibles"]}
    steps += [
        {"note": {"text": "PrisonButton2 (RT_CounterBalance.scr): the counterbalance drops onto the crypt lid, which "
                          "breaks (evt.DestroyDestructible; its destroyed event sets CryptOpen); the shaft under it "
                          "is open down to the first dirt plug."}},
        var("CryptOpen", 0),
        *m.click("PrisonButton2", distance=120, query=-2700), wait(2.5),
        var("CryptOpen", 1), wait(2.0), state(cb, "open"),
    ]
    plug0 = breakable[convert.PLUGS[0]]
    steps += [{"note": {"text": "The shaft's dirt plugs (DestructableBrush0-5, scene destructibles of 20 hit points): "
                                "19 damage leave the first standing; standing on each, a click on the dirt at the "
                                "party's feet breaks it (the shared click's killing blow) and the party drops to the "
                                "next."}},
              {"console": {"line": f"destructible {plug0['id']} damage {plug0['hp'] - 1}", "expect_contains": "damage"}},
              wait(0.3), var(f"Broken{convert.PLUGS[0]}", 0)]
    for k, plug in enumerate(convert.PLUGS):
        centre, _ = m.model(plug)
        points = np.array(m.source.models[plug].points, float)
        top = points[:, 1].max() * 2.56
        # stand on the plug's flat west half (x 0..88 LT; its east half is a slope) and look down and west on it
        x, y = centre[0] - 70, centre[1]
        steps += [{"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(top)) + 1,
                                "yaw": round(math.pi, 4), "pitch": round(-math.atan2(EYE, 55), 4)}},
                  wait(0.3), {"press_interact": {}}, wait(3.0), var(f"Broken{plug}", 1),
                  var(f"HintOff{hints[f'PerceptionBrush{k + 4}']}", 1)]
    steps += [
        {"note": {"text": "PrisonButton3 in the tunnel: DoorCryptEscape0 rises (0.5 s + 120 LT at 25 LT/s), then "
                          "the Tree of Life's cell door and bars open."}},
        *m.click("PrisonButton3", distance=120, query=-2700), wait(1),
        state(d["DoorCryptEscape0"]["door_id"], "opening"), wait(5.5),
        state(d["DoorCryptEscape0"]["door_id"], "open"), wait(6),
        state(d["PrisonDoor"]["door_id"], "open"), state(d["PrisonBars"]["door_id"], "open"),
    ]
    if m.props:
        steps += [
            {"note": {"text": f"The Tree of Life (TreeofLife.scr): item {convert.ITEM_TREE}, key {convert.KEY_TREE}; "
                              "it arms TriggerCaveIn1."}},
            *m.click_prop("Treeoflife", distances=(110, 150), height=20),
            {"assert": {"qbit_set": [key(convert.KEY_TREE)]}},
            {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_TREE, "count": 1}]}},
            var("CaveIn1Armed", 1),
        ]
    else:
        steps += [{"execute_event": {"id": convert.EV_TREE}}, wait(1), {"assert": {"qbit_set": [key(convert.KEY_TREE)]}}]
    boxes = m.report["scripted"]["boxes"]

    def into(name, distance=300, yaws=(90, 270, 0, 180, 45, 135, 225, 315)):
        """Walk into a trigger box from the first side whose floor is level and clear for `distance`."""
        lo, hi = boxes[name]
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        z = m.floors.z(cx, cy, hi[2] + 50)
        for yaw in yaws:
            dx, dy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            sx, sy = cx - dx * distance, cy - dy * distance
            sz = m.floors.z(sx, sy, z + 60)
            if sz is not None and abs(sz - z) < 4 and m.floors.clear((sx, sy), (cx, cy), z):
                return m.walk((sx, sy), yaw, distance / scenarios.WALK + 0.25,
                              (cx + dx * 120, cy + dy * 120, z + 1), 240, 40, query=z + 60)
        raise SystemExit(f"no clear approach to {name}")
    def stand_in(name):
        """Set the party down in a trigger box (the spiral stair's foot has no straight level approach)."""
        lo, hi = boxes[name]
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        z = m.floors.z(cx, cy, hi[2] + 50)
        return {"set_pose": {"map": MAP, "x": int(round(cx)), "y": int(round(cy)), "z": int(round(z)) + 1,
                             "yaw": 0.0, "pitch": 0.0}}
    steps += [
        {"note": {"text": "TriggerCaveIn1 (on the way out with the Tree): the ceiling breaks and its rocks drop."}},
        stand_in("TriggerCaveIn1"), wait(4.0), var("CaveIn1Done", 1),
        state(d["CaveInRightB"]["door_id"], "open"), state(d["CaveInLeftB"]["door_id"], "open"),
        {"note": {"text": "TriggerCaveIn0 at the hidden door: the rails break and the rocks drop by the pews."}},
        into("TriggerCaveIn0"), wait(4.0), var("CaveIn0Done", 1),
        state(d["CaveInLeft"]["door_id"], "open"), state(d["CaveInRight"]["door_id"], "open"),
    ]
    if m.props:
        steps += [{"note": {"text": "The scrolls (BookLetter.scr 502, 503) show MM9's texts on a click."}}]
        for name in convert.EV_LETTER:
            steps += [*m.click_prop(name, distances=(100, 140), height=5),
                      {"assert": {"dialog": {"active": True}}}, {"press_action": {"action": "cancel_dialog"}}]
        genie = m.report["scripted"]["genie"]
        gx, gy, gz = m.report["scripted"]["genie_point"]
        steps += [
            {"note": {"text": "The genie (GenieCrystal.scr, ColloidalGenie.scr): hidden until the lamp is used; two "
                              "seconds after the click it stands over the lamp."}},
            {"assert": {"actor_visible": {"actor_index": genie["actor"], "hidden": True}}},
            *m.click_prop("Lamp", distances=(130, 170), height=5),
            var("GenieCalled", 1), wait(2.5), var("GenieShown", 1),
            {"assert": {"actor_visible": {"actor_index": genie["actor"], "hidden": False, "hostile_to_party": False}}},
            {"note": {"text": "A click on the genie opens dialogue 435; the gold wish sets key 5022; closing it grants "
                              "5000 gold (GrantWish) and the genie vanishes 3 s later."}},
            m.pose((gx, gy, gz + 100), (gx, gy - 220), query=gz + 100), wait(0.2), {"press_interact": {}},
            {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": convert.GENIE_RUDE}}},
            choose(convert.GENIE_RUDE, convert.GENIE_RUDE, "You're welcome."),
            choose(convert.GENIE_RUDE, 1, "We'd like more gold."),
            {"assert": {"qbit_set": [key(5022)]}},
            {"press_action": {"action": "cancel_dialog"}}, wait(1),
            var("WishGranted", 1), var("Wish", 1), wait(3.5), var("GenieGone", 1),
            {"assert": {"actor_visible": {"actor_index": genie["actor"], "hidden": True}}},
        ]
    return doc


def main() -> int:
    m = Map()
    for name, builder in (("doors_exits", doors_exits), ("chests", chests), ("scripted", scripted)):
        document = builder(m)
        if document is None:
            print(f"scenario_{name}.yml: skipped (no props.json yet)")
            continue
        scenarios.write(PROJECT / f"scenario_{name}.yml", document, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
