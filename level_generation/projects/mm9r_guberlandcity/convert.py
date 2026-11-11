#!/usr/bin/env python3
"""
Guberland City, MM9 rework: MM9's GUBERLANDCITY.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_guberlandcity/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_guberlandcity/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the glass and the city settings (roof line, cuts); this file adds the city's own
geometry edits (glass only on MM9's translucent panes, faces cut at the walls standing on them, the bank's counter
bars as an untouchable cut-out), its population (props.json from ../../props/mm9_guberlandcity_claude, the fish
tank's water, the townsfolk and guards with their RUDE dialogues) and the scripted objects as native Lua
(citylua.py), each citing its .scr (README.md, "Scripted objects").

Map-local fixes carried over from Thjorgard City (glass on translucent panes, split_at_walls, the cached
crossing-portal test, the DOORS table keyed by strings, peaceful relations for NPCs on hostile picture rows) and
Thronheim City (large floors cut at the walls standing on them, with a 16 LT foot).
"""

from __future__ import annotations

import dataclasses
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from city.hooks import CityHooks  # noqa: E402
from dungeon import rooms  # noqa: E402
from dungeon.bodies import mm9_bodies  # noqa: E402
from dungeon.geometry import Polygon, clip  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from mm9_ai_placement import townsperson_walks  # noqa: E402
from mm9_monster_bodies import native_body  # noqa: E402
from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402

PROPS = PROJECT / "props.json"
# Markel on his throne (seat_markel): the throne's seat centre from its props.json x (MM9's Throne.ABC posed: x -64..79
# about its box centre), the council chairs' seat-to-sitter distance, the throne seat's rise over a chair's (71 - 50)
MARKEL_THRONE = "Throne0"
THRONE_SEAT_CENTRE = 7.0
CHAIR_TO_SITTER = 38.0
THRONE_SEAT_RISE = 21.0
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/guberlandcity.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"
LT_TRANSLUCENT = 0x8
STAND_IN_ROW = 367                  # Peasant Human2 MaleA: an NPC the old import did not place (as Sturmford City)
PEASANT_ROWS = range(301, 383)      # the Peasant family rows (monster_data.txt)
PEACEFUL_ALLY = (352 - 1) // 3 + 1   # monster type of row 352 (Peasant Human1 FemaleB A): neutral to the party
GUARD_CLASS, GUARD_ROW = "PoorTownGuard1", 9107       # MM9 107 Town Guard (L20): MM9's PoorTownGuard1
GROUP_TOWNSFOLK, GROUP_GUARDS = 1, 2
TANK_MODEL = "BlueWater0"           # the magic shop's fish tank (BlueWater, ShowSurface, SurfaceAlpha 0.7)
TANK_TEXTURE = "water:tank"           # overrides.yml textures: Water115 (MM9 draws Water115flowing.spr)
BARS_MODEL = "WorldObject1"         # the bank's counter bars (MetalBar in an invisible shell, MM9 solid)
# The Guberland Players' stage in the tavern (benchwood at 32 LT = 82 native over the hall's floor, x -1248..-800,
# its front edge at z -1568 under the curtain): MM9's player steps up 40-48 LT, the party 50 native. One invisible step
# (top at 16 LT = 41 native, 20 LT deep) along the front lets the party onto it (CITY_PLAYBOOK "Raised floors": a
# standable floor 67-127 over its floor gets a hand-made step).
STAGE_STEP_LT = {"x": (-1240.0, -808.0), "z": (-1588.0, -1568.0), "low": 0.0, "top": 16.0}


