"""
An MM9 outdoor (wilderness) map as a BLV open to the sky: the shared part of the outdoor-as-BLV route, piloted on the
Isle of Ashes (../mm9r_isleofashes_blv/README.md) and Sturmford (../mm9r_sturmford_blv/README.md). A map project's
convert.py redirects the review root if it installs into its own, subclasses OutdoorBlvHooks and runs dungeon.main.

What it does on top of the city hooks (city/hooks.py: sky faces, open sky, daylight, half steps):

- **The near box and the far sea** (Frosgard City's route). The voxel pass, rooms and face assignment cover the near
  box: every terrain model's extent with a margin, from just under the sea surface to over the highest peak. The grid's
  outer layer is solid, so the air ends at the box. What lies outside it is far scenery of the open-air room: the sea
  surface out to the BLV's int16 frame. Everything under the sea surface goes (MM9's sea floor, the terrain's
  underwater skirts: nothing shows through the opaque sea), and so does the far sky shell (our sky is drawn behind).
- **The sea** (the map's Ocean brush), in 1 024 LT tiles, is drawn as the deep outdoor sea (liquids.py `sea_mm9`,
  MM6-MM8's outdoor sea colour: `deep_sea`), not as the bright indoor ocean its MM9 texture names. Without
  `map: {swim: true}` it is a solid surface the party wades on. With it (`swimmable_sea`), the near box reaches down
  under the sea, the seabed stays, the sea surface in the box turns nonsolid over the water volume (dungeon/water.py,
  BlueWater0) and four invisible walls round the box keep a swimmer in it; the far sea stays a wading surface
  (devdocs/INDOOR_OPEN_SKY.md "Swimming").
- **One open-air room**: no streets, no UserPortals.
- **Footsteps** by floor texture (footsteps.py), **the party's slopes** (`party_movement: {steep_slopes: block}`: no
  climbing what a monster cannot, MM9's cliffs), **indoor model bindings** for the map's outdoor props
  (bind_indoor_decorations) and **boat arrivals** (rewrite_transport).

- **Monster barriers** come from the shared build (dungeon/build.py `actor_barriers`, every converted map): without
  them monsters crowding the party on a bridge were pushed off into the sea (Isle of Ashes, 2026-11-02).
- **Monsters**: MM9's own (the map's `monster_classes`), except those with no floor under them. With a swimmable sea,
  those under the sea surface (spores, sea monsters) swim at their DAT height (the centre of their body box, kept under
  the surface and over the seabed: swimmer_foot); those in the far sea past the near box move to its nearest point of
  water (`actors_moved_into_near_sea_lt`); one with no seabed even there is left out (`actors_in_far_sea`). `outdoor: {test_population: N}` adds copies of them on the
  floor 400-1 200 units round the originals until the map holds N: a pathing and performance aid at MM6-MM8 density,
  not a design (the real population comes from the encounter plan, devdocs/mm9_rework/PLAN.md).

overrides.yml `outdoor` block (all optional): `voxel` is the map's `voxel` (32 LT: a whole region's air in some 20-30 M
voxels); `ocean_model` (default Ocean), `near_margin_lt` (default 256), `props` (a props.json path relative to the
project, entries in the map's frame), `test_population` (above), `decoration_swaps` ({decoration: decoration}: props drawn as another decoration, e.g. MM9's trees as ours),
`outdoor_view` (default true: the scene's sky takes
`view: outdoor`, an outdoor map's view distance and haze).
`weather` (default rain; snow, rain_and_snow or none: the scene's sky `weather`, WeatherModel's rolls).
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

import dungeon.build as dungeon_build
import footsteps
import liquids
import review_root
from city.hooks import CityHooks, apply_weather
from dungeon.geometry import Polygon, VoxelGrid, air_regions, clip, mark_polygons
from dungeon.source import ROOT, SCALE, floor_below

SKY_TEXTURE = "skymarker.dtx"
OCEAN_TILE_LT = 1024.0
INT16_NATIVE = 32512.0
TERRAIN_PREFIXES = ("terrain", "earthquake")
# A swimmer MM9 put in the far sea moves this far (LT) inside the near box's walls (swimmer_into_near_box)
NEAR_SEA_INSET = 160.0
# MM9's AISwimFly monsters (generate_mm9_monster_tables.py SWIMMER_SOURCES): swimmers wherever they are over the sea
# Region map Lua (map_script): the load and poll events of the shared part; a region's own events start at 300
EV_REGION_LOAD, EV_REGION_POLL = 1, 260
SCRIPTS_DIR = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS"
EV_BARRED = 360          # a barred door's destructible dying (BARRED_DOORS): EV_BARRED + k
EV_STAT_STONE = 390      # a StatStone's click: EV_STAT_STONE + k (stat_stones)
# MM9's StatStone class (Stat, BonusAmt, BonusSeconds: floats stored as their bits) gives the party a timed bonus to
# one primary stat. MM9's stat ids (GLOBALS.inc STAT_MIGHT..STAT_LUCK: might, magic, endurance, accuracy, speed, luck)
# -> the engine's timed primary stat bonuses (Party::applyTemporaryPrimaryStatBonus: might, intellect, personality,
# endurance, speed, accuracy; magic is intellect and personality, as MMerge's).
STAT_STONE_STATS = {0: ("Might", (0,)), 1: ("Magic", (1, 2)), 2: ("Endurance", (3,)), 3: ("Accuracy", (5,)),
                    4: ("Speed", (4,))}
# ForadWorld.scr: the party's location key by its world parameter (keys 1024-1033; anything else 1033)
FORAD_WORLD_KEYS = {"isleofashes": 1024, "thjorgard": 1025, "sturmford": 1026, "drangheim": 1027, "guberland": 1028,
                    "frosgard": 1029, "thronheim": 1030, "lindisfarne": 1031, "yorwick": 1032}
# Region people (npcs()): as the cities' townsfolk (mm9r_thjorgardcity/convert.py)
NPC_STAND_IN_ROW = 367                  # Peasant Human2 MaleA: an NPC the old import did not place
NPC_PEASANT_ROWS = range(301, 383)      # the Peasant family rows (monster_data.txt)
NPC_PEACEFUL_ALLY = (352 - 1) // 3 + 1  # monster type of row 352 (Peasant Human1 FemaleB A): neutral to the party
NPC_GROUP = 1

SWIMMER_CLASSES = ("JellySpore", "GelatinousSpore", "NettleSpore", "SeaMonsterMale", "SeaMonsterFemale",
                   "Fish")


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


class Layout:
    """The map's near box, sea and open-air point, from its DAT (terrain models, the Ocean brush)."""

    def __init__(self, source, settings: dict, swim: bool = False):
        models = source.models
        self.ocean_model = settings.get("ocean_model", "Ocean")
        ocean = models.get(self.ocean_model)
        self.ocean_y = float(np.array(ocean.points)[:, 1].max()) if ocean is not None else None
        # By name (Terrain0, Earthquake) or by class (Mountain Pass's CliffsTerrain0 and PathTerrain1)
        terrain = [np.array(m.points) for name, m in models.items()
                   if name.lower().startswith(TERRAIN_PREFIXES) or source.object_class(name) == "Terrain"]
        points = np.concatenate(terrain)
        margin = float(settings.get("near_margin_lt", 256))
        # A swimmable sea (map: {swim: true}) keeps the seabed and the air under the surface: the box reaches under it
        bottom = (self.ocean_y - 32.0) if self.ocean_y is not None and not swim else points[:, 1].min() - margin
        top = points[:, 1].max() + 200.0
        self.near_box = (np.array([points[:, 0].min() - margin, bottom, points[:, 2].min() - margin]),
                         np.array([points[:, 0].max() + margin, top, points[:, 2].max() + margin]))
        centre = (self.near_box[0] + self.near_box[1]) / 2
        self.open_air_point = (float(centre[0]), float(top - 50.0), float(centre[2]))

    def far_limits(self, project):
        """The LT box whose native image stays inside int16 (the frame's offset makes it asymmetric)."""
        offset = np.array(project.offset, float)
        low = np.array([(-INT16_NATIVE + offset[0]) / SCALE, -1e9, (-INT16_NATIVE + offset[1]) / SCALE])
        high = np.array([(INT16_NATIVE + offset[0]) / SCALE, 1e9, (INT16_NATIVE + offset[1]) / SCALE])
        return low, high


