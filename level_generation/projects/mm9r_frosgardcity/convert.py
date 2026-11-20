#!/usr/bin/env python3
"""
Frosgard City, MM9 rework: MM9's FROSGARDCITY.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_frosgardcity/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_frosgardcity/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the glass and the city settings (roof line, street box); this file adds the
city's own geometry (the near box and the far scenery, the harbour's sea to swim in, glass only on MM9's translucent
panes, the wall splits), its population (props.json from ../../props/mm9_frosgardcity_claude, the townsfolk with their
RUDE dialogues) and the scripted objects as native Lua (citylua.py), each citing its .scr (README.md, "Scripted
objects").

**The near box and the far scenery.** MM9's Frosgard City is a harbour town on a frozen bay: the sky shell spreads
31 232 x 17 408 LT over the sea (x -12 800..18 432: past the BLV's int16 frame, which ends at 12 799 LT) and Terrain0's
mountains ring the bay. A 16 LT voxel pass over all of it would be 845 M voxels. MM9 itself draws only 2 500 LT far
(WorldProperties FarZ, grey fog from 1 to 2 000 LT). So:

- the voxel pass, the rooms and the face assignment cover only NEAR_BOX: the town, the north gate, the harbour inside
  its fence (InvisibleBrush1) down to its bed and the air up to 800 LT (over every roof; the town's highest is 656).
  Polygons are clipped at the box; the grid's outer layer is solid (`_sealed_build_voxels`), so the air ends at the box;
- the parts outside it (the mountains above 800 LT and beyond the box, the bay's ocean surface beyond it) are the far
  scenery: kept as faces of the open-air room round the town (`_assign_with_far`), clipped to |x|, |z| <= FAR_LIMIT_LT
  (inside int16). Far parts under the ocean surface (the sea bed), far sky faces (MM9's shell: the sky is drawn behind
  the scene anyway) and far invisible faces (the fence's top, nobody reaches it) are dropped.
- **The ocean** (the Ocean brush, Ocean4.spr at Alpha 0.8, non-solid over the BlueWater volume), drawn by the liquid
  shader (../mm9r_common/liquids.py), in 1 024 LT tiles. Inside the box the party swims and dives in it: the box reaches
  under the harbour's bed (MM9's world at -528 LT, Terrain0's slopes), so the shared water rule (dungeon/water.py,
  Build.swim_surfaces) finds a bed under every tile and makes the tiles non-solid; the fence (InvisibleBrush1, down to
  -512) keeps a swimmer in the harbour. Past the box the far sea stays a solid surface with no bed (unreachable).
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
import dungeon.build as dungeon_build  # noqa: E402
from city.hooks import CityHooks  # noqa: E402
from dungeon import rooms  # noqa: E402
from dungeon.bodies import mm9_bodies  # noqa: E402
from dungeon.geometry import air_regions, clip, mark, sample_polygon, VoxelGrid  # noqa: E402
import liquids  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from mm9_ai_placement import townsperson_walks  # noqa: E402
from mm9_monster_bodies import native_body  # noqa: E402
from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402

PROPS = PROJECT / "props.json"
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/frosgardcity.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"
LT_TRANSLUCENT = 0x8
GREENSCREEN = "greenscreen.dtx"
SKY_TEXTURE = "skymarker.dtx"
STAND_IN_ROW = 367                  # Peasant Human2 MaleA: an NPC the old import did not place (as Sturmford City)
PEASANT_ROWS = range(301, 383)      # the Peasant family rows (monster_data.txt)
PEACEFUL_ALLY = (352 - 1) // 3 + 1   # monster type of row 352 (Peasant Human1 FemaleB A): neutral to the party
GROUP_TOWNSFOLK = 1
FORAD_RUDE = 2

# The voxel pass's box (LithTech x, y, z): the town (x -1 700..5 650, z -2 600..2 250), the north gate's pocket (to z
# 5 376), the harbour inside its fence (InvisibleBrush1: x -5 056..8 768, z -6 336..-704), from under the harbour's bed
# (-528: the water is swum, README "Swimming") to over the highest roof (656).
NEAR_BOX = (np.array([-5200.0, -560.0, -6500.0]), np.array([9000.0, 800.0, 5440.0]))
FAR_LIMIT_LT = 12700.0              # far scenery is clipped here: 32 512 native, inside the BLV's int16 frame
OCEAN_MODEL = "Ocean"
OCEAN_Y = -143.0                    # the ocean surface (LT)
OCEAN_TILE_LT = 1024.0
OPEN_AIR_POINT = (2000.0, 780.0, 0.0)   # a point in the open air over the town: the room the far scenery joins


# Glass only on MM9's translucent panes: frosgardwindow2 also paints 12 opaque facade windows (flags 0x1081); MM9
# draws only the magic shop's two 0x1109 panes translucent (Thjorgard City's rule).
_glass_texture = rooms.Glass.texture


def _translucent_glass_texture(self, polygon):
    if not polygon.flags & LT_TRANSLUCENT:
        return None
    return _glass_texture(self, polygon)


rooms.Glass.texture = _translucent_glass_texture


# rooms.crossing_portals with the portal rectangles' boxes computed once per portal list and tested together: the same
# portals in the same order (Thjorgard City's map-local version; the shared one is slow on a city).
_portal_boxes = {}


def _crossing_portals(polygon, portals, voxel):
    key = (id(portals), len(portals), voxel)
    boxes = _portal_boxes.get(key)
    if boxes is None:
        corners = [rooms.rectangle_points(p["centre"], p["axis_a"], p["half_a"] + voxel, p["axis_b"],
                                          p["half_b"] + voxel, 1e9) for p in portals]
        boxes = (portals, np.array([c.min(0) for c in corners]), np.array([c.max(0) for c in corners]))
        _portal_boxes.clear()
        _portal_boxes[key] = boxes
    _, box_low, box_high = boxes
    low, high = polygon.points.min(0) - 2 * voxel, polygon.points.max(0) + 2 * voxel
    near = ~((box_high < low).any(1) | (box_low > high).any(1))
    candidates = []
    for k in np.flatnonzero(near):
        portal = portals[k]
        side = polygon.points @ portal["normal"] - portal["normal"] @ portal["centre"]
        if side.min() < -0.5 and side.max() > 0.5:
            candidates.append(portal)
    return candidates


rooms.crossing_portals = _crossing_portals


# --- the near box: a sealed voxel pass, the far scenery joins the open air ----------------------------------------
FAR = {"polygons": []}


def _sealed_build_voxels(polygons, source, extra_seeds=()):
    """rooms.build_voxels with the grid's outer layer solid: the near polygons are clipped at NEAR_BOX, so the air
    ends at the box instead of leaking to the grid's border (the far scenery is not voxelised)."""
    voxel = source.project.voxel
    points = np.concatenate([p.points for p in polygons])
    grid = VoxelGrid(points.min(0), points.max(0), voxel)
    solid = np.zeros(grid.shape, bool)
    for polygon in polygons:
        if polygon.role == "static":
            mark(grid, solid, sample_polygon(polygon.points, voxel / 4))
    solid[[0, -1], :, :] = True
    solid[:, [0, -1], :] = True
    solid[:, :, [0, -1]] = True
    seeds = []
    classes = source.project.seed_classes | source.project.monster_classes
    excluded = {name.lower() for name in (source.project.overrides.get("seed_exclude") or [])}
    for o in source.objects:
        if o["class"] in classes and o["name"].lower() not in excluded:
            seeds.append(o["properties"]["Pos"])
    seeds += [list(s) for s in extra_seeds]
    air, stats = air_regions(grid, solid, np.array(seeds, float))
    return grid, solid, air, stats


