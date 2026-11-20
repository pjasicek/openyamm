"""
The MM9 dungeon -> native BLV conversion, run by a map project's convert.py:

    python3 level_generation/projects/<project>/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/<project>/convert.py --plan     # analysis and room plans only
    python3 level_generation/projects/<project>/convert.py --scratch DIR   # build and compile into DIR, no install

A map project is a directory with overrides.yml (section `map` plus the model rules, archway cuts, exits) and a
convert.py that subclasses `Hooks` for its own population and scripts, then calls `main(directory, hooks)`.
Geometry is MM9's PhysicsBSP and the static world models, merged back from BSP fragments into convex polygons. Rooms
are the air of the map divided at its doorways and archway cuts; every face goes to the room in front of it. The
source package (GLB + geometry metadata) is compiled with build/tools/mm9_compile_indoor_source and installed with
its scene, Lua and the map's table rows into output/mm9_rework/assets_dev. See ../DUNGEON_PLAYBOOK.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import yaml

import review_root

from . import (ambient, density, destructibles, objects, people, perception, spr_surfaces, tables, treasure,
               wall_splits, water)
from .geometry import Polygon, drop_unshared_collinear, merge_coplanar, poly_ring, sample_polygon
from .lights import MAX_LIGHTS_PER_POINT, build_lights, light_coverage, perception_lights, pulsing_lights
from .movers import build_movers
from .floors import cut_floors_under_overlays, cut_floors_under_ramps, floor_holes, invisible_bottoms, weld_floor_cracks
from .package import SourcePackage, face_rings, room_id
from .rooms import (Glass, NearestRoom, archway_portals, assign_faces, build_voxels, door_portals, doorway_floors,
                    draw_plan, floor_mismatches, glass_backed, glass_portals, label_rooms, portal_corners,
                    portal_side_faces, portal_sides, restore_continuations, shared_rooms, split_straddling_portals,
                    uncovered_barriers)
from .rotation import ladder_records, rectangle_portals
from .source import ROOT, SCALE, FloorsBelow, Project, Source, classify_models, facing_degrees, floor_below

COMPILER = ROOT / "build/tools/mm9_compile_indoor_source"
# The desktop renderer draws each translucent face as a render batch of its own, with its own GPU buffers, and bgfx
# has 4 096 of each for the whole map: 9 828 translucent faces (Thousand Terrors' candle orbs) made it refuse the
# map, 647 (Training Hall) draw fine. Headless runs do not show it. Small translucent objects go in as decorations.
TRANSLUCENT_FACE_WARNING = 1500
FLOOR_SPLIT_MIN_LT2 = 8000         # LT²: a floor is cut when two rooms with no portal between them hold this much of it
PORTAL_NEAR_REACH = 96             # native units: the scene's portal_visibility near_reach (scene_file)
SCENE_TEMPLATE = ROOT / "level_generation/projects/brackenford_greywatch/calibration/calibration.scene.yml"


class Hooks:
    """What a map project adds to the shared conversion. Override what the map needs."""
    generator = "mm9r_dungeon"
    mover_events: dict = {}             # mover group -> (event id, "click" | "pressure_plate")
    # MM9's touch Triggers switching AmbientSounds get the shared poll (objects.ambient_triggers); the cities' and
    # regions' own scripts handle theirs (CityHooks)
    shared_ambient_triggers: bool = True
    # Lua tables of the map script that list placed actors by DAT name for its messages, not as scripted behaviour of
    # each: pack growth's Lua scan does not follow them and adds the copies to them (density.py)
    density_lua_directories: tuple = ()
    # Lua tables that name every placed actor by DAT name (with its kind, say) but take no copies: pack growth's Lua
    # scan does not read them as scripting either (1000 Terrors' KIND; density.lua_name_tables)
    density_lua_name_tables: tuple = ()

    def extra_seeds(self, build) -> list:
        """Extra air seed points (LithTech) beyond starts, lights, chests, triggers and monsters."""
        return [s for s in (build.project.overrides.get("seeds") or [])]

    def edit_polygons(self, build, polygons: list) -> list:
        """The map's own changes to the merged polygons, before voxels and rooms (Beethoven: water surfaces)."""
        return polygons

    def extra_portals(self, build) -> list:
        """More portals after the doorways, archway cuts and rect portals, before the rooms are labelled (a city's
        street cuts and roof-line portals, ../city/structure.py). A portal may carry `cells`, its barrier voxels."""
        return []

    def populate(self, build) -> None:
        """Decorations, pads and other entities, after movers and lights (build.content is a content.Content)."""

    def actors(self, build, sector_of_room: dict) -> list[dict]:
        return []

    def map_script(self, build) -> str:
        return "-- no map events\n"

    def scene(self, build, scene: dict) -> None:
        """Last changes to the scene (runtime restrictions, environment)."""

    def report(self, build) -> dict:
        return {}

    def grown(self, build, scene: dict, script: str, copies: list) -> str:
        """The map Lua after pack growth appended `copies` to the scene's actors (density.py): a script that counts
        the placed actors updates itself here."""
        return script


