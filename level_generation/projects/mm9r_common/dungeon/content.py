"""
The population helpers of the dungeon converter: decoration entities (props.json from the map's props project),
MM9 touch triggers as invisible pressure-plate pads on the floor under them, placed actors from MM9's monster
objects, and the chests' loot records (tools/mm9_import_discovery/mm9_item_sources.py, the same records the old
importer wrote). Every entity, pad and actor keeps its DAT object name as its anchor (work/content.json). The map's
own wiring (which pad runs which event, which actors are hidden or friendly) lives in the map project.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import yaml

import review_root
import stat_barrels

from . import bodies, destructibles, pickups, prop_pose, town_portal, trees, water
from .package import room_id
from .source import ROOT, SCALE, facing_degrees, floor_below, surface_column

CHEST_EVENT = 41                    # chest k (loot container k) opens with event CHEST_EVENT + k
BONUS_CLASSES = ("WellMMIX", "Cauldron", "Cookpot", "Clover")   # MM9's bonus props (objects.py bonus_lines)
PAD_LIFT = 3                        # a trigger pad stands this far over its floor, so it is the floor the party stands on
# A lamp, lantern or brazier without an MM9 Light of its own (props.json `light: null`; Thjorgard, Thronheim and
# Arslegard City's street lamps): MM9 lit it only with the CandleProp's own dynamic light, the soft warm spot around the
# lantern in MM9 (user's screenshot, 2026-11-04). It gets a native light at its flame of WallTorch's default radius
# (200 LT) in a warm lamp colour.
LAMP_LIGHT_RADIUS = 512
LAMP_LIGHT_COLOUR = [255, 230, 160]
INVISIBLE_BIT, AGGRESSOR_BIT = 0x00010000, 0x00080000
# Where a placed actor stands (Content.actor_floor): the first surface under its DAT position, never one under that
# (actor_floor_audit.py, 2026-11-11). A DAT position at most BURIED_REACH under a surface's top is in the ground (four
# Magreebs on Lindisfarne 35 units under the grass, a Drangheim townsman in a terrace); one on a slope steeper than a
# floor moves to the nearest floor round it, at most SLOPE_REACH away (a Guberland Bandit on a 48 degree cliff).
FLOOR_NORMAL_Y = 0.7
BURIED_REACH = 256 / SCALE
SLOPE_REACH = 768 / SCALE
SLOPE_RING = 24 / SCALE
SLOPE_ANGLES = 16


UPRIGHT_LETTER = re.compile(r"^mm9_scroll(_x\d+)?$")


def flat_letter(source, entry: dict, decoration: str) -> str:
    """MM9's BookLetter.scr letters whose third ScriptParams token (bDown) is 1 lie flat (`:Init` LoopAnim Down, the
    scroll-open.ABC `down` pose): an upright `mm9_scroll` (or `_xNNN`) decoration takes `mm9_scrollflat` at the same
    scale. Same origin convention (props/mm9_outdoor_regions_claude/scripts/scrollflat.py), so the props.json position
    holds; rows from props/mm9_outdoor_regions_claude/scripts/converter_rows.py. Other letters and models (Thjorgard
    City's laid-flat scrollp90) stay."""
    match = UPRIGHT_LETTER.match(decoration.lower())
    index = entry.get("source_object")
    if match is None or not isinstance(index, int) or not 0 <= index < len(source.objects):
        return decoration
    properties = source.objects[index]["properties"]
    tokens = str(properties.get("ScriptParams") or "").split()
    if "bookletter" not in str(properties.get("ScriptName") or "").lower() or len(tokens) < 3 or tokens[2] != "1":
        return decoration
    return "mm9_scrollflat" + (match.group(1) or "")


def model_document(model: str) -> dict:
    """A decoration model's glTF JSON (assets_source/<model>), read once."""
    cache = model_document.__dict__.setdefault("cache", {})
    if model not in cache:
        data = (ROOT / "assets_source" / model).read_bytes()
        cache[model] = json.loads(data[20:20 + int.from_bytes(data[12:16], "little")])
    return cache[model]


def decoration_ids() -> dict:
    """Decoration list ids by name from the review root's tables as the engine merges them (engine rows, then the MM9
    world's contribution, game/content/WorldDecorations.cpp)."""
    world = yaml.safe_load(review_root.mirror_path("worlds/mm9/world.yml").read_text())
    tables = ["engine/data_tables/decoration_data.txt"] + [
        "worlds/mm9/" + c["path"] for c in world.get("tableContributions", []) if c.get("table") == "decorations"]
    ids = {}
    for table in tables:
        for cells in (line.split("\t") for line in review_root.mirror_path(table).read_text(encoding="latin-1")
                      .splitlines()):
            if len(cells) > 1 and cells[0].strip().isdigit():
                ids[cells[1].strip().lower()] = int(cells[0]) - 1
    return ids


def item_sources(project, objects) -> dict:
    """The MM9 item source manifest of the map (chests, world items) as scene data."""
    from mm9_item_sources import Mm9ItemIdMap, build_mm9_item_source_manifest
    manifest = build_mm9_item_source_manifest(project.stem, objects,
                                              Mm9ItemIdMap.load(ROOT / "assets_dev/worlds/mm9/state/item_ids.yml"),
                                              SCALE)
    manifest.require_resolved_item_references()
    return manifest.scene_data()


def monster_replacements():
    """MM9 monster object classes -> runtime monster rows (the old importer's table: monster rows 9xxx whose pictures
    are the `MM9 <Family> A|B|C` families)."""
    from transcode_mm9_dat_to_odm import read_mm9_monster_replacements
    return read_mm9_monster_replacements(
        ROOT / "mm9/extracted/DATA/DATA/MONSTERS.txt", ROOT / "mm9/extracted/DATA/DATA/ACTOR.txt",
        ROOT / "tools/mm9_import_discovery/mm9_monster_legacy_replacements.tsv",
        ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt",
        ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt")


def mm9_npc_actor_rows() -> set:
    """MM9 rows of the townsfolk, uniques and town animals that have their own engine row and 3D model
    (tools/mm9_import_discovery/mm9_npc_actor_rows.tsv, first column)."""
    if not hasattr(mm9_npc_actor_rows, "rows"):
        lines = (ROOT / "tools/mm9_import_discovery/mm9_npc_actor_rows.tsv").read_text().splitlines()[1:]
        mm9_npc_actor_rows.rows = {int(line.split("\t")[0]) for line in lines if line.strip()}
    return mm9_npc_actor_rows.rows


def mm9_monster_rows() -> set:
    """MM9 rows that already have their own engine monster row (9000 + row) and 3D model through the monster
    replacement table: an NPC class resolving to one of them (Thronheim's ElderHonkFemale, Yoltzin Tor, on row 217)
    takes that row too. mm9_npc_actor_rows.tsv cannot list them (the table generator rejects the overlap)."""
    if not hasattr(mm9_monster_rows, "rows"):
        mm9_monster_rows.rows = {replacement.source_number for replacements in monster_replacements().values()
                                 for replacement in replacements}
    return mm9_monster_rows.rows


class Content:
    def __init__(self, build):
        self.build = build
        self.project, self.source, self.package, self.rooms = build.project, build.source, build.package, build.rooms
        self.destructible_props = {}     # DAT object index -> (SetSprite key, native position): destructibles.py
        self.searchable = {}             # DAT object index of a placed BonePile -> its decoration (objects.py)
        self.bonus_props = {}            # DAT object index of a placed well, cauldron, cook pot or clover -> its name
        self.world_items = []            # the scene's world items: MM9's pickable props (pickups.py)
        self.polygons = build.polygons
        self.ids = decoration_ids()
        self.report = {"decorations": [], "pads": [], "actors": [], "chests": [], "omitted": []}
        self.floors = [p for p in self.polygons if p.normal[1] >= 0.7 and p.role == "static"]
        self.floor_low = np.array([p.points.min(0)[[0, 2]] for p in self.floors])
        self.floor_high = np.array([p.points.max(0)[[0, 2]] for p in self.floors])
        self._surfaces = None              # every solid surface, the movers' too (actor_floor)
        self.decoration_lights = []        # (native position, radius) of decorations that carry a light
        self._water_pieces = None          # the volumes' pieces, for swimmers (water.surface_pieces)

    def owner(self, point_lt) -> str:
        return room_id(self.rooms.owner(point_lt))

    # --- Decorations -----------------------------------------------------------------------------------------------
    def entity(self, anchor: str, decoration: str, position, facing: float, primary: int = 0, secondary: int = 0,
               light_radius: int = 0) -> dict:
        name = decoration.lower()
        if name not in self.ids:
            raise SystemExit(f"decoration {name} has no row in the review root's tables (run the props tables.py)")
        if anchor.lower() in self.ids:
            raise SystemExit(f"entity {anchor} would resolve as the decoration of that name")
        node = f"DECOR_{anchor}"
        position = np.asarray(position, float).copy()
        # Whole units up, not to the nearest: the engine puts a decoration in the sector of the floor under its
        # position, and a base rounded under its floor (Thjorgard's Cabinet3: 449.9 -> 450 under an upper floor at 451)
        # put it in the room below, hidden whenever that room was not drawn (2026-11-01).
        position[2] = np.ceil(position[2] - 0.05)
        self.package.marker(node, position, self.package.marker_material())
        owner = self.owner(self.project.lt_from_native(position + [0, 0, 24]))
        self.package.room_nodes[owner].append(node)
        record = {"id": anchor, "kind": "decoration", "source_node": node, "decoration_list_id": self.ids[name],
                  "event_id_primary": primary, "event_id_secondary": secondary}
        if int(round(facing)) % 360:
            record["facing"] = int(round(facing)) % 360
        self.package.metadata["entities"].append(record)
        entry = {"anchor": anchor, "decoration": name, "room": owner, "position": [int(round(v)) for v in position],
                 "event": secondary, "cog": primary}
        self.report["decorations"].append(entry)
        if light_radius:
            self.decoration_lights.append((position, light_radius))
        return entry

    def flame_offset(self, decoration: str) -> np.ndarray:
        """The centre of a decoration model's flame cards (its `Fire` material; a claw lamp's `_orb` without them) in
        OpenYAMM units from the entity position at facing 0, placed as the engine places it: glTF (x, y, z) ->
        (-x, z, y), scaled by the binding height over the model's height."""
        return self._flame_offset(decoration)

    def binding(self, decoration: str) -> dict | None:
        """A decoration's indoor binding (model, height), from the review root's manifest and assets_dev's."""
        if not hasattr(self, "_bindings"):
            # assets_dev's manifest too: a root that owns its copy (the outdoor BLVs') rebuilds it only after the
            # props are placed (outdoor_blv.bind_indoor_decorations), so rows added for them are not in it yet
            self._bindings = {}
            for path in (review_root.SOURCE / "worlds/mm9/models/indoor_decorations.yml",
                         review_root.mirror_path("worlds/mm9/models/indoor_decorations.yml")):
                for b in yaml.safe_load(path.read_text())["decorations"]:
                    self._bindings.setdefault(b["name"].lower(), b)
        return self._bindings.get(decoration.lower())

    def burning(self, decoration: str) -> bool:
        """Whether a decoration's model has flame cards (a `Fire` material: the burning log piles, braziers, torches)."""
        binding = self.binding(decoration)
        if binding is None:
            return False
        return any(m.get("name") == "Fire" for m in model_document(binding["model"]).get("materials", []))

    def burning_decoration_near(self, native, reach: float) -> str | None:
        """The anchor of a placed burning decoration within reach (native units) of a point, horizontally, whose base
        is at most 2 reach under it or reach over it."""
        for entry in self.report["decorations"]:
            delta = np.asarray(entry["position"], float) - native
            if np.hypot(delta[0], delta[1]) <= reach and -2 * reach <= delta[2] <= reach and \
                    self.burning(entry["decoration"]):
                return entry["anchor"]
        return None

    def point_light(self, node: str, position, radius: float, colour) -> None:
        """A native point light (a lamp's or a fire's own light), in the room of its position."""
        position = np.asarray(position, float)
        room = self.owner(self.project.lt_from_native(position))
        self.package.marker(node, position, self.package.marker_material())
        self.package.room_nodes[room].append(node)
        self.package.metadata["lights"].append({"id": node, "source_node": node, "color": list(colour),
                                                "radius": int(round(radius)), "brightness": 31, "type": "point"})

    def _flame_offset(self, decoration: str) -> np.ndarray:
        binding = self.binding(decoration)
        if binding is None:
            raise SystemExit(f"lamp {decoration}: no indoor binding for its flame")
        gltf = model_document(binding["model"])
        low, high, fire, orb = np.full(3, np.inf), np.full(3, -np.inf), [], []
        for mesh in gltf["meshes"]:
            for primitive in mesh["primitives"]:
                accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
                low, high = np.minimum(low, accessor["min"]), np.maximum(high, accessor["max"])
                name = gltf["materials"][primitive["material"]].get("name", "")
                centre = (np.array(accessor["min"]) + np.array(accessor["max"])) / 2
                if name == "Fire":
                    fire.append(centre)
                elif name.endswith("_orb"):     # a claw lamp's glowing orb (no flame: the Blue 1 claw lamps)
                    orb.append(centre)
        fire = fire or orb
        if not fire:
            raise SystemExit(f"lamp {decoration}: its model has no Fire cards or glowing orb")
        centre = np.mean(fire, axis=0) * float(binding["height"]) / (high[1] - low[1])
        return np.array([-centre[0], centre[2], centre[1]])

    def lamp_light(self, entry: dict) -> None:
        """A native light at the flame of a lamp without an MM9 Light of its own (LAMP_LIGHT_RADIUS)."""
        yaw = np.radians(entry["yaw_degrees"])
        c, s = np.cos(yaw), np.sin(yaw)
        offset = self.flame_offset(entry["decoration"])
        position = np.array([entry["x"], entry["y"], entry["z"]], float) + np.array(
            [c * offset[0] - s * offset[1], s * offset[0] + c * offset[1], offset[2]])
        node = f"LIGHT_lamp_{entry['source_name']}"
        room = self.owner(self.project.lt_from_native(position))
        self.package.marker(node, position, self.package.marker_material())
        self.package.room_nodes[room].append(node)
        self.package.metadata["lights"].append({"id": node, "source_node": node, "color": LAMP_LIGHT_COLOUR,
                                                "radius": LAMP_LIGHT_RADIUS, "brightness": 31, "type": "point"})
        self.report.setdefault("lamp_lights", []).append(
            {"lamp": entry["source_name"], "room": room, "position": [int(round(v)) for v in position]})

    def props(self, props_path: Path, events: dict | None = None, cogs: dict | None = None, skip=()):
        """props.json entries (props, torches, chests...) as decorations. events: DAT name -> click event (chests get
        CHEST_EVENT + their container id from the loot records); cogs: DAT name -> SetSprite key. MM9's stat barrels
        (class Barrel) take MM6's drinkable barrel (stat_barrels.py); its flat letters the flat scroll (flat_letter);
        a Town Portal altar (TownPortal.scr) gets its clean twin at its place (town_portal.py)."""
        events, cogs = dict(events or {}), dict(cogs or {})
        chest_index = {record["source_object_index"]: record["container_id"] for record in self.loot_records}
        placed = []
        for entry in json.loads(Path(props_path).read_text()):
            if entry["source_name"] in skip:
                continue
            secondary = events.get(entry["source_name"], 0)
            if entry["kind"] == "chest":
                secondary = CHEST_EVENT + chest_index[entry["source_object"]]
            if entry.get("class") == "BonePile" and not secondary and isinstance(entry.get("source_object"), int):
                # MM9's BonePile (bone or trash pile): a click searches it (objects.py, evt.SearchLootProp)
                from .objects import OBJECT_EVENT_BASE
                secondary = OBJECT_EVENT_BASE + entry["source_object"]
                self.searchable[entry["source_object"]] = entry["decoration"]
            if entry.get("class") in BONUS_CLASSES and not secondary and isinstance(entry.get("source_object"), int):
                # MM9's wells, cauldrons, cook pots and clovers: a click gives their bonus (objects.py bonus_lines)
                from .objects import OBJECT_EVENT_BASE
                secondary = OBJECT_EVENT_BASE + entry["source_object"]
                self.bonus_props[entry["source_object"]] = entry["source_name"]
            # a DestructableProp breaks (destructibles.py): its decoration needs a SetSprite key, the hook's or its own
            primary = cogs.get(entry["source_name"], 0) or destructibles.prop_cog(self.source, entry)
            if town_portal.is_altar(entry):     # the dirty altar's key: the map script swaps it for its clean twin
                primary = primary or town_portal.COG_DIRTY
            decoration = flat_letter(self.source, entry, stat_barrels.stat_decoration(entry))
            position = (entry["x"], entry["y"], entry["z"])
            yaw = entry["yaw_degrees"]
            # MM9 draws the prop in its first animation's pose: the *NS furniture a quarter turn from its bind-mesh GLB
            posed = prop_pose.placement(entry, self.source.objects, self.binding(decoration))
            if posed is not None:
                position, yaw = posed
                self.report.setdefault("pose_turned", []).append(
                    {"anchor": entry["source_name"], "decoration": decoration, "yaw_props_json": entry["yaw_degrees"],
                     "yaw": yaw, "position": [round(v, 1) for v in position]})
            # MM9 lifts a ModelObject by its model's half height at its initial update (prop_pose.lift): chairs and
            # cabinets stored with their Pos on the floor stand on it, things stored on a table top stand on the table
            moved = prop_pose.lifted(entry, self.source.objects, self.binding(decoration), position,
                                     self.project.native)
            if moved is not None:
                if max(abs(a - b) for a, b in zip(moved, position)) > 0.5:
                    self.report.setdefault("lifted", []).append(
                        {"anchor": entry["source_name"], "decoration": decoration,
                         "from": [round(float(v), 1) for v in position], "to": [round(v, 1) for v in moved]})
                position = moved
            # MM9's tree models as the regions' MM6-MM8 trees (trees.py), set into the ground as there
            tree = trees.swap(entry, self.project.stem)
            if tree is not None:
                decoration = tree[0]
                position = (entry["x"], entry["y"], entry["z"] - tree[1]["sink"])
            placed.append({"entry": entry, "decoration": decoration, "position": position, "yaw": yaw,
                           "primary": primary, "secondary": secondary, "tree": tree is not None})
        self.move_to_floor(placed)
        for item in placed:
            entry, position = item["entry"], item["position"]
            # MM9's pickable props are the scene's world items (pickups.py), not decorations
            pickup = self.pickup(entry)
            if pickup is not None:
                dat_name = str(self.source.objects[entry["source_object"]]["properties"].get("Name", ""))
                placement = (self.project.overrides.get("pickups") or {}).get(dat_name)
                self.world_items.append(pickups.scene_entry(self.project.stem, entry["source_object"],
                                                            entry["source_name"], dat_name, position, pickup,
                                                            events.get(entry["source_name"], 0), placement))
                continue
            if destructibles.prop_cog(self.source, entry):
                self.destructible_props[int(entry["source_object"])] = (item["primary"],
                                                                        (entry["x"], entry["y"], entry["z"]))
            self.entity(entry["source_name"], item["decoration"], position,
                        item["yaw"], primary=item["primary"], secondary=item["secondary"],
                        light_radius=entry.get("light_radius", 0))
            if town_portal.is_altar(entry):     # TownPortal.scr's cleansed altar at its place, shown by the script
                self.entity(town_portal.clean_name(entry["source_name"]), town_portal.CLEAN, position,
                            entry["yaw_degrees"], primary=town_portal.COG_CLEAN, secondary=item["secondary"])
            if "light" in entry and entry["light"] is None and entry["kind"] == "torch":
                self.lamp_light(entry)

    def pickup(self, entry: dict):
        """The pickups.py rule of a props.json entry's DAT object, or None."""
        source = entry.get("source_object")
        if entry.get("kind") == "chest" or not isinstance(source, int):
            return None
        return pickups.rule(self.source.objects[source]["properties"], self.project.stem)

    def move_to_floor(self, placed: list[dict]) -> None:
        """MM9's MoveToFloor (the TreasureChest default, most table-top things): LithTech drops such an object at load
        from its DAT position until it rests on the first surface under it, a floor of the map or the top of another
        prop (prop_pose.move_to_floor: the decorations' GLBs as placed, supports first). The old bake dropped them by
        their DAT dims box onto its own supports, which the props projects fit: 147 stood off their tables, shelves
        and floors by 4-150 units (prop_audit.py, 2026-11-07), the Isle of Ashes' chests floated 30-66 units."""
        items = []
        for index, item in enumerate(placed):
            entry, binding = item["entry"], self.binding(item["decoration"])
            source = entry.get("source_object")
            if binding is None or item["tree"] or not isinstance(source, int):
                continue
            properties = self.source.objects[source]["properties"]
            if str(properties.get("Name", "")).lower() != prop_pose.dat_name(entry).lower():
                continue
            points, triangles = prop_pose.decoration_mesh(binding, float(item["yaw"]))
            # the seated townsfolk (a seat z_offset in their binding) sit as the props projects' seats.py placed them:
            # MM9 puts their dims box, which ends at the thighs, on the seat, not their feet
            items.append({"key": index, "points": points, "triangles": triangles, "position": item["position"],
                          "move_to_floor": bool(properties.get("MoveToFloor", 0)) and not binding.get("z_offset"),
                          "dat_z": float(self.project.native(np.asarray(properties["Pos"], float))[2])})

        # the movers' floors where MM9 authored them too (Dark Passageway's ice statues stand on its bridges)
        mover_floors = [p for name in self.build.plan["movers"] for p in self.source.polygons(name)
                        if p.normal[1] >= 0.7 and p.role == "static"]
        # their plan boxes, so each drop tests only the floors whose box holds the point (floor_below's own box test)
        mover_low = np.array([p.points[:, [0, 2]].min(0) for p in mover_floors]).reshape(-1, 2)
        mover_high = np.array([p.points[:, [0, 2]].max(0) for p in mover_floors]).reshape(-1, 2)

        def floor_at(x: float, y: float, z_max: float):
            lx, ly, lz = self.project.lt_from_native((x, y, z_max))
            near = np.flatnonzero((mover_low[:, 0] <= lx) & (lx <= mover_high[:, 0]) & (mover_low[:, 1] <= lz)
                                  & (lz <= mover_high[:, 1]))
            floors = [f for f in (self.floor_at(lx, lz, ly), floor_below([mover_floors[i] for i in near], (lx, ly, lz)))
                      if f is not None]
            return None if not floors else float(self.project.native([lx, max(floors), lz])[2])

        for key, z in prop_pose.move_to_floor(items, floor_at).items():
            item = placed[key]
            if abs(z - item["position"][2]) > 0.5:
                self.report.setdefault("moved_to_floor", []).append(
                    {"anchor": item["entry"]["source_name"], "decoration": item["decoration"],
                     "z_before": round(float(item["position"][2]), 1), "z": round(z, 1)})
            item["position"] = (item["position"][0], item["position"][1], z)

    # --- Floors and pads -------------------------------------------------------------------------------------------
    def floor_at(self, x, z, y_from):
        near = np.nonzero((self.floor_low[:, 0] <= x) & (x <= self.floor_high[:, 0]) & (self.floor_low[:, 1] <= z)
                          & (z <= self.floor_high[:, 1]))[0]
        return floor_below([self.floors[i] for i in near], (x, y_from, z))

    def surfaces_at(self, x: float, z: float) -> list:
        """surface_column over every solid surface of the map: the compiled polygons (visible and invisible) and the
        movers' as MM9 placed them (the Isle of Ashes' sinking islet carries the Lich)."""
        if self._surfaces is None:
            polygons = [p for p in self.polygons if p.role in ("static", "invisible")]
            polygons += [p for name in self.build.plan["movers"] for p in self.source.polygons(name)
                         if p.role in ("static", "invisible")]
            polygons = [p for p in polygons if abs(p.normal[1]) >= 0.02]
            low = np.array([p.points[:, [0, 2]].min(0) for p in polygons]).reshape(-1, 2)
            high = np.array([p.points[:, [0, 2]].max(0) for p in polygons]).reshape(-1, 2)
            self._surfaces = (polygons, low, high)
        polygons, low, high = self._surfaces
        near = np.flatnonzero((low[:, 0] <= x) & (x <= high[:, 0]) & (low[:, 1] <= z) & (z <= high[:, 1]))
        return surface_column([polygons[i] for i in near], x, z)

    def first_surface(self, x: float, z: float, y_from: float) -> tuple:
        """(height, polygon) of the first surface an actor at (x, y_from, z) stands on: a DAT position in the ground
        (the first surface over it, at most BURIED_REACH up, is a top) stands on that top, else on the first top under
        it, steep or not; (None, None) when there is none."""
        column = self.surfaces_at(x, z)
        over = [(h, p) for h, p in column if h > y_from + 1]
        if over and over[0][1].normal[1] > 0 and over[0][0] - y_from <= BURIED_REACH:
            return over[0]
        under = [(h, p) for h, p in column if h <= y_from + 1 and p.normal[1] > 0]
        return under[-1] if under else (None, None)

    def actor_floor(self, anchor: str, x: float, z: float, y_from: float) -> tuple:
        """(x, floor height, z) in LithTech units where the actor whose DAT position is (x, y_from, z) stands: the
        first surface under it (first_surface), or, on a slope too steep to stand on, the nearest point round it whose
        first surface is a floor; (x, None, z) when there is no surface under it. A placement this moves is in the
        report's `actors_moved`."""
        height, polygon = self.first_surface(x, z, y_from)
        if polygon is None:
            return x, None, z
        if polygon.normal[1] >= FLOOR_NORMAL_Y:
            if height > y_from + 1:
                self.report.setdefault("actors_moved", []).append(
                    {"anchor": anchor, "why": "in the ground", "lt": [round(x, 1), round(y_from, 1), round(z, 1)],
                     "floor_lt": round(height, 1)})
            return x, height, z
        # on a slope: rings outward, nearest first, the first spot whose own first surface is a floor
        for ring in range(1, int(SLOPE_REACH / SLOPE_RING) + 1):
            distance = ring * SLOPE_RING
            for k in range(SLOPE_ANGLES):
                angle = 2 * np.pi * k / SLOPE_ANGLES
                cx, cz = x + distance * np.cos(angle), z + distance * np.sin(angle)
                floor, record = self.first_surface(cx, cz, max(y_from, height))
                if record is not None and record.normal[1] >= FLOOR_NORMAL_Y and abs(floor - height) <= 1.5 * distance:
                    self.report.setdefault("actors_moved", []).append(
                        {"anchor": anchor, "why": "off a slope", "lt": [round(x, 1), round(y_from, 1), round(z, 1)],
                         "to_lt": [round(cx, 1), round(floor, 1), round(cz, 1)]})
                    return cx, floor, cz
        raise SystemExit(f"actor {anchor}: on a slope with no floor within {SLOPE_REACH * SCALE:.0f} units")

    def fits(self, x0, z0, hx, hz, centre_floor, owner) -> bool:
        for sx in np.linspace(-1, 1, 7):
            for sz in np.linspace(-1, 1, 7):
                x, z = x0 + sx * hx, z0 + sz * hz
                floor = self.floor_at(x, z, centre_floor + 40)
                if floor is None or abs(floor - centre_floor) > 0.5 or self.owner(np.array([x, floor + 20, z])) != owner:
                    return False
        return True

    def pad(self, name, pos, dims, event, trigger: str = "pressure_plate"):
        """An MM9 touch trigger as an invisible pressure-plate face PAD_LIFT units over the floor under it: the
        trigger's footprint (Dims are half extents), shrunk until every sample over it stands on the same floor in the
        same room (so it never pokes through a wall); a trigger in a doorway moves to one side of it (half its size
        off centre) when the centred one does not fit."""
        px, y0, pz = pos
        centre_floor = self.floor_at(px, pz, y0 + dims[1])
        if centre_floor is None:
            raise SystemExit(f"trigger {name}: no floor under it")
        found = None
        for shrink in (1.0, 0.85, 0.7, 0.55, 0.4, 0.3, 0.2):
            hx, hz = dims[0] * shrink, dims[2] * shrink
            for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                x0, z0 = px + dx * dims[0] * 0.5, pz + dz * dims[2] * 0.5
                owner = self.owner(np.array([x0, centre_floor + 20, z0]))
                if self.fits(x0, z0, hx, hz, centre_floor, owner):
                    found = (x0, z0, hx, hz, owner)
                    break
            if found:
                break
        if found is None:
            raise SystemExit(f"trigger {name}: no floor under it")
        x0, z0, hx, hz, owner = found
        corners = [self.project.native([x0 + sx * hx, centre_floor, z0 + sz * hz])
                   for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        points = np.round(np.array(corners)).astype(int) + np.array([0, 0, PAD_LIFT])
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        if normal[2] < 0:
            points = points[::-1]
        node = f"TRIGGER_{name}"
        self.package.add_raw(node, points, self.package.marker_material())
        self.package.room_nodes[owner].append(node)
        self.package.metadata["surfaces"].append({"id": name, "source_node": node, "flags": ["invisible"],
                                                  "trigger": {"event_id": event, "type": trigger}})
        centre = points.mean(0).round().astype(int).tolist()
        entry = {"anchor": name, "event": event, "room": owner, "centre": centre,
                 "size": [round(2 * hx * SCALE), round(2 * hz * SCALE)], "z": int(points[0][2])}
        self.report["pads"].append(entry)
        return entry

    # --- Actors and chests -----------------------------------------------------------------------------------------
    def actor(self, o: dict, base: dict, sector_of_room: dict, group: int = 0, hidden: bool = False,
              friendly: bool = False, floor_query_lt: float | None = None, **changes) -> dict:
        """A placed actor at its DAT position on the floor under it, facing as in MM9. base: name, attributes, hp,
        hostility_type, monster_info_id, monster_id, radius, height, move_speed; changes override base fields."""
        p = o["properties"]
        x, floor, z = self.actor_floor(o["name"], p["Pos"][0], p["Pos"][2],
                                       p["Pos"][1] if floor_query_lt is None else floor_query_lt)
        if floor is None:
            raise SystemExit(f"actor {o['name']}: no floor under it")
        position = self.project.native([x, floor, z]).round().astype(int)
        position[2] += 1
        room = self.owner(np.array([x, floor + 20, z]))
        yaw = facing_degrees(p.get("Rotation"))
        record = dict(base, **changes)
        # MM9's townsfolk, uniques and town animals with an approved 3D model (mm9_npc_actor_rows.tsv): their own MM9
        # row (9000 + row) instead of the MM6-MM8 stand-in the old import placed (openyamm-cf, 2026-11-05); also an NPC
        # class on an MM9 monster row (mm9_monster_rows)
        npc_row = self.mm9_row(o, record["monster_id"]) if record["monster_id"] < 9000 else None
        switched = npc_row is not None and (npc_row in mm9_npc_actor_rows() or npc_row in mm9_monster_rows())
        if switched:
            record["monster_id"] = record["monster_info_id"] = 9000 + npc_row
        attributes, hostility = record["attributes"], record["hostility_type"]
        if o["class"] in water.SWIMMER_CLASSES and water.swimming(self.project):
            # MM9's swimmers placed in a volume float there at their DAT height (the shared water rule, water.py)
            if self._water_pieces is None:
                self._water_pieces = water.surface_pieces(self.source)
            foot = water.swimmer_foot(self.build, o, float(record["height"]), self._water_pieces)
            if foot is not None:
                position[2] = foot
        # DAT Visible 0: MM9 places it unseen and a script shows it (the Afterworld heroes and Forad, Guberland's
        # Nicolai and Alvar, the Isle's Lich summoner, Thjorgard's jumpers); each map's Lua shows it at MM9's moment
        # (MM9_ACTOR_PROPERTY_AUDIT.md B5)
        hidden = hidden or p.get("Visible", 1) == 0
        if hidden:
            attributes |= INVISIBLE_BIT
        if friendly:
            attributes &= ~AGGRESSOR_BIT
            hostility = 0
        index = len(self.report["actors"])
        out = {"actor_index": index, "name": record["name"], "npc_id": 0, "attributes": attributes,
               "hp": record["hp"], "hostility_type": hostility, "monster_info_id": record["monster_info_id"],
               "monster_id": record["monster_id"], "radius": record["radius"], "height": record["height"],
               "move_speed": record["move_speed"], "position": {k: int(v) for k, v in zip(("x", "y", "z"), position)},
               "initial_yaw_units": int(round(yaw % 360 / 360 * 2048)) % 2048, "immobile": False,
               "sprite_ids": [0, 0, 0, 0], "sector_id": sector_of_room[room], "current_action_animation": 0,
               "carried_item_id": 0, "group": group, "ally": 0, "unique_name_index": 0}
        # The 3D model's size, apart from the MM9 collision body in height/radius (bodies.draw_scale): every MM9 row
        # actor carries it, 1.0 unless the placement has its own Scale
        if out["monster_id"] >= bodies.MM9_MONSTER_ID_BASE:
            out["draw_scale"] = bodies.draw_scale(out["monster_id"], p) or 1.0
        if "SightDistance" in p or "HearingDistance" in p:
            # MM9's AI settings of the placement (devdocs/mm9_rework/monster_ai/PROFILE.md)
            out["mm9_ai"] = self.mm9_ai(p, self.mm9_row(o, record["monster_id"]))
            if p.get("ExecuteScript", 1) == 0:
                # ExecuteScript 0: MM9 does not start the placement's script at load (object.lto's AI ReadProp at
                # 0x1000cf34 runs ScriptName only with it set; default 1), and wandering and patrols are that script's
                # (BaseWander.inc, the path scripts): it stands where placed (Drangheim Prison's PatrolGuard1 and
                # Guard6, Yanmir's caged children; MM9_ACTOR_PROPERTY_AUDIT.md B7)
                for key in ("wander", "path", "path_random", "path_stops", "wander_leash", "wander_wait",
                            "wander_time"):
                    out["mm9_ai"].pop(key, None)
        from mm9_ai_placement import starts_dormant
        if starts_dormant(out.get("mm9_ai", {}), record["monster_id"], p):
            # A dormant start the AI wakes by itself (MM9_MONSTER_AI_PLAN.md phase 4b): one disturbed by hits,
            # calls and sightings (a hanging Flying Icky). Trigger starts stay with the map's own wiring.
            out["dormant"] = True
        if friendly and (record["monster_id"] < 9000 or switched):
            # A townsperson (a stand-in engine row, or MM9's own NPC row): it runs NPCBase.inc (mm9StandInCivilianProfile).
            out["mm9_civilian"] = True
        if p.get("CanDamage", 1) == 0:
            # MM9's CanDamage 0 (townsfolk, the gods, Yanmir, Ebora, the coffin mummies ...): no hit hurts it until the
            # map's Lua turns it on (MM9.setCanDamage, MM9's SetPropNumber CanDamage; MM9_ACTOR_PROPERTY_AUDIT.md)
            out["mm9_can_receive_damage"] = False
        if p.get("ShouldRepopulate", 1) == 0:
            # MM9's ShouldRepopulate 0 (retainers, bank orbs, quest NPCs, Kluso's Count ...): a map refill keeps it as
            # the party left it (the engine's keepActorsThroughRefill; MM9_ACTOR_PROPERTY_AUDIT.md B4)
            out["respawns_on_refill"] = False
        self.report["actors"].append({"actor_index": index, "anchor": o["name"], "class": o["class"],
                                      "monster_id": record["monster_id"], "room": room, "group": group,
                                      "hidden": hidden, "friendly": friendly})
        return out

    def mm9_ai(self, properties: dict, row: int | None = None) -> dict:
        """The scene actor's mm9_ai map from its DAT properties and placement script (mm9_ai_placement.py): sight,
        hearing, runaway chance, ranged type, resurrection, wander and its markers, dormant, hostility, summons and
        the profile fields its own script decides where they differ from its row's (row: its MONSTERS.txt row)."""
        from mm9_ai_placement import placement_ai
        if not hasattr(self, "_mm9_markers"):
            self._mm9_markers = {name: o["properties"]["Pos"] for name, o in self.source.by_name.items()
                                 if isinstance(o["properties"].get("Pos"), list)}
            self._mm9_marker_properties = {name: o["properties"] for name, o in self.source.by_name.items()}
            self._mm9_script_memo = {}
        return placement_ai(properties, self._mm9_markers, self.project.native, self._mm9_script_memo, row,
                            self._mm9_marker_properties, facing_degrees)

    def mm9_row(self, o: dict, monster_id: int) -> int | None:
        """The placed object's own MONSTERS.txt row, by its DAT class as the ODM transcoder resolves it (a monster's,
        else an NPC's, whatever stand-in row the converter places it on); else its runtime MM9 row."""
        from transcode_mm9_dat_to_odm import (property_map_cased, read_mm9_npc_replacements,
                                              resolve_mm9_monster_replacement, resolve_mm9_npc_replacement)
        if not hasattr(self, "_mm9_row_replacements"):
            self._mm9_row_replacements = (monster_replacements(), read_mm9_npc_replacements(
                ROOT / "mm9/extracted/DATA/DATA/ACTOR.txt",
                ROOT / "tools/mm9_import_discovery/mm9_npc_legacy_replacements.tsv",
                ROOT / "assets_dev/engine/data_tables/monster_descriptors.txt"))
        index = o.get("index")
        if isinstance(index, int) and 0 <= index < len(self.source.world.objects):
            world_object = self.source.world.objects[index]
            monsters, npcs = self._mm9_row_replacements
            try:
                replacement = resolve_mm9_monster_replacement(world_object, monsters)
            except ValueError:
                replacement = None
            if replacement is None:
                replacement = resolve_mm9_npc_replacement(world_object, property_map_cased(world_object), npcs)
            if replacement is not None:
                return replacement.source_number
        return monster_id - 9000 if monster_id >= 9000 else None

    def npc_row_base(self, o: dict) -> dict | None:
        """The actor base record of a monster-class object with no MM9 monster replacement but its own MM9 row with a
        3D model (mm9_npc_actor_rows.tsv: the farm animals, the Temple of Honk's fish and geese, townsfolk and
        uniques): the row by the NPC resolver (mm9_row), else by its DAT class against the runtime row names
        (`Fish`, `Brown Cow`), from worlds/mm9 monster_data.txt and monster_descriptors.txt (row 9000 + N)."""
        from transcode_mm9_dat_to_odm import ACTOR_ATTRIBUTE_AGGRESSOR, normalized_binding_name, read_numeric_tsv_rows
        if not hasattr(self, "_npc_row_tables"):
            data = read_numeric_tsv_rows(ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt")
            descriptors = read_numeric_tsv_rows(ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt")
            by_name = {normalized_binding_name(data[9000 + row][1]): row for row in mm9_npc_actor_rows()
                       if 9000 + row in data}
            self._npc_row_tables = (data, descriptors, by_name)
        data, descriptors, by_name = self._npc_row_tables
        row = self.mm9_row(o, 0)
        if row is None or row not in mm9_npc_actor_rows():
            row = by_name.get(normalized_binding_name(o["class"]))
        if row is None or 9000 + row not in data or 9000 + row not in descriptors:
            return None
        cells, descriptor = data[9000 + row], descriptors[9000 + row]
        hostility = int(cells[12])
        return {"name": cells[1].strip(), "attributes": ACTOR_ATTRIBUTE_AGGRESSOR if hostility else 0,
                "hp": int(cells[4]), "hostility_type": hostility, "monster_info_id": 9000 + row,
                "monster_id": 9000 + row, "radius": int(descriptor[3]), "height": int(descriptor[2]),
                "move_speed": int(cells[13])}

    def monster_bases(self, cache_only: bool = False, npc_rows: bool = False) -> dict:
        """DAT object name -> the actor base record of its MM9 monster row (objects without a row are listed in
        report['omitted']). cache_only: also the `CacheOnly 1` objects (never placed: templates for what a map spawns,
        Ta'Sar Academy's crate Dagrell). npc_rows: a class with no monster replacement takes its own MM9 NPC row
        where it has one with a 3D model (npc_row_base; opt-in, 2026-11-06, FINAL_REBUILD_WORK.md M19: maps whose
        hooks give such classes their own records, Drangheim Prison and Ta'Sar Academy, keep them)."""
        from transcode_mm9_dat_to_odm import ACTOR_ATTRIBUTE_AGGRESSOR, resolve_mm9_monster_replacement
        replacements = monster_replacements()
        out = {}
        for o, world_object in zip(self.source.objects, self.source.world.objects):
            if o["class"] not in self.project.monster_classes:
                continue
            # `CacheOnly 1`: LithTech loads the object's model and never spawns it (Boot Camp's
            # EvilGrandSorcererCACHEONLY, ReverendMonkCACHEONLY and OrbusCACHEONLY, Wizard's Lab's one).
            if float(o["properties"].get("CacheOnly", 0) or 0) and not cache_only:
                self.report["omitted"].append({"anchor": o["name"], "class": o["class"], "reason": "CacheOnly"})
                continue
            replacement = resolve_mm9_monster_replacement(world_object, replacements)
            if replacement is None and npc_rows and (base := self.npc_row_base(o)) is not None:
                out[o["name"]] = base
                continue
            if replacement is None:
                if not cache_only:          # reported once, by the placing call
                    self.report["omitted"].append({"anchor": o["name"], "class": o["class"],
                                                   "reason": "no MM9 monster row in the runtime tables"})
                continue
            # Hostility 0 rows (the harmless MM9 animals) are placed friendly: no aggressor bit.
            aggressor = ACTOR_ATTRIBUTE_AGGRESSOR if replacement.hostility else 0
            out[o["name"]] = {"name": replacement.display_name, "attributes": aggressor,
                              "hp": replacement.hit_points, "hostility_type": replacement.hostility,
                              "monster_info_id": replacement.runtime_monster_id,
                              "monster_id": replacement.runtime_monster_id, "radius": replacement.radius,
                              "height": replacement.height, "move_speed": replacement.move_speed}
        return out

    @property
    def item_source_data(self) -> dict:
        """The map's MM9 item source manifest as scene data (chests, bone piles, urn bags), built once."""
        if not hasattr(self, "_item_sources"):
            self._item_sources = item_sources(self.project, self.source.world.objects)
        return self._item_sources

    @property
    def loot_records(self) -> list[dict]:
        if not hasattr(self, "_loot"):
            self._loot = self.loot()
        return self._loot

    def loot(self) -> list[dict]:
        """The chests' loot records (treasure type and level, trap level, repopulate) in this map's frame, container k
        in DAT order, from the shared MM9 item sources."""
        out = []
        for record in self.item_source_data["loot_containers"]:
            record = dict(record)
            record.pop("world_visual", None)
            if any(self.project.offset):
                position = self.project.native(record["source_position_lt"]).round().astype(int)
                record["position"] = {k: int(v) for k, v in zip(("x", "y", "z"), position)}
            out.append(record)
            self.report["chests"].append({"container_id": record["container_id"], "anchor": record["source_name"],
                                          "event": CHEST_EVENT + record["container_id"],
                                          "treasure_level": record["random_treasure_level"],
                                          "trap_level": record["trap_level"]})
        return out