dungeon_build.build_voxels = _sealed_build_voxels
_assign_faces = dungeon_build.assign_faces


def _assign_with_far(rooms_, polygons, portals, stats, log, **kwargs):
    """The shared face assignment for the near polygons; the far scenery goes whole to the open-air room."""
    kept = _assign_faces(rooms_, polygons, portals, stats, log, **kwargs)
    label = rooms_.owner(np.array(OPEN_AIR_POINT))
    for polygon in FAR["polygons"]:
        polygon.label = label
    stats["far_scenery_faces"] = len(FAR["polygons"])
    stats["far_scenery_room"] = int(label)
    return kept + FAR["polygons"]


dungeon_build.assign_faces = _assign_with_far


def _clip_box(polygon, low, high, key):
    """The polygon's part inside the box and its parts outside (convex pieces)."""
    inside, outside = polygon, []
    for axis in range(3):
        for sign, bound in ((1.0, low[axis]), (-1.0, high[axis])):
            if inside is None:
                break
            normal = np.zeros(3)
            normal[axis] = sign
            front, back = clip(inside, normal, sign * bound, f"{key}{axis}{int(sign)}")
            if back is not None:
                outside.append(back)
            inside = front
    return inside, outside


def _tiles(polygon, size: float, key: str) -> list:
    """A horizontal polygon cut into size x size LT tiles (x and z)."""
    pieces = [polygon]
    for axis in (0, 2):
        lo, hi = polygon.points[:, axis].min(), polygon.points[:, axis].max()
        for cut in np.arange(np.ceil(lo / size) * size, hi, size):
            normal = np.zeros(3)
            normal[axis] = 1.0
            out = []
            for piece in pieces:
                front, back = clip(piece, normal, float(cut), f"{key}{axis}")
                out += [p for p in (front, back) if p is not None]
            pieces = out
    return pieces