class Build:
    """The state of one conversion run (the hooks read and extend it)."""
    def __init__(self, project: Project, hooks: Hooks):
        self.project, self.hooks = project, hooks
        self.source = Source(project)
        self.plan = classify_models(self.source)
        self.stats = Counter()
        self.log = {"dropped": [], "mixed": [], "restored": [], "welded": [], "cracks_left": []}
        self.dropped_polygons = []
        self.polygons = []
        self.portals = []
        self.package = None
        self.rooms = None
        self.movers, self.lights, self.starts = [], [], []
        self.content = None
        self.runtime = project.work / "runtime"
        # what the shared MM9 object rules add (objects.py, perception.py): bone piles, broken urns and explosions,
        # hints, ambient triggers; lua.Script.finish writes their Lua
        self.shared = {}
        self.grow_packs = True              # pack growth (density.py); main's --no-density turns it off
        self.density = {}
        self.treasure = {}                  # treasure.py's summary

    # --- Geometry, rooms, faces ----------------------------------------------------------------------------------
    def geometry(self) -> None:
        polygons = []
        for name in self.plan["static"]:
            polygons += self.source.polygons(name)
        self.stats["source_polygons"] = len(polygons)
        polygons = merge_coplanar(polygons)
        self.stats["merged_polygons"] = len(polygons)
        self.stats["collinear_vertices_removed"] = drop_unshared_collinear(polygons)
        self.stats["sky_flagged_retextured"] = self.source.sky_flagged_as_sky(polygons)
        self.stats["untextured_volume_faces_retextured"] = water.untextured_volume_faces(self.source, polygons)
        polygons = self.hooks.edit_polygons(self, polygons)
        destructibles.tag_brushes(self, polygons)
        if water.swimming(self.project):
            polygons = self.swim_surfaces(polygons)
        self.glass = Glass(self.project.overrides, self.source)
        self.portals = door_portals(self.source, self.plan)
        self.grid, self.solid, self.air, air_stats = build_voxels(polygons, self.source, self.hooks.extra_seeds(self))
        self.stats.update(air_stats)
        for extra in self.project.overrides.get("portals") or []:
            self.portals.extend(archway_portals(self.grid, self.air, extra))
        self.portals.extend(rectangle_portals(self.project.overrides.get("rect_portals")))
        self.portals.extend(self.hooks.extra_portals(self))
        barrier_portals = list(self.portals)
        self.labels, room_count = label_rooms(self.grid, self.air, self.portals)
        self.stats["rooms"] = room_count
        for portal in self.portals:
            if "ring" not in portal and portal.get("kind") not in ("street_cut", "roof_line"):
                portal["face_grow"] = self.grid.size          # out to the jambs (rooms.face_halves)
        for portal in self.portals:
            portal["rooms"] = portal_sides(self.grid, self.labels, portal)
        leaky = [p["name"] for p in self.portals if len(set(p["rooms"])) < 2 or 0 in p["rooms"]]
        self.stats["portals_without_two_rooms"] = len(leaky)
        if leaky:
            print("portals without two rooms:", leaky, [p["rooms"] for p in self.portals if p["name"] in leaky])
        self.rooms = NearestRoom(self.grid, self.labels)
        self.portals += glass_portals(self.rooms, polygons, self.glass, self.stats)
        self.portals = split_straddling_portals(self.grid, self.labels, self.portals, self.stats)
        # Holes in the portal graph: barrier voxels between two rooms with no portal face over them (rooms.py)
        # The reachable air (flooded from the map's seeds) for checks after the build: the portal sweep's tables
        # (output/portal_sweep*/final_table.py) keep only poses whose eye is in it
        np.savez_compressed(self.project.work / "air_voxels.npz", air=np.packbits(self.air), shape=self.grid.shape,
                            origin=self.grid.origin, size=self.grid.size, offset=self.project.offset, scale=SCALE)
        holes = uncovered_barriers(self.grid, self.air, self.labels, barrier_portals, self.portals)
        self.stats["uncovered_barrier_voxels"] = sum(h["voxels"] for h in holes)
        self.stats["uncovered_barrier_clusters"] = len(holes)
        for hole in holes:
            hole["centre_native"] = self.project.native(np.array(hole["centre_lt"])).round().astype(int).tolist()
        (self.project.work / "uncovered_barriers.json").write_text(json.dumps(holes, indent=1) + "\n")
        print(f"uncovered barriers: {self.stats['uncovered_barrier_voxels']} voxels in {len(holes)} clusters"
              + (f", largest {holes[0]['voxels']} at native {holes[0]['centre_native']}" if holes else ""), flush=True)
        settings = self.project.overrides["map"]
        polygons = self.split_floors_between_rooms(polygons)
        self.polygons = assign_faces(self.rooms, polygons, self.portals, self.stats, self.log,
                                     minor_split=bool(settings.get("split_minor_rooms", True)),
                                     split_retry=bool(settings.get("split_retry")),
                                     thin_walls=bool(settings.get("thin_walls")),
                                     corner_samples=bool(settings.get("corner_samples")),
                                     restore_holes=bool(settings.get("restore_floor_holes", True)),
                                     dropped=self.dropped_polygons)
        portal_side_faces(self.polygons, self.portals, self.grid.size, self.stats)
        self.polygons = doorway_floors(self.polygons, self.portals, self.rooms, self.stats)
        self.polygons = cut_floors_under_ramps(self.polygons, self.stats, self.log)
        self.polygons = cut_floors_under_overlays(self.polygons, self.stats, self.log)
        if settings.get("weld_floor_cracks", True):
            self.polygons += weld_floor_cracks(self.rooms, self.polygons, self.stats, self.log)
        self.floor_hole_check()
        glass_backed(self.polygons, self.stats)
        if settings.get("drop_invisible_bottoms", True):
            # map: {drop_invisible_bottoms: false} keeps them (floors.invisible_bottoms, 2026-10-31)
            self.polygons = invisible_bottoms(self.polygons, self.stats, self.log)
            (self.project.work / "invisible_bottoms.json").write_text(
                json.dumps(self.log.get("invisible_bottoms", []), indent=0) + "\n")
        if settings.get("shared_rooms", True):
            # faces in a wall's thickness that two rooms see draw in both (rooms.shared_rooms, 2026-11-07); map:
            # {shared_rooms: false} turns it off; dropped walls going on in a kept wall's plane come back first
            self.polygons += restore_continuations(self.polygons, self.dropped_polygons, self.stats, self.log)
            shared_rooms(self.polygons, self.stats, self.log)
        self.polygons += self.actor_barriers()
        self.stats["faces"] = len(self.polygons)
        self.floor_check = floor_mismatches(self.rooms, self.polygons)
        self.stats["floor_area_under_other_rooms_lt2"] = sum(self.floor_check.values())
        work = self.project.work
        title = f"{room_count} rooms, {len(self.portals)} portals"
        draw_plan(work / "rooms.png", self.polygons, self.portals, title)
        draw_plan(work / "rooms_large.png", self.polygons, self.portals, "rooms", scale=0.4)
        for name, level in (self.project.overrides.get("plan_levels") or {}).items():
            draw_plan(work / f"rooms_{name}.png", self.polygons, self.portals, f"rooms, {name}", scale=0.4,
                      level=tuple(level))

    def split_floors_between_rooms(self, polygons: list) -> list:
        """Floors under the air of two rooms, cut at the walls standing on them (wall_splits.split_at_walls). The face
        assignment splits a face only at portal planes or where a second room holds 15 % of its samples, so a floor
        running on under a room's walls into another room stays whole in the first, and the engine, finding a party's
        sector by the floor under it, puts a party standing in the second room in the first: its view black or the
        second room missing (Verhoffin Ruins' water-trap room, by hand 2026-11-07; found by the portal sweep's follow-up
        2026-11-08 in Boot Camp, Thjorgard and Dark Passageway). A portal between the two rooms does not help: from the
        first room it can be behind the party or out of view (Drangheim City's tower passage, whose floor was the inner
        room's, behind its doorway; a player's report, 2026-11-08). So a floor is cut when the air a voxel and a half
        over its samples holds, besides the room with the most of it, FLOOR_SPLIT_MIN_LT2 of another room, joined to it
        by a portal or not (until 2026-11-08 only rooms with no portal; cutting every big floor added 14-25 % faces).
        map: {split_floors_between_rooms: false} turns it off; `without_portal` keeps the narrower rule (a map at the
        7 000-outline limit: each cut splits the wall-to-floor edges along it, Chasm of the Dead +231)."""
        mode = self.project.overrides["map"].get("split_floors_between_rooms", True)
        if not mode:
            return polygons
        joined = set()
        if mode == "without_portal":
            joined = {frozenset(int(r) for r in p["rooms"]) for p in self.portals if len(set(p.get("rooms", ()))) == 2}
        grid, labels = self.grid, self.labels
        lift = np.array([0.0, 1.5 * grid.size, 0.0])

        def between_rooms(polygon) -> bool:
            if polygon.role != "static" or polygon.normal[1] < 0.99 or polygon.area < wall_splits.FLOOR_SPLIT_AREA:
                return False
            samples = sample_polygon(polygon.points, 16.0)
            cells = grid.index(samples + lift)
            above = labels[cells[:, 0], cells[:, 1], cells[:, 2]]
            weight = polygon.area / max(len(samples), 1)
            values, counts = np.unique(above[above > 0], return_counts=True)
            if len(values) < 2:
                return False
            own = int(values[np.argmax(counts)])            # the room the floor will go to (the most of its air)
            return any(int(room) != own and count * weight >= FLOOR_SPLIT_MIN_LT2
                       and frozenset((own, int(room))) not in joined for room, count in zip(values, counts))

        polygons, splits = wall_splits.split_at_walls(polygons, kinds=("floor",), select=between_rooms)
        self.stats["floors_split_between_rooms"] = splits
        return polygons

    def swim_surfaces(self, polygons: list) -> list:
        """The shared water rule (dungeon/water.py `swimming`): a liquid volume's own polygons that a map keeps as
        static geometry stop being a floor or a wall: its tops become non-solid surfaces, its invisible sides go; and
        every other up-facing polygon with a liquid texture at a volume's top inside its footprint (MM9's water brush
        faces, the wading floors the maps' hooks built there) becomes non-solid too. The voxel pass then sees the air
        under the surface as the air over it (one room; the engine crosses rooms only at portals); `water_checks`
        reports the pieces where it is not, or where no bed is under the water."""
        liquid = {o["name"] for o in water.liquid_objects(self.source)}
        pieces = water.surface_pieces(self.source)
        beds = water.Beds(polygons)
        out = []
        for polygon in polygons:
            if polygon.model in liquid and polygon.role == "invisible":
                self.stats["swim_volume_sides_dropped"] += 1
                continue
            if polygon.model in liquid and polygon.role == "static":
                polygon.role = "nonsolid"
                self.stats["swim_surfaces_nonsolid"] += 1
            elif polygon.role == "static" and (piece := water.surface_polygon(pieces, polygon)) is not None:
                # over an unbuilt bed (no floor under it in the volume: a far sea past a map's near box) it stays a solid
                # wading floor, as before the shared rule
                if beds.has_bed(polygon, piece):
                    polygon.role = "nonsolid"
                    self.stats["swim_wading_surfaces_nonsolid"] += 1
                else:
                    self.stats["swim_surfaces_kept_no_bed"] += 1
            out.append(polygon)
        # a hook that builds a volume's surface itself later (Bathhouse's FloodWater mover faces over BlueWater2) names it
        # in `own_water_surfaces`; DrainWater.scr volumes are drawn by their movers
        own = set(getattr(self.hooks, "own_water_surfaces", ()))
        drawn = water.drawn_surfaces(self.source, out, set(self.plan["skipped"]) - own)
        self.stats["swim_drawn_surfaces"] = len(drawn)
        return out + drawn

    def actor_barriers(self) -> list:
        """MM9's AIBarrier brushes (invisible volumes along ledges, bridges and pits that block only its AI) as faces
        of the room nearest each: invisible and untouchable, listed in the scene's `actor_barriers`, where only the
        monsters' movement treats them as walls (devdocs/INDOOR_OPEN_SKY.md "Monster barriers"). They stay out of the
        air, room and floor passes."""
        barriers = []
        if not self.plan["barriers"]:
            return barriers
        # Never drawn: every face takes MM9's invisible helper texture (a barrier's own, often "Default", may have no
        # alias), and every polygon is kept whatever its surface flags. A map whose own faces never use the helper has
        # no alias for it in its table: the one the other MM9 maps' tables give it (worlds/mm9/textures/INVIZVJN7N).
        texture = next((name for name in self.source.aliases if name.endswith("misc\\invisible.dtx")), None)
        if texture is None:
            texture = "textures\\leveltextures\\misc\\invisible.dtx"
            self.source.aliases[texture] = {"source_texture": texture, "alias": "INVIZVJN7N", "width": 64, "height": 64}
        alias = self.source.aliases[texture]
        for name in self.plan["barriers"]:
            model = self.source.models[name]
            for poly in model.polies:
                ring = poly_ring(poly)
                if len(ring) < 3:
                    continue
                surface = model.surfaces[poly.surface_index]
                points = np.array([model.points[i] for i in ring], float)
                polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], alias["source_texture"],
                                  (np.array(surface.uv_origin), np.array(surface.uv_u), np.array(surface.uv_v)),
                                  surface.flags, name, "barrier")
                polygon.notes.update(width=alias["width"], height=alias["height"])
                if polygon.area <= 0.5:
                    continue
                polygon.label = self.rooms.owner(points.mean(axis=0))
                if polygon.label > 0:
                    barriers.append(polygon)
        self.stats["actor_barrier_models"] = len(self.plan["barriers"])
        self.stats["actor_barrier_polygons"] = len(barriers)
        return barriers

    def floor_hole_check(self) -> None:
        """The floor-hole check (floors.floor_holes): dropped floor faces with air above beside a kept floor of their
        height, and same-height cracks wider than the weld. A WARNING line for each kind; work/floor_holes.json."""
        found = floor_holes(self.rooms, self.polygons, self.dropped_polygons)
        def native(points) -> list:
            return self.project.native(np.array(points)).round().astype(int).tolist()

        for kind in ("holes", "cracks"):
            for record in found[kind]:
                record["centre_native"] = native(record["centre_lt"])
                record["ring_native"] = native(record.pop("ring_lt"))
        self.floor_holes = dict(found, restored=self.log["restored"], welded=self.log["welded"],
                                cracks_left=self.log["cracks_left"])
        self.stats["floor_holes_left"] = len(found["holes"])
        self.stats["floor_cracks_left"] = len(found["cracks"])
        (self.project.work / "floor_holes.json").write_text(json.dumps(self.floor_holes, indent=1) + "\n")
        if found["holes"]:
            print(f"WARNING: {len(found['holes'])} floor holes (dropped up-facing faces with air above beside a floor "
                  "of their height; work/floor_holes.json): restore them (a map hook) or explain them")
        if found["cracks"]:
            print(f"WARNING: {len(found['cracks'])} floor cracks wider than the weld (work/floor_holes.json): a path "
                  "planner falls through any crack over 2 units")

    def faces(self) -> None:
        """Rooms with their static, glass, invisible and non-solid faces, and the portal faces. Glass faces go to
        STATIC_glass<k>_<room> nodes (k: the glass kind, rooms.Glass), ordinary solid faces of the
        room whose ids the compiler reports (faces.yml), so the scene can make them translucent."""
        package = self.package
        by_room = defaultdict(list)
        for polygon in self.polygons:
            by_room[polygon.label].append(polygon)
        # a second room (rooms.shared_rooms) only for faces whose rooms both keep plain faces (ROOM_ nodes)
        plain = {label for label, polygons in by_room.items()
                 if any(p.role == "static" and not p.notes.get("cog") and "back_label" not in p.notes
                        and not self.glass.opaque(p) for p in polygons)}
        for label in sorted(by_room):
            rid = room_id(label)
            for polygon in by_room[label]:
                if polygon.role == "glass" and polygon.notes.get("cog"):
                    # A breakable pane (destructibles.py: a DestructableBrush window): glass faces of its own, whose
                    # cog the scene's face overrides set
                    node = f"STATIC_glass{self.glass.kind(polygon)}_c{polygon.notes['cog']}_{rid[5:]}"
                elif polygon.role == "glass":
                    node = f"STATIC_glass{self.glass.kind(polygon)}_{rid[5:]}"
                elif polygon.role == "static" and polygon.notes.get("cog"):
                    # A structure a script removes (evt.SetFacetBit by cog: the Isle of Ashes' fort walls): solid
                    # faces of their own carrying the cog number
                    node = f"TRIGGER_cog{polygon.notes['cog']}_{rid[5:]}"
                elif polygon.role == "invisible" and polygon.notes.get("cog"):
                    # A destructible's invisible hit box (MM9 RayHit: Sturmford's drawbridge chains): invisible faces
                    # carrying its cog (destructibles.py)
                    node = f"TRIGGER_cog{polygon.notes['cog']}i_{rid[5:]}"
                elif polygon.role == "static" and (self.glass.opaque(polygon)
                                                   or (polygon.notes.get("back_label") in plain and label in plain)):
                    # a face two rooms see (rooms.shared_rooms): its surface names the other as its back room, and the
                    # engine draws it when either is visible; a face MM9 draws opaque whose texture has alpha
                    # (rooms.Glass.opaque): the scene's `opaque_faces`
                    shared = polygon.notes.get("back_label") in plain and label in plain
                    back = room_id(polygon.notes["back_label"]) if shared else None
                    kind = "opaque" if self.glass.opaque(polygon) else "shared"
                    if kind == "opaque":
                        self.opaque_variant(polygon)
                    node = f"TRIGGER_{kind}_{back[5:]}_{rid[5:]}" if back else f"TRIGGER_{kind}_{rid[5:]}"
                    if node not in package.room_nodes[rid]:
                        package.room_nodes[rid].append(node)
                        package.metadata["surfaces"].append(dict({"id": node[8:], "source_node": node, "flags": []},
                                                                 **({"back_room": back} if back else {})))
                else:
                    node = {"static": "ROOM_", "invisible": "TRIGGER_invisible_", "nonsolid": "TRIGGER_nonsolid_",
                            "barrier": "TRIGGER_barrier_"}[polygon.role] + rid[5:]
                package.add_polygon(node, polygon, self.stats)
                if node.startswith("STATIC_") and node not in package.room_nodes[rid]:
                    package.room_nodes[rid].append(node)
                if node.startswith("TRIGGER_cog") and node not in package.room_nodes[rid]:
                    package.room_nodes[rid].append(node)
                    package.metadata["surfaces"].append({"id": node[8:], "source_node": node,
                                                         "flags": ["invisible"] if polygon.role == "invisible" else [],
                                                         "cog_number": int(polygon.notes["cog"])})
                elif node.startswith("TRIGGER_") and node not in package.room_nodes[rid]:
                    package.room_nodes[rid].append(node)
                    # a barrier (outdoor_blv.py: MM9's AIBarrier) is invisible and untouchable: only the scene's
                    # `actor_barriers` list makes it a wall, for monsters
                    package.metadata["surfaces"].append({"id": node[8:], "source_node": node, "flags": {
                        "invisible": ["invisible"], "barrier": ["invisible", "untouchable"]}.get(
                        polygon.role, ["untouchable"])})
        self.present = {room_id(label) for label in by_room if package.nodes.get(f"ROOM_{room_id(label)[5:]}")}
        self.portal_report = []
        node_names = Counter()
        for portal in self.portals:
            front, back = (room_id(v) for v in portal["rooms"])
            if front == back or front not in self.present or back not in self.present:
                self.portal_report.append({"name": portal["name"], "kind": portal["kind"], "skipped": True,
                                           "rooms": [front, back]})
                continue
            corners = portal["ring"] if "ring" in portal else portal_corners(portal)
            # one node per portal: MM9 names two of Thronheim City's user portals WallPortal_2, and the second's rooms
            # were written for both faces (a doorway joined two sectors 5 000 units away; portal sweep 2026-11-08)
            name = portal["name"]
            node_names[name] += 1
            if node_names[name] > 1:
                name = f"{name}_{node_names[name]}"
            node = "PORTAL_" + name
            material = package.material(next(iter(self.source.aliases.values()))["source_texture"])[0]
            # a glass portal's ring may have more than four corners
            rings = face_rings(self.project, np.array(corners), portal["normal"], np.zeros((len(corners), 2)),
                               Counter())
            for points, _ in rings:
                package.add_raw(node, points, material)
            package.metadata["portals"].append({"id": name, "source_node": node, "front_room": front,
                                                "back_room": back})
            self.portal_report.append({
                "name": portal["name"], "kind": portal["kind"], "rooms": [front, back],
                "centre_native": self.project.native(portal["centre"]).round().astype(int).tolist(),
                "width": round(2 * portal["half_a"] * SCALE), "height": round(2 * portal["half_b"] * SCALE),
                "faces": len(rings)})

    # --- Compile, starts, scene ----------------------------------------------------------------------------------
    def compile(self) -> list:
        self.runtime.mkdir(parents=True, exist_ok=True)
        stem, source_dir = self.project.stem, self.project.source_dir
        result = subprocess.run([str(COMPILER), str(source_dir / f"{stem}.glb"), str(source_dir / f"{stem}.geometry.yml"),
                                 str(self.runtime / self.project.map), str(self.runtime / f"{stem}.doors.yml"),
                                 str(self.runtime / f"{stem}.faces.yml")], capture_output=True, text=True)
        (self.project.work / "build.log").write_text(result.stdout + result.stderr)
        if result.returncode != 0:
            raise SystemExit("compile failed:\n" + result.stdout[-3000:] + result.stderr[-3000:])
        print(result.stdout.strip().split("\n")[0])
        return yaml.safe_load((self.runtime / f"{stem}.doors.yml").read_text()) or []

    def start_points(self) -> list[dict]:
        starts = []
        for name in self.project.starts:
            p = self.source.properties(name)
            floor = floor_below(self.polygons, p["Pos"])
            if floor is None:
                raise SystemExit(f"start {name}: no floor under it")
            position = self.project.native(p["Pos"]).round().astype(int).tolist()
            position[2] = int(round(floor * SCALE - self.project.offset[2])) + 1
            starts.append({"name": name, "position": position,
                           "direction_degrees": int(round(facing_degrees(p["Rotation"]))) % 360})
        return starts

    def ai_open_doors(self) -> dict:
        """door id -> the door ids a monster opens with it: every mover of a group whose MM9 door is AITriggerable and
        not Locked (the group's click opens them all, as MM9's Use opens a door and its DoubleDoorName)."""
        groups = defaultdict(list)
        for mover in self.movers:
            properties = self.source.by_name[mover["dat_models"][0].lower()]["properties"]
            if float(properties.get("AITriggerable", 0) or 0) and not float(properties.get("Locked", 0) or 0):
                groups[mover["group"]].append(mover["door_id"])
        return {door_id: sorted(ids) for ids in groups.values() for door_id in ids}

    def scene_file(self, doors: list) -> dict:
        scene = json.loads(SCENE_TEMPLATE.read_text())
        scene["source"]["geometry_file"] = self.project.map
        scene["environment"]["ceiling"] = self.project.ceiling
        scene["party_start_points"] = [{"start_index": i, "source_name": "StartPoint0" if i == 0 else s["name"],
                                        "position": s["position"], "direction_degrees": s["direction_degrees"]}
                                       for i, s in enumerate(self.starts)]
        mover_blocks = {mover["door_id"]: mover["mover"] for mover in self.movers if mover.get("mover")}
        # an empty block too: a silent MM9 door (movers.door_sounds)
        sound_blocks = {mover["door_id"]: mover["sounds"] for mover in self.movers if mover.get("sounds") is not None}
        ai_open = self.ai_open_doors()
        for door in doors:
            # MM9's AITriggerable doors: a monster walking into one opens it and the movers of its group
            # (BaseDoor.inc; MM9_MONSTER_AI_PLAN.md phase 4a).
            if door["door_id"] in ai_open:
                door["ai_open"] = ai_open[door["door_id"]]
            if door["door_id"] in mover_blocks:
                door["mover"] = mover_blocks[door["door_id"]]
            # MM9's own door sounds (movers.door_sounds; 2026-11-02, the play-test: not MM6-MM8's)
            if door["door_id"] in sound_blocks:
                door["sounds"] = sound_blocks[door["door_id"]]
        scene["initial_state"]["doors"] = doors
        scene["initial_state"]["actors"] = []
        ladders = ladder_records(self.project.overrides.get("ladders"), self.source.models, self.project.native, SCALE)
        if ladders:
            scene["ladders"] = ladders
        scene["loot_containers"] = []
        # MM9 baked its lights with shadows: a light lights no face it stands behind (a house's lights not its outer
        # walls, where their reach crosses its doorway; devdocs/INDOOR_OPEN_SKY.md "Static lights", 2026-11-04)
        scene["static_lights"] = {"sides": "front"}
        translucent = self.translucent_faces(doors)
        opaque = self.opaque_faces()
        if opaque:
            scene["opaque_faces"] = opaque
        if translucent:
            scene["translucent_faces"] = translucent
        groups = yaml.safe_load((self.runtime / f"{self.project.stem}.faces.yml").read_text()) or []
        barrier_faces = sorted(face for group in groups if group["source_node"].startswith("TRIGGER_barrier_")
                               for face in group["face_ids"])
        if barrier_faces:
            scene["actor_barriers"] = {"faces": barrier_faces}
        # MM9's monsters walk off ledges of any height after their target (devdocs/mm9_rework/MM9_MONSTER_JUMP_RE.md);
        # its AIBarrier brushes, above, are what keeps them off the edges its designers meant
        scene["actor_movement"] = {"drops": "follow"}
        # Rooms are 16 LT (41 unit) voxels: a floor, jamb or wall near a doorway may be the room's across it, and the
        # camera standing on it takes that room. A portal of the camera's room within two voxels and a bit that the
        # view would drop opens the whole view (IndoorPortalVisibility.h nearPortalReach; MM9 portal sweep 2026-11-08)
        scene["portal_visibility"] = {"near_reach": PORTAL_NEAR_REACH}
        if water.swimming(self.project):
            # MM9's liquid volumes, swum in (dungeon/water.py); a volume on a mover follows its door. A map's scene
            # hook may adjust them (Verhoffin Ruins: its trap water's top at the BLV's stored pose).
            liquid = {o["name"] for o in water.liquid_objects(self.source)}
            scene["water_volumes"] = water.water_volumes(self.source, self.project.native,
                                                         movers=water.mover_doors(self, liquid))
        self.stats["actor_barrier_faces"] = len(barrier_faces)
        fog = self.source.fog()
        if fog:
            scene["fog"] = fog
        model_lighting = self.source.model_lighting()
        if model_lighting:
            scene["model_lighting"] = model_lighting
        # MM9's breakable walls and props (dungeon/destructibles.py, devdocs/INDOOR_DESTRUCTIBLES.md)
        breakable = destructibles.scene_entries(self, scene)
        if breakable:
            scene["destructibles"] = breakable
        # MM9's searchable bone and trash piles and the urns' bags (objects.py)
        searchable = objects.searchable_records(self.content)
        if searchable:
            scene["searchable_loot_props"] = searchable
        if self.shared.get("spawned_loot_containers"):
            scene["spawned_loot_containers"] = self.shared["spawned_loot_containers"]
        # MM9's pickable props as world items (pickups.py)
        if self.content.world_items:
            scene["world_items"] = self.content.world_items
            self.stats["world_items"] = len(self.content.world_items)
        perception.scene_faces(self, scene)
        # MM9's GlowingLights (dungeon/lights.py, devdocs/INDOOR_PULSING_LIGHTS.md)
        pulsing = pulsing_lights(self.source, self.project)
        # and its PerceptionLights, switched by the shared Lua (objects.shared_lines)
        pulsing += self.perception_light_entries
        if pulsing:
            scene["pulsing_lights"] = pulsing
        # MM9's AmbientSounds (dungeon/ambient.py, devdocs/AMBIENT_SOUNDS.md)
        sounds = ambient.ambient_sounds(self.source, self.project, self.stats)
        # the fires', torches' and braziers' own sounds (after the map's hooks and objects.place_fires placed them)
        sounds += ambient.fire_sounds(self, self.stats)
        if sounds:
            scene["ambient_sounds"] = sounds
        # touch Triggers that switch them (objects.ambient_triggers); the cities' and regions' own scripts do theirs,
        # unless the map opts in (overrides.yml `map: {ambient_triggers: true}`: no script of its own switches them)
        if getattr(self.hooks, "shared_ambient_triggers", True) or self.project.overrides["map"].get("ambient_triggers"):
            self.shared["ambient_triggers"] = objects.ambient_triggers(self, sounds)
        # touch Triggers that switch a WeatherMan's fog (objects.weather_triggers: Frosgard's pass); no map scripts them
        self.shared["weather_triggers"] = objects.weather_triggers(self)
        return scene

    def opaque_variant(self, polygon) -> None:
        """An opaque face takes its texture's opaque variant (`<first seven>OPQ`, ../opaque_textures.py: alpha 255 in
        every tier, so the x4 and x2 reductions keep the RGB the premultiplied filtering loses at low alpha) when the
        review root has it."""
        alias = self.source.aliases[polygon.texture.lower()]
        name = alias["alias"][:7].upper() + "OPQ"
        if not (review_root.ASSETS / "worlds/mm9/textures" / f"{name}.bmp").exists():
            return
        key = polygon.texture + "#opaque"
        self.source.aliases.setdefault(key.lower(), dict(alias, alias=name, source_texture=key))
        polygon.texture = key

    def merge_face_lists(self, scene: dict) -> None:
        """A map's own `translucent_faces` (its hooks' entries, appended after the shared glass: webs, chains, its
        glass found by texture) win over the shared glass's entries for the same face, and a translucent face is no
        opaque face: the engine refuses a face listed twice."""
        entries = scene.get("translucent_faces") or []
        seen = set()
        for entry in reversed(entries):
            entry["faces"] = [face for face in entry["faces"] if face not in seen]
            seen.update(entry["faces"])
        if entries:
            scene["translucent_faces"] = [entry for entry in entries if entry["faces"]]
        if scene.get("opaque_faces"):
            scene["opaque_faces"] = [face for face in scene["opaque_faces"] if face not in seen]
            self.stats["opaque_faces"] = len(scene["opaque_faces"])

    def opaque_faces(self) -> list[int]:
        """The scene's `opaque_faces` (devdocs/INDOOR_TRANSLUCENT_FACES.md "Opaque faces"): the compiled faces of the
        TRIGGER_opaque_ nodes, MM9 surfaces without the Translucent flag whose texture has a graded alpha (rooms.Glass)."""
        groups = yaml.safe_load((self.runtime / f"{self.project.stem}.faces.yml").read_text()) or []
        faces = sorted(face for group in groups if group["source_node"].startswith("TRIGGER_opaque_")
                       for face in group["face_ids"])
        self.stats["opaque_faces"] = len(faces)
        return faces

    def translucent_faces(self, doors: list) -> list[dict]:
        """The scene's `translucent_faces` (devdocs/INDOOR_TRANSLUCENT_FACES.md): the compiled faces of the static
        glass nodes (faces.yml) and of the movers' glass parts (their doors' faces), one entry per glass kind."""
        faces = defaultdict(list)
        groups = yaml.safe_load((self.runtime / f"{self.project.stem}.faces.yml").read_text()) or []
        for group in groups:
            node = group["source_node"]
            if node.startswith("STATIC_glass"):
                faces[int(node[len("STATIC_glass"):].split("_")[0])] += group["face_ids"]
        door_faces = {door["door_id"]: door["face_ids"] for door in doors}
        for mover in self.movers:
            if mover.get("glass") is not None:
                faces[mover["glass"]] += door_faces[mover["door_id"]]
        entries = [dict(faces=sorted(faces[k]), **self.glass.kinds[k]) for k in sorted(faces)]
        self.stats["translucent_faces"] = sum(len(e["faces"]) for e in entries)
        if self.stats["translucent_faces"] > TRANSLUCENT_FACE_WARNING:
            print(f"WARNING: {self.stats['translucent_faces']} translucent faces (over {TRANSLUCENT_FACE_WARNING}): "
                  "the desktop renderer may refuse the map; make small translucent objects decorations")
        return entries

    # --- Run -----------------------------------------------------------------------------------------------------
    def run(self, plan_only: bool = False) -> int:
        project = self.project
        project.work.mkdir(parents=True, exist_ok=True)
        self.geometry()
        if plan_only:
            (project.work / "dropped_faces.json").write_text(json.dumps(self.log["dropped"], indent=0) + "\n")
            (project.work / "mixed_faces.json").write_text(json.dumps(self.log["mixed"], indent=0) + "\n")
            print(json.dumps(self.stats, indent=1))
            return 0
        if project.install:
            review_root.create(fresh=False)
        self.package = SourcePackage(self.source, self.hooks.generator)
        self.faces()
        self.movers = build_movers(self.source, self.plan, self.package, self.rooms, self.stats,
                                   self.hooks.mover_events, self.glass, self.present,
                                   all_doors_click=getattr(self.hooks, "all_doors_click", False))
        # `motion: break` brushes: static faces and scene destructibles in the movers' place (dungeon/destructibles.py)
        destructibles.build_breakables(self)
        self.lights = build_lights(self.source, self.polygons, self.package, self.rooms,
                                   set(project.overrides.get("skip_lights") or []))
        from .content import Content
        self.content = Content(self)
        self.hooks.populate(self)
        # MM9's objects every map shares, where the map's own hooks left them (objects.py, perception.py)
        self.shared["hints"] = perception.place(self)
        self.perception_light_entries, self.shared["perception_lights"] = perception_lights(self.source, project)
        objects.place_fires(self)
        piles = {r["source_object_index"]: r["source_id"]
                 for r in self.content.item_source_data.get("searchable_loot_props", [])}
        self.shared["bone_piles"] = {index: (piles[index], "Trash Pile" if "trash" in decoration else "Bone Pile",
                                             self.source.objects[index]["name"])
                                     for index, decoration in self.content.searchable.items() if index in piles}
        self.sector_of_room = {rid: index + 1 for index, rid in enumerate(sorted(self.present))}
        for rid in sorted(self.present):
            self.package.metadata["rooms"].append({"id": rid, "source_nodes": [f"ROOM_{rid[5:]}"]
                                                   + self.package.room_nodes[rid],
                                                   "min_ambient_light_level": project.ambient})
        project.source_dir.mkdir(parents=True, exist_ok=True)
        # Cracks at T-junctions (package.repair_t_junctions; 2026-11-01, Thjorgard City's floor lines).
        self.package.repair_t_junctions(self.stats)
        print(f"t-junctions: {self.stats['t_junction_vertices_inserted']} vertices inserted, "
              f"{self.stats['t_junction_faces_split']} faces split into triangles (non-planar)", flush=True)
        self.package.write(project.source_dir / f"{project.stem}.glb", project.source_dir / f"{project.stem}.geometry.yml")
        doors = self.compile()
        self.starts = self.start_points()
        scene = self.scene_file(doors)
        scene["initial_state"]["actors"] = self.hooks.actors(self, self.sector_of_room)
        # MM9's people by the names their dialogues give them, not a DAT object or row name (dungeon/people.py)
        self.content.report["people_named"] = people.name_people(scene["initial_state"]["actors"])
        scene["loot_containers"] = self.content.loot_records
        # The balance session's chest rules (tools/mm9_import_discovery/mm9_chest_balance.py, BALANCE_PLAN.md, user
        # 2026-11-06): black chests a guaranteed artifact or relic, level-0 random chests the map's usual level, the
        # ordinary random chests' items per chest by chapter (`random_records`); edits the records in place
        from mm9_chest_balance import balance_loot_containers
        balance_loot_containers(project.stem, scene["loot_containers"])
        self.hooks.scene(self, scene)
        # MM9's .spr surfaces animated and translucent where the map opts in (overrides.yml `spr_surfaces`), after
        # the map's hooks and their liquids (dungeon/spr_surfaces.py)
        spr_surfaces.apply(self, scene)
        self.merge_face_lists(scene)
        self.water_checks(scene)
        # Pack growth (density.py, BALANCE_PLAN.md 3.6): copies of the packs' own monsters after every placed actor,
        # once the map Lua (whose actor references it reads) is written
        # the placed actors, for the shared Lua's greeting voices (objects.voice_lines)
        self.scene_actors = scene["initial_state"]["actors"]
        script = density.apply(self, scene, self.hooks.map_script(self))
        stem = project.stem
        (self.runtime / f"{stem}.scene.yml").write_text(json.dumps(scene, indent=1) + "\n")
        # Ground treasure (treasure.py, GROUND_TREASURE_PLAN.md): MM6-MM8 treasure markers on the written scene, which
        # the walk graph reads; the scene is written again with its `spawns`
        treasure.apply(self, scene)
        (self.runtime / f"{stem}.scene.yml").write_text(json.dumps(scene, indent=1) + "\n")
        (self.runtime / f"{stem}.lua").write_text(script)
        facings = {s["name"].lower(): s["direction_degrees"] for s in self.starts}
        _, transition_changes = tables.update_tables(project, self.polygons, write=project.install, facings=facings)
        if project.install:
            tables.install_map(project, self.runtime)
            tables.install_original_comparison(project)
        self.gate_cinematics(scene)
        self.reports(doors, transition_changes)
        return 0

    def water_checks(self, scene: dict) -> None:
        """The shared water rule's two gates (DUNGEON_PLAYBOOK.md "Water volumes and swimming") over every volume of the
        scene not on a mover (a map hook that ran them itself, Verhoffin Ruins, keeps its own): `water.room_mismatches`
        (the air under a surface another room than over it) and `water.bed_holes` (open water with no floor in the
        volume); both must be 0. In build_report.json `stats` and `water`."""
        if not scene.get("water_volumes") or "water_room_mismatches" in self.stats:
            return
        names = {v["id"] for v in scene["water_volumes"] if "mover_door_id" not in v}
        objects = [o for o in water.liquid_objects(self.source) if o["name"] in names]
        mismatches = water.room_mismatches(self, objects)
        holes = water.bed_holes(self, objects)
        self.stats["water_volumes"] = len(scene["water_volumes"])
        self.stats["water_room_mismatches"] = len(mismatches)
        self.stats["water_bed_holes"] = len(holes)
        self.log["water"] = {"volumes": [{"id": v["id"], "pieces": len(v["pieces"]),
                                          "top": sorted({p["top"] for p in v["pieces"]}),
                                          "depth": round(max(p["top"] - p["bottom"] for p in v["pieces"]), 1)}
                                         for v in scene["water_volumes"]],
                             "room_mismatches": mismatches, "bed_holes": holes}
        if mismatches:
            print("WARNING: water surfaces between two rooms (the engine crosses rooms only at portals):", mismatches)
        if holes:
            print(f"WARNING: {len(holes)} points of open water without a bed, e.g. {holes[:3]}")

    def gate_cinematics(self, scene: dict) -> None:
        """The camera gate (mm9r_common/camera_gate.py) over the map's installed cinematics against this BLV: cameras in
        walls or the void move minimally (written back), one that cannot is an error unless overrides.yml
        `cinematics_gate` names it ("<id> shot <n>": reason)."""
        import review_root
        import camera_gate
        stem = self.project.stem
        yml = review_root.mirror_path(f"worlds/mm9/maps/{stem}.cinematics.yml")
        if not yml.is_file():
            return
        if not self.project.install:
            # A scratch build installs nothing: it gates a copy in its own runtime folder (it moved the review root's
            # cameras again on every scratch run before 2026-11-08)
            copy = self.runtime / yml.name
            copy.write_text(yml.read_text())
            yml = copy
        scene_path = self.runtime / f"{stem}.scene.yml"
        overrides = self.project.overrides.get("cinematics_gate") or {}
        for line in camera_gate.gate_installed(stem, yml, self.runtime / self.project.map, scene_path, overrides,
                                               strict=True):
            print("camera gate: " + line, flush=True)

    def reports(self, doors: list, transition_changes: list) -> None:
        project, work = self.project, self.project.work
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(self.runtime / project.map)["payload"]
        sector_faces = list(Counter(f["room_number"] for f in blv["faces"] if not f["is_portal"]).values())
        report = {"map": project.map, "stats": dict(self.stats), "native": {
            "faces": len(blv["faces"]), "vertices": len(blv["vertices"]), "sectors": len(blv["sectors"]),
            "portal_faces": sum(1 for f in blv["faces"] if f["is_portal"]), "doors": len(doors),
            "lights": len(blv["lights"]), "faces_per_sector_max": max(sector_faces),
            "faces_per_sector_median": int(np.median(sector_faces))},
            "portals": self.portal_report, "transitions": transition_changes, "starts": self.starts,
            "floor_check": self.floor_check, "density": self.density, "treasure": self.treasure}
        if "water" in self.log:
            report["water"] = self.log["water"]
        report.update(self.hooks.report(self))
        (work / "build_report.json").write_text(json.dumps(report, indent=1) + "\n")
        (work / "doors.json").write_text(json.dumps(self.movers, indent=1) + "\n")
        (work / "dropped_faces.json").write_text(json.dumps(self.log["dropped"], indent=0) + "\n")
        (work / "mixed_faces.json").write_text(json.dumps(self.log["mixed"], indent=0) + "\n")
        (work / "lights.json").write_text(json.dumps(self.lights, indent=1) + "\n")
        content = self.content.report
        content["light_coverage"] = light_coverage(project, self.polygons, self.lights, self.content.decoration_lights)
        if content["decorations"]:
            content["decorations_per_room_max"] = max(Counter(d["room"] for d in content["decorations"]).values())
        (work / "content.json").write_text(json.dumps(content, indent=1) + "\n")
        (work / "population.json").write_text(json.dumps(population(self), indent=1) + "\n")
        (work / "models.json").write_text(json.dumps({"static": self.plan["static"], "skipped": self.plan["skipped"],
                                                      "movers": sorted(self.plan["movers"])}, indent=1) + "\n")
        (work / "transform.json").write_text(json.dumps({
            "scale": SCALE, "offset": list(project.offset), "voxel_lt": project.voxel,
            "note": "native x = LT.x * scale - offset[0], y = LT.z * scale - offset[1], z = LT.y * scale - offset[2]"},
            indent=1) + "\n")
        print(json.dumps(report["native"], indent=1))