def float_property(value) -> float:
    """A float MM9 stores in an int property (NPCNbr 1124859904 = 140.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


# Glass only on MM9's translucent panes (Thjorgard City): MM9 draws only the 0x8-flagged panes translucent; the
# same window textures also paint opaque windows on facades.
_glass_texture = rooms.Glass.texture


def _translucent_glass_texture(self, polygon):
    if not polygon.flags & LT_TRANSLUCENT:
        return None
    return _glass_texture(self, polygon)


rooms.Glass.texture = _translucent_glass_texture


# rooms.crossing_portals with the portal rectangles' boxes computed once per portal list and tested together: the same
# portals in the same order (Thjorgard City; the shared version took over 30 minutes on a city).
_portal_boxes = {}


def _crossing_portals(polygon, portals, voxel):
    key = (id(portals), len(portals), voxel)
    boxes = _portal_boxes.get(key)
    if boxes is None:
        # a portal with `split_boxes` (the merged top portals, city/structure.py) is tested by those boxes, as the
        # shared version does
        entries = []
        for p in portals:
            if "split_boxes" in p:
                entries += [(p, name, corners) for name, corners in p["split_boxes"]]
            else:
                entries.append((p, None, rooms.rectangle_points(p["centre"], p["axis_a"], p["half_a"] + voxel,
                                                                p["axis_b"], p["half_b"] + voxel, 1e9)))
        boxes = (entries, np.array([c.min(0) for _, _, c in entries]).reshape(-1, 3),
                 np.array([c.max(0) for _, _, c in entries]).reshape(-1, 3))
        _portal_boxes.clear()
        _portal_boxes[key] = boxes
    entries, box_low, box_high = boxes
    low, high = polygon.points.min(0) - 2 * voxel, polygon.points.max(0) + 2 * voxel
    near = ~((box_high < low).any(1) | (box_low > high).any(1))
    candidates = []
    for k in np.flatnonzero(near):
        portal, name, _ = entries[k]
        side = polygon.points @ portal["normal"] - portal["normal"] @ portal["centre"]
        if side.min() < -0.5 and side.max() > 0.5:
            candidates.append(portal if name is None else dict(portal, name=name))
    return candidates


rooms.crossing_portals = _crossing_portals


# Faces that run on under walls into other rooms (split_at_walls below)
FLOOR_SPLIT_AREA = 4000             # LT²: floors and ceilings this big are cut at the walls standing on or under them
WALL_SPLIT_AREA = 4000              # LT²: walls this big are cut at the partitions whose ends meet them
PARTITION_HEIGHT = 48               # LT: walls at least this tall (not beams, kerbs or sills)
WALL_FOOT_LT = 16                   # LT: a wall stands on a floor when its foot is at most this far over it (Thronheim)


def split_at_walls(polygons: list) -> tuple[list, int]:
    """Cut the faces that run on under walls into other rooms (Thjorgard City's split_at_walls, with Thronheim City's
    floor rule). MM9 lays a street's floor on under the houses beside it, a house's long wall on behind its
    partitions and one sloped ceiling over a row of rooms; the shared converter splits a face only at portal planes or
    where a second room holds 15 % of its samples, so a strip of street floor in front of a facade goes to the room
    inside the house (the street draws the sky through it). Each big floor is cut at the plane of every wall standing
    on it (its foot at most 16 LT over the floor or below it, reaching 48 LT over it), each big ceiling at every wall
    under it (a sloped one at every partition with two corners on its plane), each big wall at every partition whose
    end meets it; a cut splits only the pieces the cutting wall reaches. Pieces under or behind the walls see no air
    and are dropped as before."""
    walls, wall_points = [], []
    for p in polygons:
        n = p.normal
        if p.role != "static" or abs(n[1]) > 0.01 or np.ptp(p.points[:, 1]) < PARTITION_HEIGHT:
            continue
        horizontal = np.array([n[0], 0.0, n[2]]) / np.hypot(n[0], n[2])
        tangent = np.array([-horizontal[2], 0.0, horizontal[0]])
        along = p.points @ tangent
        walls.append((horizontal, float(horizontal @ p.points[0]), tangent, float(along.min()), float(along.max()),
                      float(p.points[:, 1].min()), float(p.points[:, 1].max())))
        wall_points.append(p.points)
    if not walls:
        return polygons, 0
    normals = np.array([w[0] for w in walls])
    distances = np.array([w[1] for w in walls])
    bottoms, tops = np.array([w[5] for w in walls]), np.array([w[6] for w in walls])
    ends = np.array([[w[3], w[4]] for w in walls])
    tangents = np.array([w[2] for w in walls])
    out, splits = [], 0
    for polygon in polygons:
        n = polygon.normal
        kind = ("floor" if n[1] > 0.99 else "ceiling" if n[1] < -0.99 else "wall" if abs(n[1]) < 0.01
                else "slope" if n[1] < -0.3 else None)
        if polygon.role != "static" or kind is None or polygon.area < (
                WALL_SPLIT_AREA if kind == "wall" else FLOOR_SPLIT_AREA):
            out.append(polygon)
            continue
        points = polygon.points
        sides = points @ normals.T - distances                      # (points, walls)
        crossing = (sides.min(0) < -4) & (sides.max(0) > 4)
        if kind == "floor":
            height = float(points[0, 1])
            touching = (bottoms <= height + WALL_FOOT_LT) & (tops >= height + PARTITION_HEIGHT)
        elif kind == "ceiling":
            touching = np.abs(tops - points[0, 1]) < 1.5
        elif kind == "slope":
            # a sloped ceiling (a roof's underside over several rooms): the partitions whose top corners lie on its
            # plane (the tavern's side rooms under one lean-to ceiling)
            unit = n / np.linalg.norm(n)
            plane = float(unit @ points[0])
            touching = np.zeros(len(walls), bool)
            for k in np.flatnonzero(crossing):
                touching[k] = bool((np.abs(wall_points[k] @ unit - plane) < 1.5).sum() >= 2)
        else:
            plane_normal, plane = n / np.linalg.norm(n), float(n @ points[0] / np.linalg.norm(n))
            low, high = points[:, 1].min(), points[:, 1].max()
            touching = np.zeros(len(walls), bool)
            candidates = np.flatnonzero(crossing & (np.abs(normals @ plane_normal) < 0.99)
                                        & (bottoms < high - 4) & (tops > low + 4))
            for k in candidates:
                origin = normals[k] * distances[k]
                for end in ends[k]:
                    if abs((origin + tangents[k] * end) @ plane_normal - plane) < 1.5:
                        touching[k] = True
        pieces = [polygon]
        for k in np.flatnonzero(crossing & touching):
            normal, distance, tangent, start, end = walls[k][:5]
            key = f"cw{np.round(normal, 3).tolist()}{round(distance, 1)}"
            cut = []
            for piece in pieces:
                if kind == "wall":
                    reach_low, reach_high = piece.points[:, 1].min(), piece.points[:, 1].max()
                    reached = bottoms[k] < reach_high - 4 and tops[k] > reach_low + 4
                else:
                    along = piece.points @ tangent
                    reached = start < along.max() - 4 and end > along.min() + 4
                if reached:
                    front, back = clip(piece, normal, distance, key)
                    cut += [part for part in (front, back) if part is not None]
                else:
                    cut.append(piece)
            pieces = cut
        splits += len(pieces) - 1
        out += pieces
    return out, splits


class GuberlandCity(CityHooks):
    generator = "mm9r_guberlandcity"
    own_water_surfaces = (TANK_MODEL,)      # the tank's surface is built here (no shared drawn_surfaces face)
    mover_events = citylua.MOVER_EVENTS

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        polygons = super().edit_polygons(build, polygons)
        # The bank's counter bars (MetalBar in an Invisible shell): talking through bars (The Arena). The shell and
        # the solid bars stop the pick, so the banker behind them could not be clicked; the shell is dropped and the
        # bars become an untouchable cut-out (the counter keeps the party out); the scene draws them as cut-outs.
        kept, bars = [], 0
        for polygon in polygons:
            if polygon.model == BARS_MODEL:
                if polygon.role == "invisible":
                    continue
                polygon = dataclasses.replace(polygon, role="nonsolid")
                bars += 1
            kept.append(polygon)
        build.stats["bank_bars_nonsolid"] = bars
        kept += self.stage_step(kept)
        polygons, splits = split_at_walls(kept)
        build.stats["city_wall_splits"] = splits
        return polygons

    @staticmethod
    def stage_step(polygons: list) -> list:
        """The invisible step in front of the tavern's stage (STAGE_STEP_LT): a top and a riser, as the city's half
        steps (../mm9r_common/city/hooks.py) are built."""
        invisible = next(p for p in polygons if p.role == "invisible")
        s = STAGE_STEP_LT
        (x0, x1), (z0, z1), low, top = s["x"], s["z"], s["low"], s["top"]
        rings = ((np.array([[x0, top, z0], [x0, top, z1], [x1, top, z1], [x1, top, z0]]), np.array([0.0, 1.0, 0.0])),
                 (np.array([[x0, low, z0], [x1, low, z0], [x1, top, z0], [x0, top, z0]]), np.array([0.0, 0.0, -1.0])))
        out = []
        for ring, want in rings:
            face = Polygon(ring, [tuple(np.round(q, 1)) for q in ring], invisible.texture, invisible.mapping,
                           invisible.flags, "StageStep", "invisible")
            if face.normal @ want < 0:
                ring = ring[::-1].copy()
                face = Polygon(ring, [tuple(np.round(q, 1)) for q in ring], invisible.texture, invisible.mapping,
                               invisible.flags, "StageStep", "invisible")
            face.notes.update(invisible.notes)
            out.append(face)
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        if PROPS.exists():
            build.content.props(PROPS, events=citylua.prop_events(build), cogs=citylua.prop_cogs(build))
        else:
            print("note: props.json is missing; no decorations placed")
        self.tank(build)
        self.points = citylua.marker_points(build)

    def tank(self, build) -> None:
        """The fish tank's water: the top face of MM9's BlueWater0 volume (ShowSurface, SurfaceAlpha 0.7,
        Water115flowing.spr) as an untouchable face, drawn see-through by the liquid shader (../mm9r_common/liquids.py:
        Water115 at 0.7; Sturmford City's well)."""
        project, package = build.project, build.package
        points = np.array(build.source.models[TANK_MODEL].points, float)
        top = points[:, 1].max()
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        ring = np.array([[x0, top, z0], [x0, top, z1], [x1, top, z1], [x1, top, z0]])
        native = np.round(project.native(ring)).astype(np.int64)
        if np.cross(native[1] - native[0], native[2] - native[0])[2] < 0:
            native, ring = native[::-1], ring[::-1]
        key = package.material(TANK_TEXTURE)[0]
        node = f"TRIGGER_water_{TANK_MODEL}"
        package.nodes[node].append((native, ring[:, [0, 2]] - ring[:, [0, 2]].min(0), key))
        room = build.content.owner(np.array([(x0 + x1) / 2, top - 4, (z0 + z1) / 2]))
        package.room_nodes[room].append(node)
        package.metadata["surfaces"].append({"id": TANK_MODEL, "source_node": node, "flags": ["untouchable"]})
        build.content.report["water"] = {"model": TANK_MODEL, "room": room, "z": int(native[0][2])}

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """Every townsperson and guard of the DAT: the old import's NPC records (row, name, RUDE dialogue) where it
        placed them, MM9's body (the object's model's initial dims x its Scale, ABC extents), RUDE ids from the object
        (NPCNbr). All friendly; they stand where MM9 placed them (MM9's wander rails, the guards' wall patrols and the
        players' theatre walks are not carried). NPCs on rows of a monster family take a peasant's relations."""
        content, source = build.content, build.source
        old = {a["mm9_source_object_index"]: a for a in
               yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]
               if "mm9_source_object_index" in a}
        names = read_mm9_npc_names(NPC_NAMES)
        bodies = mm9_bodies()
        out, self.actor, self.objects, self.rude = [], {}, {}, {}
        self.players = {}           # the Guberland Players (citylua.PLAYERS): DAT name -> scene actor
        for o in source.objects:
            if o["class"] not in build.project.monster_classes:
                continue
            name, p = o["name"], o["properties"]
            record = old.get(o["index"])
            if record is not None:
                rude = int(record.get("mm9_rude_id") or 0)
                base = {key: record[key] for key in ("name", "attributes", "hp", "hostility_type", "monster_info_id",
                                                     "monster_id", "radius", "height", "move_speed")}
            else:
                rude = mm9_npc_rude_id({key: p.get(key) for key in ("DoRude", "ScriptName", "GreetingSound",
                                                                      "NPCNbr")})
                base = {"name": names.get(rude, name), "attributes": 0, "hp": 20, "hostility_type": 0,
                        "monster_info_id": STAND_IN_ROW, "monster_id": STAND_IN_ROW, "radius": 43, "height": 120,
                        "move_speed": 0}
            group = GROUP_TOWNSFOLK
            if o["class"] == GUARD_CLASS:
                base["monster_id"] = base["monster_info_id"] = GUARD_ROW
                base["name"] = "Town Guard"
                group = GROUP_GUARDS
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                height, radius = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
                base["height"], base["radius"] = height, radius
            actor = content.actor(o, base, sector_of_room, group=group, friendly=True,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = not townsperson_walks(actor.get("mm9_ai") or {})
            if base["monster_id"] not in PEASANT_ROWS:
                # Rows of monster families (Markel's 579, the guards' 9107, 439 Wizards...) belong to families the
                # relation table may set against the party: they take a peasant family's relations (Hall of the Gods).
                actor["ally"] = PEACEFUL_ALLY
            self.actor[name], self.objects[name], self.rude[name] = actor["actor_index"], o["index"], rude
            if name in citylua.PLAYERS:
                self.players[name] = actor
            out.append(actor)
        self.seat_markel(out)
        return out

    def seat_markel(self, actors: list) -> None:
        """NPC127.scr loops Sit (dungeon/lua.py init_poses plays it). MM9 places Markel 157 units in front of his
        throne's centre, and the HD Sit clip is grounded at the actor, so he sat on the floor in front of it (a player's
        report, 2026-11-08). He sits on it as the council Jarls sit on their chairs: 38 units in front of the seat's
        centre (Thronheim's chairs), raised by how much higher the throne's seat is than such a chair's (MM9's models:
        Throne.ABC 71 over its base, Chair.abc 50), posed so the game neither drops nor pushes him."""
        throne = next(e for e in json.loads(PROPS.read_text()) if e["source_name"] == MARKEL_THRONE)
        actor = next(a for a in actors if a["actor_index"] == self.actor["MarkeltheGreat0"])
        yaw = math.radians(actor["initial_yaw_units"] / 2048 * 360)
        x = throne["x"] + THRONE_SEAT_CENTRE + CHAIR_TO_SITTER * math.cos(yaw)
        y = throne["y"] + CHAIR_TO_SITTER * math.sin(yaw)
        actor["position"] = {"x": int(round(x)), "y": int(round(y)),
                             "z": int(round(throne["z"] + THRONE_SEAT_RISE))}
        actor["posed"] = True

    def scene(self, build, scene: dict) -> None:
        super().scene(build, scene)
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        citylua.bars_cutout(build, blv, scene)
        liquids.apply(build, scene)

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        return citylua.map_script(self, build)

    def report(self, build) -> dict:
        return dict(super().report(build), scripted={"actors": getattr(self, "actor", {}),
                                                     "objects": getattr(self, "objects", {}),
                                                     "rude": getattr(self, "rude", {})})


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, GuberlandCity()))