def near_and_far(build, polygons: list) -> list:
    """Split the merged polygons at NEAR_BOX: the near parts are returned (voxels, rooms, faces), the far parts kept
    in FAR (see the module docstring), clipped to FAR_LIMIT_LT, minus the sea bed, the far sky and invisible faces."""
    low, high = NEAR_BOX
    near, far = [], []
    for k, polygon in enumerate(polygons):
        inside, outside = _clip_box(polygon, low, high, f"nb{k}")
        if inside is not None:
            near.append(inside)
        far += outside
    limit = np.array([FAR_LIMIT_LT, 1e9, FAR_LIMIT_LT])
    kept, dropped = [], {"sea_bed": 0, "sky": 0, "invisible": 0, "past_int16": 0}
    for k, polygon in enumerate(far):
        texture = polygon.texture.replace("\\", "/").split("/")[-1].lower()
        if texture == SKY_TEXTURE:
            dropped["sky"] += 1
            continue
        if polygon.role == "invisible":
            dropped["invisible"] += 1
            continue
        if polygon.points[:, 1].max() < OCEAN_Y - 1:
            dropped["sea_bed"] += 1
            continue
        inside, _ = _clip_box(polygon, -limit, limit, f"fl{k}")
        if inside is None:
            dropped["past_int16"] += 1
            continue
        kept.append(inside)
    FAR["polygons"] = kept
    build.stats["near_polygons"] = len(near)
    build.stats["far_scenery_polygons"] = len(kept)
    build.stats.update({f"far_dropped_{key}": value for key, value in dropped.items()})
    return near


class FrosgardCity(CityHooks):
    generator = "mm9r_frosgardcity"
    mover_events = citylua.MOVER_EVENTS

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        # The 10 solid greenscreen polygons (two small boxes on the western mountain at 567-606 LT): MM9's renderer
        # zones, never drawn.
        before = len(polygons)
        polygons = [p for p in polygons
                    if p.texture.replace("\\", "/").split("/")[-1].lower() != GREENSCREEN]
        build.stats["greenscreen_dropped"] = before - len(polygons)
        # The ocean, in tiles (one face over the bay would span 36 000 native): static here; the shared water rule
        # makes the tiles over the harbour's bed non-solid (Build.swim_surfaces).
        out, ocean = [], 0
        for k, polygon in enumerate(polygons):
            if polygon.model == OCEAN_MODEL:
                polygon.role = "static"
                tiles = _tiles(polygon, OCEAN_TILE_LT, f"oc{k}")
                ocean += len(tiles)
                out += tiles
            else:
                out.append(polygon)
        build.stats["ocean_tiles"] = ocean
        polygons = super().edit_polygons(build, out)        # half steps
        from convert_walls import split_at_walls
        polygons, splits = split_at_walls(polygons)
        build.stats["city_wall_splits"] = splits
        return near_and_far(build, polygons)

    def extra_portals(self, build) -> list:
        """No street structure: Frosgard has no town wall and no streets between continuous facades. Its houses stand
        free on one snow field that runs on into the shore, the harbour and the north gate, so the street air under
        any roof line joins the open air all round (the first plan pass, street box and roof line at 200 LT: no
        corridor for a street cut, nothing divided). The open air is one room; the walk-in interiors are rooms behind
        their doors and windows (README, "Structure")."""
        build.city_report = {"structure": "none: one open-air room (convert.py FrosgardCity.extra_portals)"}
        return []

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        if PROPS.exists():
            build.content.props(PROPS, events=citylua.prop_events(build), cogs=citylua.prop_cogs(build))
        else:
            print("note: props.json is missing; no decorations placed")
        # Trigger0 (BattleMan.scr :OnFight2, the touch line across the square south of the temple)
        trigger = build.source.by_name["trigger0"]["properties"]
        build.content.pad("Trigger0", trigger["Pos"], trigger["Dims"], citylua.EV_TRIGGER0)

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
            if name == "ForadDarre" and not rude:
                rude = FORAD_RUDE           # Forad.scr's (commented) DoRude 2: NPC2.rude is Forad Darre's dialogue
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                height, radius = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
                base["height"], base["radius"] = height, radius
            group = {"ForadDarre": citylua.GROUP_FORAD, "TamurLeng0": citylua.GROUP_TAMUR}.get(name, GROUP_TOWNSFOLK)
            actor = content.actor(o, base, sector_of_room, group=group, friendly=True,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = not townsperson_walks(actor.get("mm9_ai") or {})
            if base["monster_id"] not in PEASANT_ROWS:
                # Picture rows of hostile families (Tamur Leng, Forad Darre, Tryggva): peaceful relations of a
                # peasant family, or the click is refused (Hall of the Gods' route).
                actor["ally"] = PEACEFUL_ALLY
            self.actor[name], self.objects[name], self.rude[name] = actor["actor_index"], o["index"], rude
            out.append(actor)
        return out

    def scene(self, build, scene: dict) -> None:
        super().scene(build, scene)
        liquids.apply(build, scene)         # the ocean (Ocean4) and the well

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        return citylua.map_script(self, build)

    def report(self, build) -> dict:
        return dict(super().report(build), scripted={"actors": getattr(self, "actor", {}),
                                                     "objects": getattr(self, "objects", {}),
                                                     "rude": getattr(self, "rude", {})})


if __name__ == "__main__":
    hooks = FrosgardCity()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        import transport                    # the boat routes into the docks (transport.py)
        transport.main()
        import cutscenes                    # BreakIce.scr's cinema, Bob and Doug (citylua.scenes; README "Cinematics")
        print(f"cinematics installed: {cutscenes.install('frosgardcity', citylua.scenes(hooks.actor))}")
    sys.exit(code)
