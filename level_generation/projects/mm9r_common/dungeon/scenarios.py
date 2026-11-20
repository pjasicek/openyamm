"""
Scenario helpers for a built dungeon (headless `--headless-run-scenario` YAML): floor queries on the DAT floors,
level approaches that walk onto a plate or pad, the tops of movers in the compiled BLV, and the chest steps (stand
in front of each chest model, look at it, press interact, expect that chest to open).

    ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/<project>/scenario_<name>.yml --scenario-no-color
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import yaml

from .content import PAD_LIFT
from .source import ROOT, SCALE, Project, Source, classify_models, floor_below

EYE = 160
WALK = 768                      # party speed in scenarios (always run: units per second)


class Floors:
    def __init__(self, project: Project):
        self.project = project
        source = Source(project)
        plan = classify_models(source)
        polygons = [p for m in plan["static"] for p in source.polygons(m)]
        self.floors = [p for p in polygons if p.normal[1] >= 0.7 and p.role == "static"]

    def z(self, x, y, z_from):
        """The floor (native z) under a native point, searched from z_from down."""
        point = self.project.lt_from_native((x, y, z_from))
        found = floor_below(self.floors, (point[0], point[1] + 1, point[2]))
        return None if found is None else found * SCALE - self.project.offset[2]

    def clear(self, a, b, z) -> bool:
        """The floor from a toward b stays at height z (no step, no hole on the way); the last stretch is the
        target's own plate or pad, which may be a mover."""
        for t in np.linspace(0, 0.6, 7):
            p = np.asarray(a, float) + t * (np.asarray(b, float) - np.asarray(a, float))
            found = self.z(p[0], p[1], z + 40)
            if found is None or abs(found - z) > 2:
                return False
        return True


def movement(map_name, start, yaw, seconds, stop, tolerance_xy=60, tolerance_z=16) -> dict:
    """A forward walk from start (native x, y, z) facing yaw degrees, expected to stop near `stop`."""
    pose = {"map": map_name, "x": int(round(start[0])), "y": int(round(start[1])), "z": int(round(start[2])),
            "yaw_degrees": round(yaw, 1), "pitch": 0}
    return {"movement_segment": {"input": "forward", "seconds": seconds, "actor_collision": False, "actor_ai": False,
                                 "start": pose, "expect_stop": dict(pose, x=int(round(stop[0])), y=int(round(stop[1])),
                                                                    z=int(round(stop[2]))),
                                 "loose_tolerance": True, "tolerance_xy": tolerance_xy, "tolerance_z": tolerance_z}}


def walk_onto(floors: Floors, map_name, target, name, distance=220, avoid=()):
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
        return movement(map_name, (start[0], start[1], z + 1), yaw, round(distance / WALK, 2), (x, y, z + 1))
    raise SystemExit(f"{name}: no level approach")


def floor_of(pad: dict) -> list:
    """A trigger pad's centre on the floor under it (pads stand PAD_LIFT over it)."""
    x, y, z = pad["centre"]
    return [x, y, z - PAD_LIFT]


def door_tops(runtime: Path, map_name: str, stem: str) -> dict:
    """door id -> the centre of its highest horizontal face (a plate's top), native."""
    import sys
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(runtime / map_name)["payload"]
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
    faces = {f["index"]: f for f in blv["faces"]}
    scene = json.loads((runtime / f"{stem}.scene.yml").read_text())
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


def _segment_distance(a, b, p) -> float:
    a, b, p = np.asarray(a, float), np.asarray(b, float), np.asarray(p, float)[:2]
    t = np.clip((p - a) @ (b - a) / max((b - a) @ (b - a), 1e-9), 0.0, 1.0)
    return float(np.linalg.norm(a + t * (b - a) - p))


def look_at(floors: Floors, map_name, target, yaw_degrees_of_model, distances=(150,), height=25,
            max_drop: float = 120, avoid=()) -> dict:
    """A pose in front of a model (its facing first, then its sides, then diagonals) on a floor at most max_drop below
    the model's base, looking at it (an object on an altar stands above the floor in front of it). avoid: native
    (x, y) points (actors) that must stay 90 units off the line of sight and 300 beyond the target, so interact does
    not hit them."""
    cx, cy, cz = target
    yaw = math.radians(yaw_degrees_of_model)
    directions = [(math.cos(yaw + math.pi / 2 + k * math.pi / 4), math.sin(yaw + math.pi / 2 + k * math.pi / 4))
                  for k in (0, 2, -2, 4, 1, -1, 3, -3)]
    for distance in distances:
        for fx, fy in directions:
            x, y = cx + fx * distance, cy + fy * distance
            z = floors.z(x, y, cz + 200)
            beyond = (cx + (cx - x) / distance * 300, cy + (cy - y) / distance * 300)   # a missed ray goes on
            blocked = any(_segment_distance((x, y), beyond, a) < 90 for a in avoid)
            if z is not None and abs(z - cz) < max_drop and not blocked:
                look = math.atan2(cy - y, cx - x)
                pitch = math.atan2(cz + height - (z + EYE), math.dist((x, y), (cx, cy)))
                return {"set_pose": {"map": map_name, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                                     "yaw": round(look, 4), "pitch": round(pitch, 4)}}
    raise SystemExit(f"no floor in front of {target}")