def population(build: Build) -> dict:
    """Where MM9 placed its monsters and chests (DAT records; the map's hooks place them)."""
    import struct
    project = build.project
    monsters, chests = [], []
    floors = FloorsBelow(build.polygons)
    for o in build.source.objects:
        p = o["properties"]
        if o["class"] not in project.monster_classes | {"TreasureChest"}:
            continue
        floor = floors(p["Pos"])
        record = {"dat_object_index": o["index"], "name": o["name"], "class": o["class"],
                  "position_lt": [round(v, 1) for v in p["Pos"]],
                  "position": project.native(p["Pos"]).round().astype(int).tolist(),
                  "floor_z": None if floor is None else int(round(floor * SCALE - project.offset[2])),
                  "facing_degrees": round(facing_degrees(p.get("Rotation")), 1)}
        keys = (("Locked", "TreasureLevel", "TrapLevel", "TreasureType0_7", "Gold", "GoldOnly", "Random", "AIDrop",
                 "Item1", "Item2", "Item3", "Item4", "Item5", "TriggerTarget", "Filename", "Scale")
                if o["class"] == "TreasureChest" else
                ("ScriptName", "ScriptParams", "WanderPathName", "Filename", "Scale", "ShouldRepopulate",
                 "GiveTreasure", "SightDistance"))
        for key in keys:
            value = p.get(key)
            if value in ("", None):
                continue
            if isinstance(value, int) and abs(value) > 1_000_000:         # a float stored in an int property
                value = round(struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0], 3)
            record[key] = value
        (chests if o["class"] == "TreasureChest" else monsters).append(record)
    counts = Counter(m["class"] for m in monsters)
    return {"note": "DAT placements in the native frame (work/transform.json); the map's hooks place them "
                    "(work/content.json)", "monster_counts": dict(sorted(counts.items())), "monsters": monsters,
            "chests": chests}


def main(directory: Path, hooks: Hooks, argv=None) -> int:
    parser = argparse.ArgumentParser(description="MM9 dungeon to native BLV (../mm9r_common/DUNGEON_PLAYBOOK.md)")
    parser.add_argument("--plan", action="store_true", help="analysis and plan images only")
    parser.add_argument("--scratch", type=Path, help="build and compile into this directory; install nothing")
    parser.add_argument("--no-density", action="store_true",
                        help="no pack growth (density.py), for comparisons; overrides.yml `map: {density: false}` "
                             "turns it off for good")
    arguments = parser.parse_args(argv)
    project = Project.load(directory, work=arguments.scratch, install=arguments.scratch is None)
    build = Build(project, hooks)
    build.grow_packs = not arguments.no_density
    return build.run(plan_only=arguments.plan)
