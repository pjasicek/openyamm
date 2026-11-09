#!/usr/bin/env python3
"""
Write the Inventa Storca scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json); doors, switches, chests and pickups are clicked from in front of them (look, press interact):

    scenario_doors_exits.yml   the exit to Thronheim; a shut double door stops the party, opens on a click and is
                               walked through; DoubleDoor9 also sets the Lich King on the dying adventurer; the
                               trapdoor stops a climb up Ladder5 and, clicked open, lets the party out on top; a
                               cracked wall breaks on a click
    scenario_chests.yml        the three chests and two treasure bags open from in front of them (the bags' niches and
                               the chests' floor compartment opened first by their secret switches)
    scenario_scripted.yml      the scripted objects: perception hints, an Orb of Linking, a letter, the bookcase domino,
                               the scurrying basilisks, the ickies, both bust-outs, the spook triggers and the Lich
                               King's kill, the dead adventurers, the cavern's water

    python3 level_generation/projects/mm9r_inventastorca/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_inventastorca/scenario_$s.yml --scenario-no-color; done
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
from dungeon import scenarios, water  # noqa: E402
from dungeon.source import ROOT, Project  # noqa: E402
import convert  # noqa: E402

MAP = "inventastorca.blv"
EXIT_OBJECT = 452                   # ExitTrigger0 (DAT object index; its map_transitions.txt row)


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.inventastorca_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


class Map:
    def __init__(self):
        self.project = Project.load(PROJECT, install=False)
        self.floors = scenarios.Floors(self.project)
        self.movers = {m["node"][5:]: m for m in json.loads((PROJECT / "work/doors.json").read_text())}
        self.content = json.loads((PROJECT / "work/content.json").read_text())
        self.report = json.loads((PROJECT / "work/build_report.json").read_text())
        self.scene = json.loads((PROJECT / "work/runtime/inventastorca.scene.yml").read_text())
        self.props = {e["source_name"]: e for e in json.loads((PROJECT / "work/props_unique.json").read_text())}
        self.pads = {p["anchor"]: p for p in self.content["pads"]}
        self.actor = self.report["scripted"]["actors"]
        self.actors_xy = [(a["position"]["x"], a["position"]["y"]) for a in self.scene["initial_state"]["actors"]]
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(PROJECT / "work/runtime/inventastorca.blv")["payload"]
        self.vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
        self.faces = {f["index"]: f for f in blv["faces"]}
        self.door_faces = {d["door_id"]: d["face_ids"] for d in self.scene["initial_state"]["doors"]}

    def door(self, node: str) -> int:
        return self.movers[node]["door_id"]

    def cog_faces(self, cog: int) -> list:
        """The faces carrying a cog (a scene destructible's: dungeon/destructibles.py `break`)."""
        return [i for i, f in self.faces.items() if f["face_param"].get("cog_number") == cog]

    def mover_face(self, node: str, face_ids=None):
        """The centre of a mover's largest face and its horizontal normal (native); face_ids: other faces instead (a
        destructible's)."""
        best = None
        face_ids = self.door_faces[self.door(node)] if face_ids is None else face_ids
        for fid in face_ids:
            points = self.vertices[self.faces[fid]["vertex_indices"]]
            normal = np.cross(points[1] - points[0], points[2] - points[0])
            area = np.linalg.norm(normal)
            if area < 1e-6 or abs(normal[2]) / area > 0.5:
                continue
            if best is None or area > best[0]:
                best = (area, points.mean(0), normal / area)
        if best is None:                                    # a flat mover (a floor panel): its top's centre
            points = np.concatenate([self.vertices[self.faces[f]["vertex_indices"]] for f in face_ids])
            return points.mean(0), None
        return best[1], best[2]

    def click_mover(self, node: str, distances=(140, 190), side=None, aim_z=None, face_ids=None) -> list:
        """Stand in front of a mover and press interact. side: the native (x, y) direction from the mover to stand in
        (a push switch: against its MoveDir); else both sides of its largest upright face are tried. The floor stood
        on must lie under the aim point (not a shelf above it)."""
        centre, normal = self.mover_face(node, face_ids)
        aim = centre[2] if aim_z is None else aim_z
        sides = [np.asarray(side, float)] if side is not None else \
            ([normal[:2], -normal[:2]] if normal is not None else [np.array(v, float) for v in ((1, 0), (-1, 0), (0, 1), (0, -1))])
        for distance in distances:
            for direction in sides:
                direction = direction / np.linalg.norm(direction)
                x, y = centre[0] + direction[0] * distance, centre[1] + direction[1] * distance
                z = self.floors.z(x, y, aim + 10)
                if z is None or not (aim - 300 < z < aim + 10):
                    continue
                yaw = math.atan2(centre[1] - y, centre[0] - x)
                pitch = math.atan2(aim - (z + scenarios.EYE), distance)
                return [{"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                                      "yaw": round(yaw, 4), "pitch": round(pitch, 4)}},
                        {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]
        raise SystemExit(f"no place to click {node}")

    def click_prop(self, anchor: str, distances=(110, 150), height=10, yaw=None) -> list:
        """yaw: the model yaw look_at assumes (it stands first along yaw + 90 degrees): for things in wall niches."""
        entry = self.props[anchor]
        return [scenarios.look_at(self.floors, MAP, (entry["x"], entry["y"], entry["z"]),
                                  entry["yaw_degrees"] if yaw is None else yaw,
                                  distances=distances, height=height, max_drop=200, avoid=self.actors_xy),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}]

    def walk_pad(self, anchor: str, first=None) -> list:
        """A walk onto a pad from just outside it, along the pad's shorter side first (a party starting under a
        pad's plane never steps onto it)."""
        pad = self.pads[anchor]
        x, y, z = scenarios.floor_of(pad)
        half_x, half_y = pad["size"][0] / 2, pad["size"][1] / 2
        sides = [((0, -1), half_y), ((0, 1), half_y), ((-1, 0), half_x), ((1, 0), half_x)]
        sides.sort(key=lambda side: (side[0] != first, side[1]))
        for (dx, dy), half in sides:
            distance = half + 90
            start = (x + dx * distance, y + dy * distance)
            floor = self.floors.z(start[0], start[1], z + 40)
            if floor is None or abs(floor - z) > 12 or not self.floors.clear(start, (x, y), z):
                continue
            yaw = math.degrees(math.atan2(-dy, -dx)) % 360
            return [scenarios.movement(MAP, (start[0], start[1], z + 1), yaw, round(distance / scenarios.WALK, 2),
                                       (x, y, z + 1), 80, 16), {"advance_runtime": {"seconds": 0.5}}]
        raise SystemExit(f"{anchor}: no level approach")


def state(door_id: int, value: str) -> dict:
    return {"assert": {"mechanism": {"id": door_id, "state": value}}}


def var(name: str, value: int) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def doors_exits(m: Map) -> dict:
    doc = header("doors_exits", "Inventa Storca (native BLV) - the exit, a double door, the trapdoor over Ladder5, a "
                                "cracked wall")
    steps = doc["steps"]
    start = m.report["starts"][0]["position"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 452): the way back to Thronheim, south of the start."}},
              scenarios.movement(MAP, start, 278, 1.0, (451, -676, -676), 500, 300),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    # DoubleDoor1: the lower library, between the stair hall and the north hall (leaves at LT z -1032).
    left, right = m.door("DoubleDoorL1"), m.door("DoubleDoorR1")
    centre, normal = m.mover_face("DoubleDoorL1")
    z = m.floors.z(-240 * 2.56, -1100 * 2.56, -600 * 2.56)
    before = (-240 * 2.56, -1250 * 2.56, z + 1)
    steps += [{"note": {"text": f"DoubleDoor1 (doors {left}, {right}) is shut and stops the party walking north."}},
              state(left, "closed"), state(right, "closed"),
              scenarios.movement(MAP, before, 90, 1.0, (before[0], -1032 * 2.56 - 60, z + 1), 90, 30),
              {"note": {"text": "A click on the leaf opens both; the party walks through."}},
              *m.click_mover("DoubleDoorL1"),
              {"advance_runtime": {"seconds": 2.5}},
              state(left, "open"), state(right, "open"),
              scenarios.movement(MAP, before, 90, 1.2, (before[0], before[1] + 900, z + 1), 160, 40)]
    # DoubleDoor9 (upper floor, the dead adventurers' hall): its OpenTrigger is the Lich King's Kill.
    steps += [{"note": {"text": "DoubleDoor9: a click opens it and sends the Lich King's Kill (LichKills = 1)."}},
              *m.click_mover("DoubleDoorL9"),
              {"advance_runtime": {"seconds": 2.5}},
              state(m.door("DoubleDoorL9"), "open"),
              var("LichKills", 1),
              {"assert": {"actor_visible": {"actor_index": m.actor["LKToKillGreenParty0"], "hostile_to_party": True}}}]
    # Ladder5 and its trapdoor.
    ladder = next(entry for entry in m.scene["ladders"] if entry["id"] == "Ladder5")
    hatch = m.door("LadderDoor")
    facing = math.radians(ladder["facing_degrees"])
    foot = [int(round(ladder["bottom"][0] - math.cos(facing) * 60)),
            int(round(ladder["bottom"][1] - math.sin(facing) * 60)), int(round(ladder["bottom"][2]))]
    top = [int(round(v)) for v in ladder["top_exit"]]

    def climb(seconds, stop, tolerance_xy, tolerance_z):
        pose = {"map": MAP, "x": foot[0], "y": foot[1], "z": foot[2] + 1, "yaw_degrees": ladder["facing_degrees"],
                "pitch": 0}
        return {"movement_segment": {"input": "forward", "seconds": seconds, "actor_collision": False, "actor_ai": False,
                                     "start": pose, "expect_stop": dict(pose, x=stop[0], y=stop[1], z=stop[2]),
                                     "loose_tolerance": True, "tolerance_xy": tolerance_xy, "tolerance_z": tolerance_z}}
    steps += [{"note": {"text": "Ladder5: the shut trapdoor (LadderDoor) stops the climb under it."}},
              state(hatch, "closed"),
              climb(4.0, (int(ladder["bottom"][0]), int(ladder["bottom"][1]), int(ladder["top"][2]) - 220), 120, 120),
              {"note": {"text": "The trapdoor clicked from above slides open (its OpenTrigger: PerceptionBrush9 off); "
                                "the party climbs out on top."}},
              *m.click_mover("LadderDoor", distances=(110, 150), aim_z=-338 * 2.56 + 8),
              {"advance_runtime": {"seconds": 3}},
              state(hatch, "open"),
              climb(3.0, top, 1000, 60)]   # z: out on top; it steps on forward over the shaft wall
    # A cracked wall.
    walls = {d["name"]: d for d in m.scene["destructibles"]}
    wall = walls["DestructableBrush0"]
    steps += [{"note": {"text": "DestructableBrush0 (the entrance corridor's cracked wall into the cave; a scene "
                                "destructible): standing, a click breaks it (the shared click's killing blow), its "
                                "destroyed event sets Broken0 and turns PerceptionBrush0 off."}},
              var("Broken0", 0),
              *m.click_mover("DestructableBrush0", face_ids=m.cog_faces(wall["cog"])),
              {"advance_runtime": {"seconds": 1}},
              var("Broken0", 1), var("HintOffPerceptionBrush0", 1)]
    wall = walls["DestructableBrush2"]
    steps += [{"note": {"text": f"DestructableBrush2 ({wall['hp']} hit points) by weapons: one short of its hit points it "
                                "stands; one more breaks it (Broken2)."}},
              {"console": {"line": f"destructible {wall['id']} damage {wall['hp'] - 1}", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 0.5}}, var("Broken2", 0),
              {"console": {"line": f"destructible {wall['id']} damage 1", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 0.5}}, var("Broken2", 1)]
    return doc


def chests(m: Map) -> dict:
    doc = header("chests", "Inventa Storca (native BLV) - the three chests and two treasure bags open")
    steps = doc["steps"]
    by_anchor = {c["anchor"]: c for c in m.content["chests"]}

    def open_chest(anchor, direct=False, **kw):
        """direct: behind a moved panel, opened by its event (headless picking follows door motion only while
        frames render: playbook gotchas)."""
        c = by_anchor[anchor]
        click = [{"execute_event": {"id": c["event"]}}] if direct else m.click_prop(anchor, **kw)
        return [*click, {"assert": {"chest_opened": {"chest_id": c["container_id"]}}},
                {"press_action": {"action": "cancel_dialog"}}]
    steps += [{"note": {"text": "Chest0 in the west reading room."}}, *open_chest("Chest0")]
    steps += [{"note": {"text": "SecretSwitch (a book on the wall) swings SecretPanel open; TreasureBag1 is in the niche."}},
              *m.click_mover("SecretSwitch", distances=(90, 120), side=(-1, 0)),
              {"advance_runtime": {"seconds": 3}},
              state(m.door("SecretPanel"), "open"),
              *open_chest("TreasureBag1", direct=True, distances=(150, 180), height=10, yaw=90)]
    steps += [{"note": {"text": "SecretSwitch0 swings SecretPanel0 open; TreasureBag0 is in its niche."}},
              *m.click_mover("SecretSwitch0", distances=(90, 120), side=(0, 1)),
              {"advance_runtime": {"seconds": 3}},
              state(m.door("SecretPanel0"), "open"),
              *open_chest("TreasureBag0", direct=True, distances=(150, 180), height=10, yaw=0)]
    steps += [{"note": {"text": "SecretSwitch1 (a book on FallingBookcase4) slides SecretPanel1 off the floor "
                                "compartment holding Chest1 and Chest2."}},
              *m.click_mover("SecretSwitch1", distances=(90, 120), side=(0, -1)),
              {"advance_runtime": {"seconds": 3}},
              state(m.door("SecretPanel1"), "open"),
              *open_chest("Chest1", direct=True),
              *open_chest("Chest2", direct=True)]
    return doc


def scripted(m: Map) -> dict:
    doc = header("scripted", "Inventa Storca (native BLV) - hints, orbs, a letter, bookcases, critters, bust-outs, the "
                             "Lich King's kill, the dead adventurers, the cavern's water")
    steps = doc["steps"]
    a = m.actor
    steps += [{"note": {"text": "The dead adventurers (GreenParty.scr: Die at launch) lie dead; the dying one lives."}},
              *[{"assert": {"actor_visible": {"actor_index": a[n], "dead": True}}} for n in sorted(convert.DEAD)],
              {"assert": {"actor_visible": {"actor_index": a["GreenPartyDude0"], "dead": False,
                                          "hostile_to_party": False}}},
              {"assert": {"actor_visible": {"actor_index": a["LKToKillGreenParty0"], "hostile_to_party": False}}},
              {"note": {"text": "Perception hints: hidden at Perception 1, shown at 8 (PerceptionValue 8)."}},
              {"console": {"line": "skill set Perception 1 B"}},
              {"advance_runtime": {"seconds": 3.5}},
              var("HintSkill", 1)]
    steps += [{"console": {"line": "skill set Perception 8 B"}}, {"advance_runtime": {"seconds": 3.5}},
              var("HintSkill", 8)]
    # An orb, by a click.
    orb = "Prop4"
    steps += [{"note": {"text": f"Orb.scr: {orb}, a world item, picked up: an Orb of Linking (item 252)."}},
              *m.click_prop(orb, distances=(90, 120), height=15),
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_ORB, "count": 1}]}}]
    # A letter.
    steps += [{"note": {"text": "BookLetter.scr: Prop8 shows MM9's letter 495 (On Visitors from Space)."}},
              *m.click_prop("Prop8", distances=(90, 120), height=5),
              {"advance_runtime": {"seconds": 0.5}},
              {"press_action": {"action": "cancel_dialog"}}]
    # Bookcases.
    cases = [m.door(f"FallingBookcase{k}") for k in range(1, 7)]
    steps += [{"note": {"text": "FallingBookcaseSwitch topples FallingBookcase1-6 one a second; its riders fall with them."}},
              *m.click_mover("FallingBookcaseSwitch", distances=(90, 120), side=(0, -1)),
              {"advance_runtime": {"seconds": 0.5}},
              state(cases[0], "opening"), state(cases[5], "closed"),
              {"advance_runtime": {"seconds": 9}},
              *[state(c, "open") for c in cases],
              state(m.door("FallingBookcaseSwitch"), "open"),
              var("Domino", 6)]
    # Critters.
    scurry = [a[n] for n in a if n.startswith("ScurryBasilisk") and int(n[-1]) < 3]
    brood = [a[n] for n in a if n.startswith("BrettBird")]
    steps += [{"note": {"text": "ScurryTrigger0: three small basilisks run off and vanish (ScurryCreature.scr Hide)."}},
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": False}}} for i in scurry],
              *m.walk_pad("ScurryTrigger0"),
              var("ScurryTrigger0", 1),
              {"advance_runtime": {"seconds": 1}},     # running for HideMarker0 (:GoHide's RunTo)
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": False, "far": {
                  "x": m.actors_xy[i][0], "y": m.actors_xy[i][1], "min_distance": 48}}}} for i in scurry],
              {"advance_runtime": {"seconds": 25}},    # there: RemoveObject
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": True}}} for i in scurry],
              {"note": {"text": "BirdTrigg0 (in the cave shaft): the five resting ickies scatter and are gone."}},
              {"execute_event": {"id": convert.EV_BIRDS["BirdTrigg0"]}},
              {"advance_runtime": {"seconds": 0.5}},
              *[{"assert": {"actor_visible": {"actor_index": i, "hidden": True}}} for i in brood]]
    # Bust-outs.
    bust0, bust1 = a["BustOutLich0"], a["BustOutLichKing0"]
    steps += [{"note": {"text": "BustOutTrigger0: the cage wall (DestructableBrush4) gives way; BustOutLich0 wakes."}},
              *m.walk_pad("BustOutTrigger0"),
              {"advance_runtime": {"seconds": 2}},
              var("BustOut0", 1),
              {"assert": {"actor_visible": {"actor_index": bust0, "hostile_to_party": True}}},
              {"note": {"text": "BustOutTrigger1: the ceiling slab drops away and the Lich King and two skeletons stand "
                                "under the hole."}},
              {"assert": {"actor_visible": {"actor_index": bust1, "hidden": True}}},
              {"execute_event": {"id": convert.EV_BUSTOUT["BustOutTrigger1"]}},
              {"advance_runtime": {"seconds": 1.5}},
              {"assert": {"actor_visible": {"actor_index": bust1, "hidden": False}}}]
    # The Lich King's kill.
    steps += [{"note": {"text": "SpookTrigger5: the Lich King turns on the dying adventurer and on the party."}},
              *m.walk_pad("SpookTrigger5", first=(0, 1)),
              var("LichKills", 1),
              {"assert": {"actor_visible": {"actor_index": a["LKToKillGreenParty0"], "hostile_to_party": True}}},
              {"advance_runtime": {"seconds": 8}},    # the adventurer is on his last hit point: the first blow kills
              {"assert": {"actor_visible": {"actor_index": a["GreenPartyDude0"], "dead": True}}},
              {"note": {"text": "SpookTrigger0: a spook sound, once."}},
              {"execute_event": {"id": convert.EV_SPOOK["SpookTrigger0"]}},
              var("SpookTrigger0", 1)]
    # The cavern's water.
    if water.swimming(m.project):
        # The shared water rule: MM9's swim, from the cavern (BlueWater1) east into the flooded channel (BlueWater2),
        # south along it and up the well (BlueWater0) into the niche beside the lower library.
        S = 2.56

        def seg(start, yaw, seconds, keys="forward", **extra):
            pose = {"map": "inventastorca.blv", "x": round(start[0] * S), "y": round(start[1] * S),
                    "z": round(start[2] * S), "yaw": yaw, "pitch": 0.0}
            return {"movement_segment": {"input": keys, "seconds": seconds, "actor_collision": False,
                                         "actor_ai": False, "start": pose, "expect_stop": dict(pose),
                                         "loose_tolerance": True, "tolerance_xy": 4000, "tolerance_z": 4000, **extra}}
        steps += [{"note": {"text": "The cavern's water is swum (MM9): from its bed east into the flooded channel, south "
                                    "along it under the rock and up the well into the niche."}},
                  seg((-1250, -900, -900), 0.0, 0.3, keys="none"),
                  {"assert": {"water": {"eye_under": True}}},
                  seg((-1250, -900, -900), 0.0, 1.0),
                  {"assert": {"water": {"eye_under": True}}},
                  seg((-1072, -900, -900), -1.5708, 2.0),
                  {"assert": {"party_position": {"x": round(-1072 * S), "y": round(-1184 * S), "radius": 160}}},
                  seg((-1072, -1184, -900), -1.5708, 2.5, keys="none", fly_up=True),
                  {"assert": {"water": {"state": "surface", "eye_under": False, "breath_min": 0.99}}}]
    else:
        steps += [{"note": {"text": "The cavern's water: a party on it is moved to the well's shore."}},
                  {"execute_event": {"id": convert.EV_SWIM}},
                  {"advance_runtime": {"seconds": 1}},
                  var("Swam", 1)]
    return doc


def main() -> int:
    m = Map()
    for name, builder in (("doors_exits", doors_exits), ("chests", chests), ("scripted", scripted)):
        scenarios.write(PROJECT / f"scenario_{name}.yml", builder(m), "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