def world_item(scene: dict, source_name: str) -> dict:
    """The scene's `world_items` entry of a DAT object (dungeon/pickups.py)."""
    return next(i for i in scene.get("world_items", []) if i["source_name"] == source_name)


def pick_up_steps(floors: Floors, map_name, scene: dict, source_name: str, distances=(90, 120, 150), avoid=(),
                  facing_degrees: float = 0) -> list:
    """Stand in front of a world item (a pickup prop, dungeon/pickups.py), look at it and press interact: picked up as
    any ground item. The caller asserts what it gave. facing_degrees: the model yaw look_at searches in front of
    (an item on a shelf against a wall: the side the room is on)."""
    item = world_item(scene, source_name)
    p = item["position"]
    # a posed item (a shield leaning on a wall) stands up from its position: aim at its middle, not its foot
    height = 50 if "pose" in item else 4
    return [look_at(floors, map_name, (p["x"], p["y"], p["z"]), facing_degrees, distances=distances, height=height,
                    max_drop=200, avoid=avoid),
            {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 0.3}}]


def chest_steps(floors: Floors, map_name, chests: list, props: dict, direct: set = frozenset()) -> list:
    """For each chest (content.json chests), stand in front of its model and press interact (or, for chests in
    `direct`, run its event: headless picking does not see moved doors), then expect it open and close the dialog."""
    steps = []
    for chest in chests:
        entry = props[chest["anchor"]]
        steps.append(look_at(floors, map_name, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"]))
        steps.append({"execute_event": {"id": chest["event"]}} if chest["anchor"] in direct else {"press_interact": {}})
        steps += [{"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    return steps


def clear_monsters(actors: list, centre, radius: float = 1500, height: float = 400) -> list:
    """damage_actor steps that kill the monsters (scene initial_state actors without an NPC) within `radius` (x, y)
    and `height` (z) of a native point. A monster that follows the party through an AITriggerable door or trap opens
    it again (BaseDoor.inc `Trigger door, Use`), as in MM9: a check of the door's own timing clears the room first."""
    cx, cy, cz = centre
    return [{"damage_actor": {"actor_index": a["actor_index"], "amount": 100000, "skip_dead": True}}
            for a in actors if not a.get("npc_id")
            and math.dist((a["position"]["x"], a["position"]["y"]), (cx, cy)) < radius
            and abs(a["position"]["z"] - cz) < height]


class Sight:
    """Straight lines of sight on the compiled BLV (work/runtime/<stem>.blv): a line is clear when no wall face (not a
    portal, not a mover) crosses it at the party's eye or an actor's chest height."""

    def __init__(self, project: Project):
        import sys
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        runtime = project.work / "runtime"
        blv = parse_blv_file(runtime / f"{project.stem}.blv")["payload"]
        scene = json.loads((runtime / f"{project.stem}.scene.yml").read_text())
        movers = {f for door in scene["initial_state"]["doors"] for f in door["face_ids"]}
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)
        self.walls = []
        for f in blv["faces"]:
            poly = vertices[f["vertex_indices"]]
            if len(poly) < 3 or f["is_portal"] or f["index"] in movers:
                continue
            normal = np.cross(poly[1] - poly[0], poly[2] - poly[0])
            for k in range(2, len(poly) - 1):
                normal = normal + np.cross(poly[k] - poly[0], poly[k + 1] - poly[0])
            if abs(normal[2]) < 0.7 * max(np.linalg.norm(normal), 1e-9):     # walls, not floors or slopes
                self.walls.append(poly)

    @staticmethod
    def _crosses(poly: np.ndarray, a, b, z: float) -> bool:
        if poly[:, 2].min() > z or poly[:, 2].max() < z:
            return False
        points = []
        for k in range(len(poly)):
            p, q = poly[k], poly[(k + 1) % len(poly)]
            if (p[2] - z) * (q[2] - z) < 0:
                points.append(p[:2] + (z - p[2]) / (q[2] - p[2]) * (q[:2] - p[:2]))
        if len(points) < 2:
            return False
        c, d = points[0], points[1]

        def side(o, e, p):
            return (e[0] - o[0]) * (p[1] - o[1]) - (e[1] - o[1]) * (p[0] - o[0])

        return side(a, b, c) * side(a, b, d) < 0 and side(c, d, a) * side(c, d, b) < 0

    def clear(self, a, b, z: float) -> bool:
        a, b = np.asarray(a[:2], float), np.asarray(b[:2], float)
        low, high = np.minimum(a, b) - 1, np.maximum(a, b) + 1
        for poly in self.walls:
            if (poly[:, 0].max() < low[0] or poly[:, 0].min() > high[0] or poly[:, 1].max() < low[1]
                    or poly[:, 1].min() > high[1]):
                continue
            if self._crosses(poly, a, b, z + 60) or self._crosses(poly, a, b, z + EYE):
                return False
        return True


def thorolf_document(project: Project, floors: Floors, map_name: str, header: dict, indices: dict, actors: dict,
                     key, start=None) -> dict:
    """scenario_thorolf.yml: NPC378.scr (Thorolf Ratatoskssen, the messenger, dungeon/lua.py thorolf_approaches).
    :Init shows Thorolf0/1 with key 83 until 84 (only Frosgard's third copy comes after Tamur Leng, key 106, through
    NPC309.scr's Appear trigger); OnFoundPlayer :OnFound runs him to the party (RunTo 16) and :Talk opens RUDE 378
    with no click and removes the other copy. The party stands where one copy (Thorolf0 where a floor in his sight
    allows) sees it, the other out of sight; first the two states in which MM9 shows neither: 106 alone, and 83 with
    84 (the message delivered).
    `indices`/`actors`: DAT name -> actor index / native position; `start`: Thorolf0's position with key 83 when the
    map moves him there (Thronheim City's fix), else his placement."""
    sight = Sight(project)
    pose = None
    for runner, twin in (("Thorolf0", "Thorolf1"), ("Thorolf1", "Thorolf0")):
        tx, ty, tz = (start if runner == "Thorolf0" else None) or actors[runner]
        for distance in (700, 600, 500, 420):
            for k in range(16):
                angle = k * math.pi / 8
                x, y = tx + math.cos(angle) * distance, ty + math.sin(angle) * distance
                z = floors.z(x, y, tz + 100)
                if (z is None or abs(z - tz) > 150 or math.dist((x, y), actors[twin][:2]) < 2200
                        or not sight.clear((x, y), (tx, ty), max(z, tz))):
                    continue
                pose = (x, y, z, math.atan2(ty - y, tx - x))
                break
            if pose:
                break
        if pose:
            break
    if pose is None:
        raise SystemExit(f"{map_name}: no floor in either Thorolf's sight")
    x, y, z, yaw = pose
    thorolf0, thorolf1 = indices[runner], indices[twin]

    def stand() -> dict:
        return {"set_pose": {"map": map_name, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                             "yaw": round(yaw, 4), "pitch": 0.0}}

    def bits(*keys) -> list:
        return [{"setup_shortcut": {"kind": "set_qbit", "id": key(k), "value": k in keys}} for k in (83, 84, 106)]

    doc = dict(header)
    # the header's load_map first (a quest bit set before any map is loaded does not reach the party); the states
    # where he must not come run first, while neither copy has been removed
    doc["steps"] = list(header["steps"])
    for keys, why in (((106,), "106 alone (Tamur Leng met, no message yet): :Init shows him only with 83"),
                      ((83, 84), "83 with 84 (the message delivered): :Init hides him")):
        doc["steps"] += [
            {"note": {"text": f"NPC378.scr: {why}; nobody comes and no dialogue opens."}},
            *bits(*keys),
            {"load_map": {"map": map_name}},
            {"advance_runtime": {"seconds": 1.0}},
            stand(),
            {"advance_runtime": {"seconds": 7.0, "present_dialogs": True}},
            {"assert": {"dialog": {"active": False}}},
            {"assert": {"actor_visible": {"actor_index": thorolf0, "hidden": True}}},
            {"assert": {"actor_visible": {"actor_index": thorolf1, "hidden": True}}},
        ]
    doc["steps"] += [
        {"note": {"text": f"NPC378.scr :Init with key 83: both copies shown; {runner} sees the party, runs over "
                          f"(RunTo 16) and opens RUDE 378 himself; {twin} is removed."}},
        *bits(83),
        {"load_map": {"map": map_name}},
        {"advance_runtime": {"seconds": 1.0}},
        {"assert": {"actor_visible": {"actor_index": thorolf0, "hidden": False}}},
        {"assert": {"actor_visible": {"actor_index": thorolf1, "hidden": False}}},
        stand(),
        {"advance_runtime": {"seconds": 7.0, "present_dialogs": True}},
        {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": 378}}},
        {"assert": {"dialog": {"active": True, "source_id": 378}}},
        # he came over: off his place, beside the party
        {"assert": {"actor_visible": {"actor_index": thorolf0, "hidden": False,
                                      "far": {"x": int(round(tx)), "y": int(round(ty)), "min_distance": 200},
                                      "near": {"x": int(round(x)), "y": int(round(y)), "max_distance": 260}}}},
        {"assert": {"actor_visible": {"actor_index": thorolf1, "hidden": True}}},
        # :OnRude: with 83 alone the dialogue opens again (it cannot be skipped); once the message is delivered (84)
        # its close sends him away by town portal
        {"note": {"text": "NPC378.scr :OnRude: with 84 the dialogue's close sends him away (Vanish)."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(84), "value": True}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 0.5, "present_dialogs": True}},
        {"assert": {"dialog": {"active": False}}},
        {"assert": {"actor_visible": {"actor_index": thorolf0, "hidden": True}}},
    ]
    return doc


def write(path: Path, document: dict, writer: str) -> None:
    path.write_text(f"# Written by {writer} from the built map; rerun it after convert.py.\n"
                    + yaml.safe_dump(document, sort_keys=False, width=120))
    print(path)