class OutdoorBlvHooks(CityHooks):
    # Every MM9 door group takes a click event (a region's doors are not doorways between rooms: dungeon/movers.py)
    all_doors_click = True
    """The hooks of an MM9 outdoor map built as a BLV open to the sky (module docstring)."""
    generator = "mm9r_outdoor_blv"

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.layout = None
        self.far = []
        self.exclude_sources = set()     # DAT objects a map places itself (story actors): not placed by actors()
        hooks = self
        shared_build_voxels = dungeon_build.build_voxels
        shared_assign_faces = dungeon_build.assign_faces

        def sealed_build_voxels(polygons, source, extra_seeds=()):
            """build_voxels with the grid's outer layer solid: the air ends at the near box."""
            voxel = source.project.voxel
            points = np.concatenate([p.points for p in polygons])
            grid = VoxelGrid(points.min(0), points.max(0), voxel)
            solid = np.zeros(grid.shape, bool)
            mark_polygons(grid, solid, [polygon.points for polygon in polygons if polygon.role == "static"], voxel / 4)
            solid[[0, -1], :, :] = True
            solid[:, [0, -1], :] = True
            solid[:, :, [0, -1]] = True
            seeds = [list(hooks.layout.open_air_point)]
            classes = source.project.seed_classes | source.project.monster_classes
            seeds += [o["properties"]["Pos"] for o in source.objects if o["class"] in classes]
            seeds += [list(s) for s in extra_seeds]
            air, stats = air_regions(grid, solid, np.array(seeds, float))
            return grid, solid, air, stats

        def assign_with_far(rooms_, polygons, portals, stats, log, **kwargs):
            """The shared face assignment for the near polygons; the far scenery goes whole to the open-air room."""
            kept = shared_assign_faces(rooms_, polygons, portals, stats, log, **kwargs)
            label = rooms_.owner(np.array(hooks.layout.open_air_point))
            for polygon in hooks.far:
                polygon.label = label
            stats["far_scenery_faces"] = len(hooks.far)
            return kept + hooks.far

        dungeon_build.build_voxels = sealed_build_voxels
        dungeon_build.assign_faces = assign_with_far

    def settings(self, build) -> dict:
        return build.project.overrides.get("outdoor") or {}

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        swim = dungeon_build.water.swimming(build.project)
        self.layout = Layout(build.source, self.settings(build), swim)
        ocean_y = self.layout.ocean_y
        out, ocean, under = [], 0, 0
        # The sky-flagged polygons (Sturmford's 27 648 x 31 232 sturmfordgrass lid, Frosgard's refineryterrain one) are
        # already sky faces: the shared build does that for every map (Source.sky_flagged_as_sky).
        for k, polygon in enumerate(polygons):
            if polygon.model == self.layout.ocean_model:
                polygon.role = "static"
                tiles = _tiles(polygon, OCEAN_TILE_LT, f"oc{k}")
                ocean += len(tiles)
                out += tiles
            elif (ocean_y is not None and not swim and polygon.points[:, 1].max() < ocean_y - 1
                  and polygon.role != "invisible"):
                under += 1
            else:
                out.append(polygon)
        build.stats["ocean_tiles"] = ocean
        build.stats["under_sea_dropped"] = under
        polygons = super().edit_polygons(build, out)        # half steps
        near = self.near_and_far(build, polygons)
        if swim and ocean_y is not None:
            near = self.swimmable_sea(build, near)
        return near

    def deep_sea(self, build, scene: dict) -> None:
        """The sea's faces (the Ocean brush's texture) drawn as the deep outdoor sea (liquids.py `sea_mm9`), not as the
        indoor ocean their MM9 texture names (Dook's Castle's bright Ocean4)."""
        ocean = build.source.models.get(self.layout.ocean_model) if self.layout else None
        if ocean is None:
            return
        aliases = {build.source.aliases[ocean.textures[ocean.surfaces[q.surface_index].texture_index].lower()]["alias"]
                   .lower() for q in ocean.polies}
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        overrides = scene.setdefault("initial_state", {}).setdefault("face_attribute_overrides", [])
        by_face = {entry["face_index"]: entry for entry in overrides}
        count = 0
        for face in blv["faces"]:
            if face["texture_name"].lower() in aliases:
                if face["index"] in by_face:
                    by_face[face["index"]]["texture_name"] = liquids.SEA_TEXTURE
                else:
                    overrides.append({"face_index": face["index"], "texture_name": liquids.SEA_TEXTURE})
                count += 1
        build.stats["deep_sea_faces"] = count

    def swimmable_sea(self, build, near: list) -> list:
        """map: {swim: true}: the sea in the near box is MM9's water volume (dungeon/water.py writes BlueWater0 as the
        scene's `water_volumes`), so its surface tiles stop being a floor (non-solid: the party sinks through and swims
        up through them) and the seabed under them stays (edit_polygons keeps it). The far sea stays a solid surface;
        invisible walls round the near box, from its bottom to a little over the sea, keep a swimmer from going out
        under it."""
        surfaces = 0
        for polygon in near:
            if polygon.model == self.layout.ocean_model:
                polygon.role = "nonsolid"
                surfaces += 1
        low, high = self.layout.near_box
        top = self.layout.ocean_y + 96.0
        texture = next(name for name in build.source.aliases if name.endswith("misc\\invisible.dtx"))
        alias = build.source.aliases[texture]
        corners = [(low[0], low[2]), (high[0], low[2]), (high[0], high[2]), (low[0], high[2])]
        walls = []
        for (x0, z0), (x1, z1) in zip(corners, corners[1:] + corners[:1]):
            # wound so the face looks into the box (LithTech y up)
            points = np.array([[x0, low[1], z0], [x0, top, z0], [x1, top, z1], [x1, low[1], z1]], float)
            polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], alias["source_texture"],
                              (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 1.0, 0])), 0x105, "SeaEdge",
                              "invisible")
            polygon.notes.update(width=alias["width"], height=alias["height"])
            walls.append(polygon)
        build.stats["sea_surface_nonsolid"] = surfaces
        build.stats["sea_edge_walls"] = len(walls)
        return near + walls

    def near_and_far(self, build, polygons: list) -> list:
        low, high = self.layout.near_box
        near, far = [], []
        for k, polygon in enumerate(polygons):
            inside, outside = _clip_box(polygon, low, high, f"nb{k}")
            if inside is not None:
                near.append(inside)
            far += outside
        limit_low, limit_high = self.layout.far_limits(build.project)
        ocean_y = self.layout.ocean_y
        kept, dropped = [], {"under_sea": 0, "sky": 0, "past_int16": 0}
        for k, polygon in enumerate(far):
            texture = polygon.texture.replace("\\", "/").split("/")[-1].lower()
            if texture == SKY_TEXTURE:
                dropped["sky"] += 1
                continue
            if ocean_y is not None and polygon.points[:, 1].max() < ocean_y - 1:
                dropped["under_sea"] += 1
                continue
            inside, _ = _clip_box(polygon, limit_low, limit_high, f"fl{k}")
            if inside is None:
                dropped["past_int16"] += 1
                continue
            kept.append(inside)
        self.far = kept
        build.stats["near_box_lt"] = [[round(float(v)) for v in low], [round(float(v)) for v in high]]
        build.stats["near_polygons"] = len(near)
        build.stats["far_scenery_polygons"] = len(kept)
        build.stats.update({f"far_dropped_{key}": value for key, value in dropped.items()})
        return near

    def extra_seeds(self, build) -> list:
        return super().extra_seeds(build)

    def extra_portals(self, build) -> list:
        """No structure: the open air is one room (no streets, no UserPortals)."""
        build.city_report = {"structure": "none: one open-air room (outdoor_blv.py)"}
        return []

    # --- population -------------------------------------------------------------------------------------------------
    def props_path(self, build):
        relative = self.settings(build).get("props")
        return (self.project_dir / relative).resolve() if relative else None

    def populate(self, build) -> None:
        path = self.props_path(build)
        if path is None:
            return
        entries = json.loads(path.read_text())
        swaps = self.settings(build).get("decoration_swaps") or {}
        for entry in entries:
            entry.setdefault("kind", "prop")
            entry["decoration"] = swaps.get(entry["decoration"], entry["decoration"])
            # MM9 names such as Tree16 are also decoration names, which an entity name may not be; the DAT name stays
            # in `dat_name`, which prop_pose matches against the DAT object (without it the regions' props lost MM9's
            # pose turns, standing rule and MoveToFloor drops: Ravensford's books sunk into their shelf)
            entry.setdefault("dat_name", entry["source_name"])
            entry["source_name"] = "obj_" + entry["source_name"]
        staged = build.project.work / "props.json"
        staged.write_text(json.dumps(entries))
        events, cogs = self.prop_events(build)
        build.content.props(staged, events={"obj_" + k: v for k, v in events.items()},
                            cogs={"obj_" + k: v for k, v in cogs.items()})
        # The region's own entities beyond its props (regionlua.py `populate(hooks, build)`: Afterworld's six fires)
        module = self.region_module(build)
        if module is not None and hasattr(module, "populate"):
            module.populate(self, build)

    def region_module(self, build):
        """The region's own scripted objects (`regionlua.py` in its project), or None."""
        if not hasattr(self, "_region_module"):
            self._region_module = None
            path = self.project_dir / "regionlua.py"
            if path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"regionlua_{build.project.stem}", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._region_module = module
        return self._region_module

    def map_script(self, build) -> str:
        """The region's map Lua (REGIONS_FINISH.md step 2): MM9's doors (a click toggles each door group; a region's
        keyed doors open only with their key item) and chests; ForadWorld.scr (in every region: the party's location
        key, the shops' night key); then the region's own scripted objects and people from `regionlua.py` (its
        `extend(hooks, build, script)` adds handlers and returns its on-load events; the cities' citylua.py pattern).
        Door groups with the map's own click events (hooks `mover_events`: the Isle of Ashes' bunker and hut doors)
        are the region's Lua's to handle."""
        from dungeon import lua
        module = self.region_module(build)
        keyed = dict(getattr(module, "KEYED_DOORS", {}) or {})      # door group -> key item (doorlock.scr)
        barred = self.barred_doors(build)                             # door group -> (destructible, its death event)
        # MM9 doors that never move (MoveDist 0: the facades' doors), and doors MM9 keeps Locked with no key
        # (doorlock.scr: KEYED_DOORS) and no trigger that unlocks them, say they are locked, as the cities' do
        locked_models = self.locked_models(build)
        fixed = sorted({m["group"] for m in build.movers if m["event"] and m["group"] not in keyed
                        and m["group"] not in barred and m["group"] not in self.mover_events
                        and ((not m.get("move_length") and m.get("motion") != "rotate")
                             or any(name.lower() in locked_models for name in m.get("dat_models", [])))})
        script = lua.Script(build, build.project.overrides["map"].get("display_name", build.project.stem))
        script.doors(skip_groups=set(keyed) | set(fixed) | set(barred))
        script.chests()
        lines = [
            "local function has(k) return MM9.hasKey(k) == 1 end",
            "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
            "local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; "
            "if gold > 0 then MM9.giveGold(gold) end; quest() end",
            "",
        ]
        registrations = []
        locked = sorted({m["event"] for m in build.movers if m["group"] in fixed})
        if locked:
            lines += [f"-- Doors MM9 never opens ({', '.join(fixed)}): a click says so (doorlock01.wav).",
                      "local function lockedDoor() evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0); "
                      "evt.StatusText(\"The door is locked.\") end"]
            lines += [f"handlers[{event}] = lockedDoor" for event in locked]
            registrations += [(event, "Locked door", "Door") for event in locked]
        for group, item in sorted(keyed.items()):
            events = sorted({m["event"] for m in build.movers if m["group"] == group and m["event"]})
            doors = [m["door_id"] for m in build.movers if m["group"] == group]
            calls = " ".join(f"evt.SetDoorState({d}, DoorAction.Trigger)" for d in doors)
            for event in events:
                lines += [f"-- doorlock.scr ({group}): it opens only while the party carries item {item}.",
                          f"handlers[{event}] = function()",
                          f"    if MM9.hasItem({item}, \"{build.project.stem}:{group}\") == 1 then {calls}",
                          "    else evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0); "
                          "evt.StatusText(\"The door is locked.\") end",
                          "end"]
                registrations.append((event, "Locked door", "Door"))
        for group, (names, death) in sorted(barred.items()):
            indices = [build.source.by_name[name.lower()]["index"] for name in names]
            broken = " and ".join(f"evt.IsDestructibleDestroyed({index})" for index in indices)
            doors = [m["door_id"] for m in build.movers if m["group"] == group]
            lines += [f"-- {group} is barred by {', '.join(names)} (destructibles whose DeathTrigger opens it): a click "
                      "says so until they are broken; breaking the last opens the door (and tells the region's",
                      "-- handlers.barredOpened).",
                      f"handlers[{death}] = function()",
                      f"    if not ({broken}) then return end",
                      "    " + " ".join(f"evt.SetDoorState({d}, DoorAction.Open)" for d in doors),
                      f"    if handlers.barredOpened then handlers.barredOpened(\"{group}\") end",
                      "end"]
            registrations.append((death, f"{group} unbarred", None))
            # unbarred, MM9's USE toggles a PushOpen door; a PushOpen 0 one (Sturmford's drawbridge: its open locks
            # it) only its trigger opens, so a click leaves it down
            members = {name for m in build.movers if m["group"] == group for name in m.get("dat_models", [])}
            usable = any(float(build.source.properties(name).get("PushOpen", 1) or 0) for name in members)
            action = "DoorAction.Trigger" if usable else "DoorAction.Open"
            for event in sorted({m["event"] for m in build.movers if m["group"] == group and m["event"]}):
                lines += [f"handlers[{event}] = function()",
                          f"    if {broken} then "
                          + " ".join(f"evt.SetDoorState({d}, {action})" for d in doors),
                          "    else evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0); "
                          "evt.StatusText(\"It is barred.\") end",
                          "end"]
                registrations.append((event, "Barred door", "Door"))
        forad = next((o for o in build.source.objects
                      if str(o["properties"].get("ScriptName") or "").lower().endswith("foradworld.scr")), None)
        load = []
        if forad is not None:
            world = str(forad["properties"].get("ScriptParams") or "").strip().lower()
            key = FORAD_WORLD_KEYS.get(world, 1033)
            lines += [
                f"-- ForadWorld.scr ({forad['name']}, \"{world}\"): key {key} is the party's location while here (keys",
                "-- 1024-1033), and key 5017 closes the shops from 20:00 to 06:00 (MM9's dialogues test it).",
                "local function shopHours()",
                "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
                "    local closed = hour >= 20 or hour < 6",
                "    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then "
                "MM9.takeKey(5017) end",
                "end",
                f"handlers[{EV_REGION_POLL}] = function() shopHours() end",
                "",
            ]
            load = ["    for k = 1024, 1033 do MM9.takeKey(k) end", f"    MM9.giveKey({key})", "    shopHours()"]
            registrations.append((EV_REGION_POLL, "Shop hours", None, "timer"))
        stone_lines, stone_registrations = self.stat_stone_lines(build)
        lines += stone_lines
        registrations += stone_registrations
        script.add(lines, *registrations)
        if module is not None:
            module.extend(self, build, script)
        # The load event: ForadWorld's part, then the region's own (regionlua.py sets handlers.regionLoad)
        script.add([f"handlers[{EV_REGION_LOAD}] = function()"] + load +
                   ["    if handlers.regionLoad then handlers.regionLoad() end", "end", ""],
                   (EV_REGION_LOAD, "Map load", None))
        on_load = [EV_REGION_LOAD]
        return script.finish(on_load=on_load)

    def prop_events(self, build) -> tuple[dict, dict]:
        """A map's scripted props by DAT name: (click event, SetSprite key): the region's regionlua.py
        `prop_events(build)` and the stat stones (stat_stones), else none."""
        module = self.region_module(build)
        events, cogs = module.prop_events(build) if module is not None and hasattr(module, "prop_events") else ({}, {})
        events = dict(events)
        for k, stone in enumerate(self.stat_stones(build)):
            events[stone["name"]] = EV_STAT_STONE + k
        return events, cogs

    def stat_stones(self, build) -> list:
        """The region's StatStone objects with a bonus (Boot Camp's museum pieces have none): name, MM9 stat id,
        amount and game seconds."""
        def number(value):
            if isinstance(value, int):
                return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
            return float(value or 0)
        out = []
        for o in build.source.objects:
            p = o["properties"]
            if o["class"] != "StatStone" or "statstone" not in str(p.get("Filename") or "").lower():
                continue
            stat, amount, seconds = int(round(number(p.get("Stat")))), number(p.get("BonusAmt")), \
                number(p.get("BonusSeconds"))
            if amount > 0 and seconds > 0 and stat in STAT_STONE_STATS:
                out.append({"name": o["name"], "stat": stat, "amount": int(round(amount)), "seconds": seconds})
        return out

    def stat_stone_lines(self, build) -> tuple[list, list]:
        """The stat stones' click handlers (the StatStone class's use): the bonus on every party member, once while it
        lasts (map var StatStoneUntil<k>, game minutes): a second click meanwhile would stack it."""
        lines, registrations = [], []
        for k, stone in enumerate(self.stat_stones(build)):
            name, indices = STAT_STONE_STATS[stone["stat"]]
            event, until = EV_STAT_STONE + k, f"StatStoneUntil{k}"
            hours = stone["seconds"] / 3600
            told = f"+{stone['amount']} {name} for {hours:g} hour{'s' if hours != 1 else ''}"
            buffs = " ".join(f"evt.ApplyPartyPrimaryStatBuff({i}, {stone['amount']}, {stone['seconds']:g})"
                             for i in indices)
            lines += [f"-- {stone['name']} (StatStone: Stat {stone['stat']} {name}, +{stone['amount']} for "
                      f"{stone['seconds']:g} s)",
                      f"handlers[{event}] = function()",
                      f"    if evt.CurrentGameMinutes() < var(\"{until}\") then",
                      "        evt.StatusText(\"The stone's power is still with you.\") return",
                      "    end",
                      f"    {buffs}",
                      f"    set(\"{until}\", evt.CurrentGameMinutes() + {round(stone['seconds'] / 60)})",
                      "    evt.PlaySoundName(\"events/dingbell.wav\", 0, 0, 0)",
                      f"    evt.StatusText(\"{told}\")",
                      "end"]
            registrations.append((event, "Stat stone", "Touch"))
        return lines, registrations

    @staticmethod
    def locked_models(build) -> set:
        """DAT door models MM9 keeps locked for good (lower case): `Locked` set, and no object's trigger (a
        `...Message` property, MessageName<k> or Death/DamageTriggerMessage) sends them `unlock`."""
        unlocked = set()
        for o in build.source.objects:
            for key, value in o["properties"].items():
                if "Message" in key and isinstance(value, str) and value.strip().lower() == "unlock":
                    unlocked.add(str(o["properties"].get(key.replace("Message", "Target")) or "").lower())
        return {o["name"].lower() for o in build.source.objects
                if float(o["properties"].get("Locked", 0) or 0) and o["name"].lower() not in unlocked}

    def barred_doors(self, build) -> dict:
        """The region's regionlua.py `BARRED_DOORS` ({door group: the destructible's DAT name, or a list of them}:
        MM9's boards nailed across a gate, Sturmford's two drawbridge chains, whose DeathTrigger opens the door), each
        with the event its destructibles' deaths run: {group: ([names], event)}."""
        module = self.region_module(build)
        barred = dict(getattr(module, "BARRED_DOORS", {}) or {})
        return {group: ([names] if isinstance(names, str) else list(names), EV_BARRED + k)
                for k, (group, names) in enumerate(sorted(barred.items()))}

    def destructible_events(self, build) -> dict:
        """Map events bound to destructibles (dungeon/destructibles.py): {DAT name: (destroyed event, damaged event)}:
        the barred doors' and the region's regionlua.py `destructible_events(build)`."""
        module = self.region_module(build)
        events = {name: (death, 0) for names, death in self.barred_doors(build).values() for name in names}
        if module is not None and hasattr(module, "destructible_events"):
            events.update(module.destructible_events(build))
        return events

    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        # npc_rows: MM9's farm animals (Boot Camp's goats and cows, Yorwick's ewe) on their own rows and models
        bases = content.monster_bases(npc_rows=True)
        originals =[o for o in source.objects if o["class"] in build.project.monster_classes and o["name"] in bases
                     and o["index"] not in self.exclude_sources]
        swim = dungeon_build.water.swimming(build.project)
        ocean_y = self.layout.ocean_y if self.layout is not None else None
        # In a swimmable sea MM9's sea creatures (the water spores) float where MM9 put them, under the surface
        swimmers = [o for o in originals if swim and ocean_y is not None and o["properties"]["Pos"][1] < ocean_y]
        # >>> swimmers: MM9's AISwimFly classes over the sea count too (Isle of Ashes' Sea Monster treads water with
        # its centre over the surface); swimmer_foot then puts its body box under the surface
        for o in originals:
            pos = o["properties"]["Pos"]
            if swim and ocean_y is not None and o not in swimmers and o["class"] in SWIMMER_CLASSES:
                bed = content.floor_at(pos[0], pos[2], pos[1])
                if bed is None or bed < ocean_y:
                    swimmers.append(o)
        # <<< swimmers
        floating = [o["name"] for o in originals if o not in swimmers
                    and content.floor_at(o["properties"]["Pos"][0], o["properties"]["Pos"][2],
                                         o["properties"]["Pos"][1]) is None]
        originals = [o for o in originals if o["name"] not in floating]
        build.stats["actors_without_floor"] = floating
        out, outside, moved = [], [], {}
        for o in originals:
            swimmer = o in swimmers
            if swimmer:
                # >>> swimmers (2026-11-04, mm9_jelly/seamon_claude): one in the far sea moves to the nearest point of
                # the near box's water (inset NEAR_SEA_INSET), so MM9's sea keeps its population
                o, shift = self.swimmer_into_near_box(o)
                if shift:
                    moved[o["name"]] = shift
                # <<< swimmers
            if swimmer and content.floor_at(o["properties"]["Pos"][0], o["properties"]["Pos"][2],
                                            o["properties"]["Pos"][1]) is None:
                outside.append(o["name"])       # no seabed under it even inside the near box
                continue
            actor = content.actor(o, bases[o["name"]], sector_of_room)
            if swimmer:
                actor["position"]["z"] = self.swimmer_foot(build, o, actor)
            out.append(actor)
        build.stats["actors_in_water"] = len(swimmers) - len(outside)
        build.stats["actors_in_far_sea"] = outside
        build.stats["actors_moved_into_near_sea_lt"] = moved
        target = int(self.settings(build).get("test_population", 0))
        walls = _barrier_walls(build.polygons)
        rejected = {"sea": 0, "barrier": 0}
        copy = 0
        while len(out) < target and originals:
            o = originals[copy % len(originals)]
            ring = copy // len(originals)
            placed = None
            for attempt in range(12):
                angle = (copy * 2.399 + attempt * 0.52) % (2 * math.pi)
                distance = (400 + 200 * ((ring + attempt) % 5)) / SCALE
                x = o["properties"]["Pos"][0] + math.cos(angle) * distance
                z = o["properties"]["Pos"][2] + math.sin(angle) * distance
                floor, polygon = _floor_under(content, x, z, o["properties"]["Pos"][1] + 400)
                if floor is None:
                    continue
                # Not in the sea, and not beyond one of MM9's monster barriers from the original (a bridge's side
                # beam, the far side of a ledge): it would walk off or stand where its kind cannot be
                if polygon.model == self.layout.ocean_model:
                    rejected["sea"] += 1
                    continue
                start = o["properties"]["Pos"]
                if _crosses_wall(walls, (start[0], start[2]), (x, z), min(start[1], floor), max(start[1], floor) + 40):
                    rejected["barrier"] += 1
                    continue
                clone = dict(o, name=f"{o['name']}_copy{copy}",
                             properties=dict(o["properties"], Pos=[x, floor + 4, z]))
                placed = content.actor(clone, bases[o["name"]], sector_of_room)
                break
            copy += 1
            if placed is not None:
                out.append(placed)
            if copy > target * 4:
                break
        build.stats["actor_copies_rejected"] = rejected
        build.stats["actors_mm9"] = len(originals)
        out += self.npcs(build, sector_of_room)
        build.stats["actors_total"] = len(out)
        return out

    @staticmethod
    def script_rude_id(properties: dict) -> int:
        """A person's dialogue id from its script when its object has none (no `DoRude 1`, or one that names no id):
        DoRude.scr's first parameter (Lindisfarne's Monk0), else the script's own `DoRude <id>` (NPC132.scr, the
        hag on Guberland; StonesPlayer.scr, the stones player); 0 for none."""
        import re
        script = str(properties.get("ScriptName") or "").replace("\\", "/").split("/")[-1]
        if not script:
            return 0
        if script.lower() == "dorude.scr":
            words = str(properties.get("ScriptParams") or "").split()
            return int(words[0]) if words and words[0].isdigit() else 0
        path = next((f for f in SCRIPTS_DIR.iterdir() if f.name.lower() == script.lower()), None) \
            if SCRIPTS_DIR.is_dir() else None
        if path is None:
            return 0
        match = re.search(r"^\s*DoRude\s+(\d+)\s*$", path.read_text(errors="replace"), re.MULTILINE | re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def npcs(self, build, sector_of_room: dict) -> list[dict]:
        """The region's people (REGIONS_FINISH.md step 1): every DAT object with `DoRude 1` whose class is not one of
        the map's monster classes (and not CacheOnly, nor placed by the map itself) as a friendly, immobile actor with
        its RUDE dialogue, as the cities place their townsfolk (mm9r_thjorgardcity/convert.py actors): the old
        import's record (row, name, RUDE id) where it placed one, else a stand-in peasant row with the DAT object's
        RUDE id and the name it has in NPCNAME.rude; MM9's body (the model's extents x Scale). One without a floor under
        it is left out (listed). overrides.yml `outdoor.people` ({DAT name: shown name}) adds people without a dialogue
        whose script the map Lua carries (a click runs their 53000 + object event: Thjorgard's arm wrestler); a value
        {name, monster_id} also gives one whose class has no MM9 row the row of its model (Guberland's AtliGuard,
        WealthyTownGuard1 on guard.abc: the Guard row 9111, as Invent-a-Storca's guards)."""
        from dungeon.bodies import mm9_bodies
        from mm9_ai_placement import townsperson_walks
        from mm9_monster_bodies import native_body
        from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names
        content, source = build.content, build.source
        old_path = ROOT / f"assets_editor_dev/worlds/mm9/maps/{build.project.stem}.scene.yml"
        old = {}
        if old_path.exists():
            old = {a["mm9_source_object_index"]: a for a in
                   yaml.load(old_path.read_text(), Loader=yaml.CSafeLoader)["initial_state"].get("actors", [])
                   if "mm9_source_object_index" in a}
        names = read_mm9_npc_names(ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude")
        bodies = mm9_bodies()
        people = self.settings(build).get("people") or {}
        out, floating = [], []
        self.npc_actor, self.npc_rude = {}, {}
        for o in source.objects:
            p = o["properties"]
            if (o["class"] in build.project.monster_classes or o["index"] in self.exclude_sources
                    or float(p.get("CacheOnly", 0) or 0)):
                continue
            # MM9's own id (DoRude 1 with NPCnnn.scr, its greeting or NPCNbr), else its script's
            does_rude = bool(float(p.get("DoRude", 0) or 0))
            own_rude = mm9_npc_rude_id({key: p.get(key) for key in ("DoRude", "ScriptName", "GreetingSound",
                                                                      "NPCNbr")}) if does_rude else 0
            script_rude = 0 if own_rude else self.script_rude_id(p)
            if not does_rude and not script_rude and o["name"] not in people:
                continue
            if content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 24) is None:
                floating.append(o["name"])
                continue
            record = old.get(o["index"])
            if record is not None:
                rude = int(record.get("mm9_rude_id") or 0) or script_rude
                base = {key: record[key] for key in ("name", "attributes", "hp", "hostility_type", "monster_info_id",
                                                     "monster_id", "radius", "height", "move_speed")}
            else:
                rude = own_rude or script_rude
                base = {"name": names.get(rude, o["name"]), "attributes": 0, "hp": 20, "hostility_type": 0,
                        "monster_info_id": NPC_STAND_IN_ROW, "monster_id": NPC_STAND_IN_ROW, "radius": 43,
                        "height": 120, "move_speed": 0}
            if o["name"] in people:
                person = people[o["name"]]
                if isinstance(person, dict):
                    base["name"] = person["name"]
                    if "monster_id" in person:
                        base["monster_info_id"] = base["monster_id"] = int(person["monster_id"])
                else:
                    base["name"] = person
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                base["height"], base["radius"] = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
            actor = content.actor(o, base, sector_of_room, group=NPC_GROUP, friendly=True,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = not townsperson_walks(actor.get("mm9_ai") or {})
            if base["monster_id"] not in NPC_PEASANT_ROWS:
                actor["ally"] = NPC_PEACEFUL_ALLY       # a non-peasant picture row: a peasant family's relations
            self.npc_actor[o["name"]], self.npc_rude[o["name"]] = actor["actor_index"], rude
            out.append(actor)
        out += self.added_people(build, sector_of_room)
        build.stats["npcs"] = len(out)
        build.stats["npcs_without_floor"] = floating
        return out

    def added_people(self, build, sector_of_room: dict) -> list[dict]:
        """People MM9 does not have (overrides.yml `outdoor.added_people`; Yorwick's spellbook seller, the user,
        2026-11-09): each {name, rude, row, filename, like, at: [x, y, z] native, yaw: degrees} is a friendly,
        immobile townsperson with its RUDE dialogue (a world-owned NPC<rude>.rude) on the MM9 townsfolk row `row`
        (mm9_npc_actor_rows.tsv: its engine row 9000 + row and 3D model) with the body of model `filename`, placed
        as the DAT person `like` (its AI properties and script) without its greeting. It has no DAT object, so no
        mm9_source_object_index (no RUDE exit callback)."""
        from mm9_monster_bodies import native_body
        from dungeon.bodies import mm9_bodies
        from dungeon.content import mm9_npc_actor_rows
        out = []
        for entry in self.settings(build).get("added_people") or []:
            like = build.source.by_name[entry["like"].lower()]
            x, y, z = entry["at"]
            pos = [float(v) for v in build.project.lt_from_native((x, y, z))]
            properties = dict(like["properties"], Name=entry["name"], Pos=pos, Filename=entry["filename"],
                              ScriptParams="", GreetingSound="")
            row = int(entry["row"])
            if row not in mm9_npc_actor_rows():
                raise SystemExit(f"added person {entry['name']}: row {row} is no MM9 townsfolk row with a model")
            person = {"index": None, "class": like["class"], "name": entry["name"], "properties": properties}
            base = {"name": entry["name"], "attributes": 0, "hp": 20, "hostility_type": 0,
                    "monster_info_id": 9000 + row, "monster_id": 9000 + row, "radius": 43, "height": 120,
                    "move_speed": 0}
            extents = mm9_bodies().model_extents(entry["filename"])
            if extents is not None:
                base["height"], base["radius"] = native_body(extents[1], 1.0)
            actor = build.content.actor(person, base, sector_of_room, group=NPC_GROUP, friendly=True,
                                        floor_query_lt=pos[1] + 24)
            actor["initial_yaw_units"] = int(round(float(entry["yaw"]) % 360 / 360 * 2048)) % 2048
            actor["mm9_rude_id"] = int(entry["rude"])
            actor["immobile"] = True
            actor["mm9_civilian"] = True     # as a DAT townsperson switched to its own MM9 row (content.actor)
            out.append(actor)
        return out

    # >>> swimmers (2026-11-04; mm9_jelly/seamon_claude READMEs, devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md)
    def swimmer_into_near_box(self, o: dict) -> tuple[dict, int]:
        """A swimmer past the near box (the far sea: no seabed, no water volume) moved to the nearest point inside it,
        NEAR_SEA_INSET from its walls; (the object, the move in LT, 0 when inside)."""
        low, high = self.layout.near_box
        pos = o["properties"]["Pos"]
        x = float(np.clip(pos[0], low[0] + NEAR_SEA_INSET, high[0] - NEAR_SEA_INSET))
        z = float(np.clip(pos[2], low[2] + NEAR_SEA_INSET, high[2] - NEAR_SEA_INSET))
        shift = int(round(math.hypot(x - pos[0], z - pos[2])))
        if not shift:
            return o, 0
        return dict(o, properties=dict(o["properties"], Pos=[x, pos[1], z])), shift

    def swimmer_foot(self, build, o: dict, actor: dict) -> int:
        """A swimmer's foot (the actor's z): MM9's position is the centre of its body box (LithTech centres an
        object's Dims on its position; Gravity 0, MoveToFloor 0), so the box's centre goes there, then down until the
        box is under the sea surface (Isle of Ashes' Sea Monster sits 33 LT over it, treading water) and up to clear
        the seabed. The models carry MM9's origin at the box centre (floor_fix.py --swim)."""
        pos = o["properties"]["Pos"]
        native = build.project.native
        height = float(actor["height"])
        foot = float(native(np.array(pos, float))[2]) - height / 2
        surface = float(native(np.array([pos[0], self.layout.ocean_y, pos[2]], float))[2])
        foot = min(foot, surface - height - 8.0)
        bed = build.content.floor_at(pos[0], pos[2], pos[1])
        if bed is not None:
            foot = max(foot, float(native(np.array([pos[0], bed, pos[2]], float))[2]) + 1.0)
        return int(round(foot))
    # <<< swimmers

    def scene(self, build, scene: dict) -> None:
        super().scene(build, scene)
        # Seen as an outdoor map is: its view distance, the sky's haze and the normal sea (devdocs/INDOOR_OPEN_SKY.md
        # "Outdoor view"; the full view distance, where the cities take half). `outdoor: {outdoor_view: false}` keeps
        # the scene's own view.
        if "sky" in scene and self.settings(build).get("outdoor_view", True):
            scene["sky"]["view"] = "outdoor"
        # The outdoor weather over the open sky (devdocs/INDOOR_OPEN_SKY.md "Weather"): rain by default, `outdoor:
        # {weather: snow | rain_and_snow | none}`. With weather the sky follows it, not a fixed preset, and MM9's
        # placed thunder gives way to the storms' (city.hooks.apply_weather).
        apply_weather(scene, self.settings(build).get("weather", "rain"))
        liquids.apply(build, scene)
        self.deep_sea(build, scene)
        # Again after the liquids (CityHooks.scene ran before them): their faces' textures count too.
        footsteps.apply(build, scene)
        # The party climbs no slope a monster cannot (MM9's cliffs; MM6-MM8's party climbs any)
        scene["party_movement"] = {"steep_slopes": "block"}
        # Open country is no dungeon room: a monster that notices the party rouses none of its neighbours
        # (re_mm8/INDOOR_EXPLORATION_AND_ACTIVATION.md, "OpenYAMM detection by sight, hearing and neighbours")
        scene["actor_detection"] = {"wakes": "none"}
        # Static lights by distance on both sides (devdocs/INDOOR_OPEN_SKY.md "Static lights"), as MM9 lit its regions'
        # vertex-lit polygons (terrain, cliffs, sea; MM9_LIGHTING_GLOBAL_MODEL.md 1.2: no N.L). The cities' front-only
        # rule cut the terrain: a light over a cliff's top lit the facets tilted toward it and none of their neighbours,
        # light and dark triangles across the face (Isle of Ashes, user play-test 2026-11-06). The structures here
        # take MM9's lightmaps, which no static vertex light touches.
        scene["static_lights"] = {"sides": "both"}


def _floor_under(content, x, z, y_from):
    """The highest floor under (x, z) below y_from and its polygon (content.floor_at with the polygon)."""
    near = np.nonzero((content.floor_low[:, 0] <= x) & (x <= content.floor_high[:, 0])
                      & (content.floor_low[:, 1] <= z) & (z <= content.floor_high[:, 1]))[0]
    best, found = None, None
    for i in near:
        height = floor_below([content.floors[i]], (x, y_from, z))
        if height is not None and (best is None or height > best):
            best, found = height, content.floors[i]
    return best, found


def _barrier_walls(polygons: list) -> list:
    """The upright faces of the monster barriers (role "barrier", dungeon/build.py) as plan edges (x, z) with their
    height range (LT)."""
    walls = []
    for polygon in polygons:
        if polygon.role != "barrier" or abs(polygon.normal[1]) > 0.5:
            continue
        ring = polygon.points[:, [0, 2]]
        walls.append((ring, np.roll(ring, -1, axis=0), polygon.points[:, 1].min(), polygon.points[:, 1].max()))
    return walls


def _crosses_wall(walls: list, a, b, y_low: float, y_high: float) -> bool:
    """Whether the plan segment a-b crosses an edge of a barrier wall that overlaps [y_low, y_high]."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    for p, q, low, high in walls:
        if high < y_low or low > y_high:
            continue
        e = q - p
        denom = d[0] * e[:, 1] - d[1] * e[:, 0]
        ok = np.abs(denom) > 1e-9
        ap = p - a
        t = np.where(ok, (ap[:, 0] * e[:, 1] - ap[:, 1] * e[:, 0]) / np.where(ok, denom, 1), -1)
        u = np.where(ok, (ap[:, 0] * d[1] - ap[:, 1] * d[0]) / np.where(ok, denom, 1), -1)
        if np.any(ok & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)):
            return True
    return False


def bind_indoor_decorations(props_path: Path) -> list:
    """A BLV draws a decoration's 3D model from the indoor manifests (engine/models/indoor_decorations.yml and the
    world's), which lack the MM9 outdoor props (the MM8 pines tree29/tree30, the stone debris, the well...): their
    outdoor bindings are appended to the review root's worlds/mm9/models/indoor_decorations.yml."""
    names = {entry["decoration"].lower() for entry in json.loads(Path(props_path).read_text())}
    indoor_path = Path("worlds/mm9/models/indoor_decorations.yml")
    marker = "  # --- MM9 outdoor BLVs: outdoor props (mm9r_common/outdoor_blv.py) ---"
    # Rebuilt from the current assets_dev manifest each time (rows added there since, the stat barrels and the
    # regions' vegetation, reach the root), keeping the outdoor bindings earlier maps appended.
    source_text = (review_root.SOURCE / indoor_path).read_text()
    mirror_text = review_root.mirror_path(indoor_path).read_text()
    appended = []
    for segment in mirror_text.split(marker + "\n")[1:]:
        appended += yaml.safe_load(segment) or []
    bound = {d["name"].lower() for d in yaml.safe_load(source_text)["decorations"]}
    bound |= {d["name"].lower() for d in yaml.safe_load(
        review_root.mirror_path("engine/models/indoor_decorations.yml").read_text())["decorations"]}
    outdoor = {}
    for relative in ("engine/models/decorations.yml", "worlds/mm9/models/decorations.yml"):
        for entry in yaml.safe_load(review_root.mirror_path(relative).read_text())["decorations"]:
            outdoor.setdefault(entry["name"].lower(), entry)
    keep = {entry["name"].lower(): entry for entry in appended if entry["name"].lower() not in bound}
    missing = sorted(name for name in names - bound - set(keep) if name in outdoor)
    keep.update({name: outdoor[name] for name in missing})
    text = source_text
    if keep:
        block = yaml.safe_dump([keep[name] for name in sorted(keep)], sort_keys=False)
        text = source_text.rstrip("\n") + "\n" + marker + "\n"
        text += "".join("  " + line + "\n" for line in block.splitlines())
    if text != mirror_text:
        review_root.install(indoor_path, text.encode())
    return missing


def rewrite_transport(project) -> int:
    """The review root's `transport_routes.txt` rows that sail to the map name `<stem>.odm`, which the BLV install
    removes (the game then refuses the whole table): they name `<stem>.blv` and arrive at their start point as built
    (the scene's party start of that index in overrides.yml `starts`), under the review tables lock."""
    from dungeon import tables
    relative = "worlds/mm9/data_tables/transport_routes.txt"
    scene = yaml.safe_load(review_root.mirror_path(f"worlds/mm9/maps/{project.stem}.scene.yml").read_text())
    starts = {name.lower(): start for name, start in zip(project.starts, sorted(
        scene["party_start_points"], key=lambda s: s["start_index"]))}
    map_id = f"world.mm9.map.{project.stem}"
    changed = 0
    with tables.locked("review_tables.lock"):
        lines = review_root.mirror_path(relative).read_bytes().decode("latin-1").split("\n")
        header = lines[0].rstrip("\r").split("\t")
        col = {name: k for k, name in enumerate(header)}
        for k, line in enumerate(lines[1:], start=1):
            ending = "\r" if line.endswith("\r") else ""
            cells = line.rstrip("\r").split("\t")
            if len(cells) <= col["FacingYawUnits"] or cells[col["DestinationMap"]] != map_id:
                continue
            start = starts.get(cells[col["DestinationStartPoint"]].lower())
            if start is None:
                raise SystemExit(f"{cells[0]}: start {cells[col['DestinationStartPoint']]} is not in overrides.yml starts")
            x, y, z = start["position"]
            facing = float(start["direction_degrees"])
            cells[col["DestinationMapFile"]] = f"{project.stem}.blv"
            cells[col["ArrivalX"]], cells[col["ArrivalY"]], cells[col["ArrivalZ"]] = str(x), str(y), str(z)
            cells[col["FacingDegrees"]] = f"{facing:g}"
            cells[col["FacingYawUnits"]] = str(round(facing / 360 * 2048) % 2048)
            lines[k] = "\t".join(cells) + ending
            changed += 1
        if changed:
            review_root.install(relative, "\n".join(lines).encode("latin-1"))
    return changed


def convert_region(project_dir: Path, generator: str) -> int:
    """A region project's whole convert.py (devdocs/mm9_rework/OUTDOOR_BLV_ALL.md): build, compile and install the map
    with the shared hooks, rewrite the boat arrivals, bind the props' indoor models (when it has props) and install the
    terrain materials (when overrides.yml has `terrain`). The caller redirects review_root first."""
    import dungeon
    import terrain_blend

    hooks = type(f"Hooks_{generator}", (OutdoorBlvHooks,), {"generator": generator})(project_dir)
    code = dungeon.main(project_dir, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        project = dungeon.source.Project.load(project_dir)
        print(f"boat arrivals rewritten: {rewrite_transport(project)}")
        if (project.work / "props.json").exists():
            print(f"indoor decoration bindings added: {bind_indoor_decorations(project.work / 'props.json')}")
        print(terrain_blend.install(project_dir))
    return code
