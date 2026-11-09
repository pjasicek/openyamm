#!/usr/bin/env python3
"""
Thjorgard City, MM9 rework: MM9's THJORGARDCITY.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_thjorgardcity/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_thjorgardcity/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the glass and the city settings (roof line, hand cuts); this file adds the
city's own geometry edits (the greenscreen faces behind the facade doors, glass only on MM9's translucent panes),
its population (props.json from ../../props/mm9_thjorgardcity_claude, the townsfolk with their RUDE dialogues) and
the scripted objects as native Lua (citylua.py), each citing its .scr (README.md, "Scripted objects").
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import dungeon  # noqa: E402
from city.hooks import CityHooks  # noqa: E402
from dungeon import rooms  # noqa: E402
from dungeon.bodies import mm9_bodies  # noqa: E402
from dungeon.geometry import clip  # noqa: E402
import liquids  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from mm9_ai_placement import townsperson_walks  # noqa: E402
from mm9_monster_bodies import native_body  # noqa: E402
from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402

PROPS = PROJECT / "props.json"
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/thjorgardcity.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"
LT_TRANSLUCENT = 0x8
GREENSCREEN = "greenscreen.dtx"
# The solid greenscreen faces (flags 0x1081) stand behind six facade doors that never open (Door44 and its like): MM9
# never shows them. As sky faces they would open the sky in a wall; they take the wall texture of the house instead.
GREENSCREEN_WALL = "textures\\a2thjorgaard\\walls\\thjorwallinside7.dtx"
STAND_IN_ROW = 367                  # Peasant Human2 MaleA: an NPC the old import did not place (as Sturmford City)
PEASANT_ROWS = range(301, 383)      # the Peasant family rows (monster_data.txt)
PEACEFUL_ALLY = (352 - 1) // 3 + 1   # monster type of row 352 (Peasant Human1 FemaleB A): neutral to the party
GROUP_TOWNSFOLK = 1


# Glass only on MM9's translucent panes: thjorwindow2/4 and thjorbars also paint opaque windows on facades (flags
# 0x1081, 64 polygons); MM9 draws only the 0x1089 panes (the Invisible boxes of the shop windows) translucent.
_glass_texture = rooms.Glass.texture


def _translucent_glass_texture(self, polygon):
    if not polygon.flags & LT_TRANSLUCENT:
        return None
    return _glass_texture(self, polygon)


rooms.Glass.texture = _translucent_glass_texture


# rooms.crossing_portals with the portal rectangles' boxes computed once per portal list and tested together: the same
# portals in the same order (the same rectangle_points corners), without one numpy meshgrid per polygon and portal.
# The shared version took over 30 minutes here (15 000 polygons, 600+ portals, each tested again after every split).
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


def split_at_walls(polygons: list) -> tuple[list, int]:
    """Cut the faces that run on under walls into other rooms (Klusos House's split_at_walls, for any wall direction).
    MM9 lays a street's floor on under the houses beside it and a house's long wall on behind its partitions; the
    shared converter splits a face only at portal planes or where a second room holds 15 % of its samples, so a strip
    of street floor in front of a facade went to the room inside the house (the street drew the sky through it) and a
    tavern wall behind a storeroom, a corridor and a kitchen went to the storeroom (the corridor drew the sky). Each big
    floor is cut at the plane of every wall standing on it, each big ceiling at every wall under it, each big wall at
    every partition whose end meets it; a cut splits only the pieces the cutting wall reaches. Pieces under or behind
    the walls see no air and are dropped as before."""
    walls = []
    for p in polygons:
        n = p.normal
        if p.role != "static" or abs(n[1]) > 0.01 or np.ptp(p.points[:, 1]) < PARTITION_HEIGHT:
            continue
        horizontal = np.array([n[0], 0.0, n[2]]) / np.hypot(n[0], n[2])
        tangent = np.array([-horizontal[2], 0.0, horizontal[0]])
        along = p.points @ tangent
        walls.append((horizontal, float(horizontal @ p.points[0]), tangent, float(along.min()), float(along.max()),
                      float(p.points[:, 1].min()), float(p.points[:, 1].max())))
    if not walls:
        return polygons, 0
    normals = np.array([w[0] for w in walls])
    distances = np.array([w[1] for w in walls])
    bottoms, tops = np.array([w[5] for w in walls]), np.array([w[6] for w in walls])
    ends = np.array([[w[3], w[4]] for w in walls])                    # the partitions' ends along their tangents
    tangents = np.array([w[2] for w in walls])
    out, splits = [], 0
    for polygon in polygons:
        n = polygon.normal
        kind = "floor" if n[1] > 0.99 else "ceiling" if n[1] < -0.99 else "wall" if abs(n[1]) < 0.01 else None
        if polygon.role != "static" or kind is None or polygon.area < (
                WALL_SPLIT_AREA if kind == "wall" else FLOOR_SPLIT_AREA):
            out.append(polygon)
            continue
        points = polygon.points
        sides = points @ normals.T - distances                      # (points, walls)
        crossing = (sides.min(0) < -4) & (sides.max(0) > 4)
        if kind == "floor":
            touching = np.abs(bottoms - points[0, 1]) < 1.5
        elif kind == "ceiling":
            touching = np.abs(tops - points[0, 1]) < 1.5
        else:
            plane_normal, plane = n / np.linalg.norm(n), float(n @ points[0] / np.linalg.norm(n))
            # a partition meets this wall when one of its ends lies on the wall's plane
            low, high = points[:, 1].min(), points[:, 1].max()
            touching = np.zeros(len(walls), bool)
            candidates = np.flatnonzero(crossing & (np.abs(normals @ plane_normal) < 0.99)
                                        & (bottoms < high - 4) & (tops > low + 4))
            for k in candidates:
                # the partition's end points: its plane point moved along its tangent to each end
                origin = normals[k] * distances[k]
                for end in ends[k]:
                    point = origin + tangents[k] * end
                    # the end's horizontal distance to this wall's plane (y does not matter: both are vertical)
                    if abs(point @ plane_normal - plane) < 1.5:
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


class ThjorgardCity(CityHooks):
    generator = "mm9r_thjorgardcity"
    mover_events = citylua.MOVER_EVENTS

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        polygons = super().edit_polygons(build, polygons)
        wall = build.source.aliases[GREENSCREEN_WALL.lower()]
        changed = 0
        for polygon in polygons:
            if polygon.texture.replace("\\", "/").split("/")[-1].lower() == GREENSCREEN and polygon.flags & 0x10 == 0:
                polygon.texture = wall["source_texture"]
                polygon.notes.update(width=wall["width"], height=wall["height"])
                changed += 1
        build.stats["greenscreen_walls"] = changed
        polygons, splits = split_at_walls(polygons)
        build.stats["city_wall_splits"] = splits
        return polygons

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        if PROPS.exists():
            build.content.props(PROPS, events=citylua.prop_events(build), cogs=citylua.prop_cogs(build))
        else:
            print("note: props.json is missing; no decorations placed")

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """Every townsperson of the DAT: the old import's NPC records (row, name, RUDE dialogue) where it placed them,
        MM9's body (the object's model's initial dims x its Scale, ABC extents), RUDE ids from the object. All
        friendly; they stand where MM9 placed them (MM9's wander rails are not carried)."""
        content, source = build.content, build.source
        old = {a["mm9_source_object_index"]: a for a in
               yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]}
        names = read_mm9_npc_names(NPC_NAMES)
        bodies = mm9_bodies()
        out, self.actor, self.objects, self.rude = [], {}, {}, {}
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
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                height, radius = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
                base["height"], base["radius"] = height, radius
            actor = content.actor(o, base, sector_of_room, group=GROUP_TOWNSFOLK, friendly=True,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = not townsperson_walks(actor.get("mm9_ai") or {})
            if base["monster_id"] not in PEASANT_ROWS:
                # Sven's picture row 520 (BDwarf A) belongs to a family the relation table sets against the
                # party: he refused the click. He takes a peasant family's relations (Hall of the Gods' route).
                actor["ally"] = PEACEFUL_ALLY
            self.actor[name], self.objects[name], self.rude[name] = actor["actor_index"], o["index"], rude
            out.append(actor)
        return out

    def scene(self, build, scene: dict) -> None:
        super().scene(build, scene)
        liquids.apply(build, scene)         # the forge's quench trough (water125) and the palace basins (Water115)

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        return citylua.map_script(self, build)

    def report(self, build) -> dict:
        return dict(super().report(build), scripted={"actors": getattr(self, "actor", {}),
                                                     "objects": getattr(self, "objects", {}),
                                                     "rude": getattr(self, "rude", {})})


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, ThjorgardCity()))
