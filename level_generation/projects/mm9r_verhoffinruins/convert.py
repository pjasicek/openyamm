#!/usr/bin/env python3
"""
Verhoffin Ruins, MM9 rework: MM9's VERHOFFINRUINS.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_verhoffinruins/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_verhoffinruins/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules; this file adds the population (props.json from
../../props/mm9_verhoffinruins_claude, the pentagram's flames, the spikes of the electrified pit, 30 monsters), the
water (the crevasse's and the pit's wading surfaces, the trap room's rising water) and MM9's scripted objects as native
Lua, each citing its .scr (README.md, "Scripted objects"):
- the pentagram puzzle (PentagramPuzzle.scr): five points in the order of the flames' colours (letter 485) open the
  torture chamber; its door's shooters (Shooter objects, the leaves' OpenTriggers);
- the capstone and the writ (Capstone.scr, placeCapstone.scr, Writ.scr), the fake book (fakebook.scr), the key of
  Door5 (givetake.scr, DoorLock.scr), the diary scraps (BookLetter.scr 484, 485);
- the water trap (DrainWater.scr and the nozzles', buttons' and triggers' wiring), the saw blade, the paddle over the
  electrified pit, the falling door, the bolt on PrisonDoor2 (DestructableBrush12), the busts that drop from the
  ceiling (KingKong.scr), the PerceptionBrushes.

MM9's Trigger volumes are boxes polled four times a second (as the Chasm of the Dead's): they fire on any part of the
party in their box, as MM9's do.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
from dungeon.wall_splits import split_at_walls  # noqa: E402
import liquids  # noqa: E402
import review_root  # noqa: E402
from dungeon import lua, tables, water  # noqa: E402
from dungeon.objects import perception_light_lua  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.destructibles import CLICK_EVENT_BASE  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon import rooms as rooms_module  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
ORIGINAL_SEPARATING_PLANE = rooms_module.separating_plane
import dungeon.build as build_module  # noqa: E402
ORIGINAL_ASSIGN_FACES = build_module.assign_faces
from dungeon.source import ROOT, SCALE, yaw_degrees  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"

# --- Water ---------------------------------------------------------------------------------------------------------
# overrides.yml `map: {swim: true}` (2026-11-02, devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md): MM9's water as
# volumes the party swims and dives in (the scene's `water_volumes`, ../mm9r_common/dungeon/water.py), its surfaces
# non-solid over the beds. Without it the crevasse and the pit are wading floors the party walks on (Beethoven's route).
CREVASSE_VOLUMES = ("BlueWater0", "BlueWater1")    # the crevasse's water volumes: their top faces are its surface
CREVASSE_SURFACE_MODEL = "WorldObject0"            # MM9's one Ocean3 quad over the whole map: its texture and mapping
PIT_SURFACE_MODEL = "WaterSurface"                 # the electrified pit's surface (water125_0000)
PIT_STEP = {"x": (-2368.0, -2336.0), "z": (-1536.0, -1376.0), "y": -145.0}   # an invisible ledge out of the pit (LT)
TRAP_MODEL = "WaterTrap"                           # the trap room's water volume (DrainWater.scr moves it)
TRAP_TEXTURE = "water:pool"                        # overrides.yml textures: MM9's Water115.spr, first frame
TRAP_FULL_LT = -30.0                               # the surface when full (MM9 floods the room to its ceiling at 0)
TRAP_OPACITY = 0.7                                 # WaterTrap SurfaceAlpha
SWIM_VOLUMES = (*CREVASSE_VOLUMES, "ElectricWater1", TRAP_MODEL)   # the volumes written with `swim: true`
CREVASSE_SPR = "sprites\\water\\ocean3.spr"
PERCEPTION_TEXTURES = ("sprites\\perception.spr", "sprites\\perception2.spr")
PERCEPTION_OPACITY = 0.5                           # the brushes' Alpha
UNTOUCHABLE, INVISIBLE_FACE = 0x20000000, 0x00002000
SPLIT_PURITY, SPLIT_BAND = 0.92, 20.0              # looser_separating_plane
MINOR_SPLIT = 0.04                                 # presplit_assign_faces
SKY_TEXELS_PER_LT = 0.2                            # the core's sky face: sky04 stretched (the Chasm's)
FRAME_FLAGS = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}

# --- Events, timers, cogs, groups ------------------------------------------------------------------------------------
EV_LOAD = 1
EV_LOCKED, EV_DD9, EV_PRISON14, EV_CELL8 = 200, 201, 202, 203
EV_TORTURE, EV_PRISON2, EV_BOLT, EV_DOOR5, EV_FALLING = 204, 205, 206, 207, 208
EV_BOLT_HIT = 209                                  # the bolt damaged (its DamageTrigger: PerceptionBrush0 off); EV_BOLT: broken
BOLT = "DestructableBrush12"
EV_NOZZLE = {f"WaterNozzle{k}": 210 + k for k in range(4)}
EV_DRAIN, EV_DUMMY_BUTTON = 214, 215
EV_BOOK, EV_WRIT, EV_BLOCK, EV_LETTER = 220, 222, 223, {"Prop2": 224, "Prop3": 225}
T_POLL, T_SAW_BACK, T_SAW_REARM, T_PADDLE_BACK, T_PADDLE_REARM, T_WATER, T_SHOOT, T_HINTS = (150, 151, 152, 153, 154,
                                                                                         155, 156, 157)
COG_BOOK, COG_CAPSTONE = 300, 303
COG_FIRE = 310                                     # PentaFire k+1: COG_FIRE + k
COG_HINT = 320                                     # PerceptionBrush hint k: COG_HINT + k
GROUP_BUSTS = {"BustTrigger0": 10, "BustTrigger1": 11}
BUSTS = {"BustTrigger0": ("BustZombie0", "BustZombie1", "BustZombie2"),      # the pocket over BreakOut1
         "BustTrigger1": ("BustWraith0", "BustWraith1")}                     # the pocket over BreakOut0
# each bust's ceiling slab (KingKong.scr p0, a DestructableBrush), the dust its DeathTrigger turns on, its broken event
SLABS = {"BustTrigger0": ("BreakOut1", "BreakOutDust1", 226), "BustTrigger1": ("BreakOut0", "BreakOutDust0", 227)}
PENTA_ORDER = ["TriggerPentagram1", "TriggerPentagram2", "TriggerPentagram3", "TriggerPentagram4", "TriggerPentagram5"]
PENTA_FIRES = {"PentaFire1": "red", "PentaFire2": "yellow", "PentaFire3": "blue", "PentaFire4": "green",
               "PentaFire5": "orange"}
TOUCH_TRIGGERS = ["Trigger0", "PaddleTrigger", "SawBladeTrigger1", "PentaCenter", *PENTA_ORDER, *GROUP_BUSTS]
PARTY_REACH = 32                                   # native: MM9's touch fires on any part of the party (radius ~15 LT)
DOOR_SHOOTERS = ("DoorShooter0", "DoorShooter1")   # FireBolt, DamageAmt 20, every 4 s while on
HINTS = ["PerceptionBrush0", "PerceptionBrush2", "PerceptionBrush3", "PerceptionLightWaterTrap"]
PERCEPTION_SKILL = 29                              # evt.CheckSkill's id: the party's best Perception value
# boxes round the bolt (its shared click: CLICK_EVENT_BASE + its DAT index, set where the hints are placed), the button
HINT_EVENTS = {"PerceptionLightWaterTrap": EV_DRAIN}

# Keys (QBits 90000 + key) and items (MM9.ItemIds), from the scripts.
KEY_CAPSTONE_QUEST, KEY_PLACED, KEY_WRIT = 98, 99, 100                      # Capstone.scr, placeCapstone.scr, Writ.scr
ITEM_CAPSTONE, ITEM_WRIT, EXP_PLACED, EXP_WRIT = 396, 392, 154000, 162000
KEY_BOOK, KEY_BOOK2, KEY_BOOK_DONE, ITEM_FAKE_BOOK = 281, 290, 282, 242      # fakebook.scr
ITEM_DOOR5_KEY = 559                                                        # givetake.scr "559", DoorLock.scr "559 1"
SAW_DAMAGE, PIT_DAMAGE, DROWN_DAMAGE, BOLT_DAMAGE = 40, 5, 10, 20
# DamageTriggerTarget/Message of the bust monsters: a hit turns on the dust Fire over the corridor (BreakOutDust0 "On")
DUST_ON_HIT = {"BustWraith0": "BreakOutDust0", "BustWraith1": "BreakOutDust0", "BustWraith2": "BreakOutDust0",
               "BustWraith3": "BreakOutDust0"}
DAMAGE_HOOK = 97                                   # monster damage hook (an id outside the map's events)

# MM9's bodies (ABC AnimBinding half extents x MONSTERS.txt Scale x 2.56): radius, height in native units.
BODIES = {"Zombie": (38, 179), "SkeletonWarrior": (38, 189), "SkeletonMaster": (38, 189), "Fright": (51, 154),
          "Terror": (51, 154), "Dread": (51, 154)}


def swimming(build) -> bool:
    """The shared water rule (dungeon/water.py `swimming`): MM9's water volumes, swum in (module constants, "Water")."""
    return water.swimming(build.project)


def as_float(value) -> float:
    """A DAT float stored in an int property (PerceptionValue 1091567616 = 9.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value)


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    import csv
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


def flat(points_xz, y: float, template: Polygon, texture: str, alias: dict, model: str, role: str) -> Polygon:
    """A horizontal face over a ring of (x, z) points at height y, front upward, with the template's texture mapping."""
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    mapping = template.mapping if template is not None else (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0]))
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture, mapping, 0x1081, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, mapping, 0x1081, model, role)
    polygon.notes.update(width=alias["width"], height=alias["height"])
    return polygon


def covers_lt(polygon: Polygon, point: tuple) -> bool:
    """Whether a horizontal polygon's footprint (LT x, z) contains the point (even-odd rule)."""
    x, z = point
    ring = polygon.points[:, [0, 2]]
    inside = False
    for (x1, z1), (x2, z2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            inside = not inside
    return inside


def looser_separating_plane(samples, found, counts, corners, every_candidate=False):
    """rooms.separating_plane, robust to the samples under a thin wall (map-local, patched in by
    VerhoffinRuins.edit_polygons): the ceilings and floors run over rows of cells here and the cell walls are about a
    voxel thick, so the samples along each wall go to either cell and a row of cells never reached 88 % purity. Here a
    split goes between one room's samples and the rest's (their 15th/85th percentiles) and its purity is counted
    outside a band of SPLIT_BAND LT round it; the original's answer is taken first when it has one."""
    found_plane = ORIGINAL_SEPARATING_PLANE(samples, found, counts, corners, every_candidate)
    if found_plane is not None:
        return found_plane
    valid = found > 0
    points, rooms = samples[valid], found[valid]
    best = None
    for main in counts:
        inside = rooms == main
        if inside.all() or not inside.any():
            continue
        for axis in rooms_module.SPLIT_AXES:
            values = points @ axis
            v_main, v_other = values[inside], values[~inside]
            for main_low in (True, False):
                if main_low:
                    split = (np.percentile(v_main, 85) + np.percentile(v_other, 15)) / 2
                else:
                    split = (np.percentile(v_main, 15) + np.percentile(v_other, 85)) / 2
                extent = corners @ axis
                if min(split - extent.min(), extent.max() - split) < 12.0:
                    continue
                keep = np.abs(values - split) > SPLIT_BAND
                if keep.sum() < 0.5 * len(values):
                    continue
                below = values < split
                right = np.where(inside, below == main_low, below != main_low)
                purity = right[keep].mean()
                if purity >= SPLIT_PURITY and (best is None or purity > best[0]):
                    best = (purity, axis, float(split))
    if best is not None:
        return best[1], best[2]
    # A grid of cells (two rows of two): no one room parts from the rest, but a wall line parts the rooms in two
    # groups. Try the planes between the rooms' medians; every room with a tenth of the samples must keep 90 % of its
    # samples (outside the band) on one side.
    for axis in rooms_module.SPLIT_AXES:
        values = points @ axis
        medians = sorted(float(np.median(values[rooms == room])) for room in counts)
        extent = corners @ axis
        for a, b in zip(medians, medians[1:]):
            if b - a < 2 * SPLIT_BAND:
                continue
            split = (a + b) / 2
            if min(split - extent.min(), extent.max() - split) < 12.0:
                continue
            keep = np.abs(values - split) > SPLIT_BAND
            clean, sides = True, set()
            for room in counts:
                mine = (rooms == room) & keep
                if mine.sum() < 0.1 * keep.sum():
                    continue
                low = (values[mine] < split).mean()
                if 0.1 < low < 0.9:
                    clean = False
                    break
                sides.add(low >= 0.9)
            if clean and len(sides) == 2:
                return axis, float(split)
    return None


def presplit_assign_faces(rooms, polygons, portals, stats, log, **settings):
    """rooms.assign_faces after a map-local pre-pass: a polygon whose second room holds 4-15 % of its samples (under
    the shared pass's 15 % threshold, so it would go whole to the first room) is split at the plane between the rooms
    when one is found. The NE hall's north wall runs on behind the east room next to it (x 336-1472, the room's part 13 %
    of the samples): whole, the east room had no north wall."""
    from collections import Counter as _Counter
    out, queue = [], list(polygons)
    while queue:
        polygon = queue.pop()
        if polygon.role != "glass":
            found, samples = rooms.front(polygon, with_samples=True)
            counts = _Counter(int(v) for v in found if v)
            if len(counts) > 1:
                total, second = sum(counts.values()), counts.most_common(2)[1][1]
                if max(3, MINOR_SPLIT * total) <= second < 0.15 * total:
                    plane = looser_separating_plane(samples, found, counts, polygon.points)
                    if plane is not None:
                        parts = [part for part in rooms_module.clip(polygon, plane[0], plane[1], "minor")
                                 if part is not None]
                        if len(parts) == 2:
                            stats["face_presplits_minor"] += 1
                            queue += parts
                            continue
        out.append(polygon)
    return ORIGINAL_ASSIGN_FACES(rooms, out, portals, stats, log, **settings)


# A point (LT x, z) in the water-trap room south of its own floor: the floor under it is cut at the walls standing on it
# (edit_polygons). Cutting every big floor so added 14-25 % faces to the hall, the map's costliest sector
# (devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md), for small sills elsewhere.
TRAP_ROOM_FLOOR_POINT_LT = (232.0, -875.0)


class VerhoffinRuins(dungeon.Hooks):
    generator = "mm9r_verhoffinruins"
    mover_events = {
        "DD10": (EV_LOCKED, "click"), "TortureSide6": (EV_LOCKED, "click"), "TortureSide7": (EV_LOCKED, "click"),
        "WaterRoomButton1": (EV_DUMMY_BUTTON, "click"), "DD9": (EV_DD9, "click"), "PrisonDoor14": (EV_PRISON14, "click"),
        "Cell8": (EV_CELL8, "click"), "TortureDoor": (EV_TORTURE, "click"), "PrisonDoor2": (EV_PRISON2, "click"),
        "Door5": (EV_DOOR5, "click"), "FallingDoor": (EV_FALLING, "click"),
        **{name: (event, "click") for name, event in EV_NOZZLE.items()}, "WaterRoomButton2": (EV_DRAIN, "click"),
    }

    def destructible_events(self, build) -> dict:
        """The bolt on PrisonDoor2 (dungeon/destructibles.py `break`): its death and its damage. The busts' ceiling
        slabs: their death (the pocket's monsters fall)."""
        return {BOLT: (EV_BOLT, EV_BOLT_HIT), **{slab: (event, 0) for slab, _, event in SLABS.values()}}

    # --- geometry -----------------------------------------------------------------------------------------------
    def extra_seeds(self, build) -> list:
        """The trap room's water: MM9's WaterTrap volume (a box under the floor that DrainWater.scr raises to the
        ceiling) as its top face only, built at its full height (the BLV's stored pose, so the bake lights it in the
        room) and starting lowered under the floor (overrides.yml: a slide mover that opens downward)."""
        source = build.source
        polygons = source.polygons
        if getattr(source, "_verhoffin_wrapped", False):
            return super().extra_seeds(build)
        alias = source.aliases[TRAP_TEXTURE]

        def trap_top(model_name):
            found = polygons(model_name)
            if model_name != TRAP_MODEL:
                return found
            top = max(p.points[:, 1].max() for p in found)
            out = []
            for p in found:
                if p.normal[1] > 0.99 and abs(p.points[:, 1].mean() - top) < 0.5:
                    lift = np.array([0.0, TRAP_FULL_LT - top, 0.0])
                    face = Polygon(p.points + lift, [tuple(np.round(v, 1)) for v in p.points + lift], TRAP_TEXTURE,
                                   (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), p.flags, p.model, "static")
                    face.notes.update(width=alias["width"], height=alias["height"])
                    out.append(face)
            if not out:
                raise SystemExit(f"{TRAP_MODEL}: no top face")
            self.trap_lowered_lt = float(TRAP_FULL_LT - top)
            return out

        source.polygons = trap_top
        source._verhoffin_wrapped = True
        return super().extra_seeds(build)

    def edit_polygons(self, build, polygons: list) -> list:
        """The crevasse's water (the top faces of BlueWater0/1 with WorldObject0's Ocean3 texture) and the
        electrified pit's surface: wading floors, or with `swim: true` non-solid surfaces at the volumes' tops; and an
        invisible ledge out of the pit (kept with swimming: the pit's rim is 82 over its water, beyond the surface
        jump's 59)."""
        rooms_module.separating_plane = looser_separating_plane
        build_module.assign_faces = presplit_assign_faces
        source = build.source
        template = next(p for p in source.polygons(CREVASSE_SURFACE_MODEL) if "ocean" in p.texture.lower())
        texture = template.texture
        alias = source.aliases[texture.lower()]
        swim = swimming(build)
        role = "nonsolid" if swim else "static"
        out = []
        for polygon in polygons:
            if polygon.model == PIT_SURFACE_MODEL and polygon.role == "nonsolid":
                polygon.role = role
            if "skymarker" in polygon.texture.lower():      # one sky04 tile about 2 500 LT wide (MM9: a sky box)
                origin = np.asarray(polygon.mapping[0], float)
                polygon.mapping = (origin, np.array([SKY_TEXELS_PER_LT, 0.0, 0.0]),
                                   np.array([0.0, 0.0, SKY_TEXELS_PER_LT]))
            out.append(polygon)
        self.crevasse_faces = 0
        for model in CREVASSE_VOLUMES:
            found = source.polygons(model)
            top = max(p.points[:, 1].max() for p in found)
            for p in found:
                if p.normal[1] > 0.99 and abs(p.points[:, 1].mean() - top) < 0.5:
                    face = flat(p.points[:, [0, 2]], top if swim else top + 1.0, template, texture, alias,
                                CREVASSE_SURFACE_MODEL, role)
                    out.append(face)
                    self.crevasse_faces += 1
        step_alias = next(iter(source.aliases.values()))
        (x0, x1), (z0, z1) = PIT_STEP["x"], PIT_STEP["z"]
        out.append(flat([(x0, z0), (x0, z1), (x1, z1), (x1, z0)], PIT_STEP["y"], None, step_alias["source_texture"],
                        step_alias, "PitStep", "invisible"))
        # The hall's floor runs on under the water-trap room's walls into the room (one 16-gon, x -256..700,
        # z -1328..-832 LT), and the two rooms share no portal for split_minor_rooms to cut at: a party in the trap
        # room south of its own floor stood on the hall's floor, was put in the hall's sector and saw the room black
        # (play-test 2026-11-07 at native (596, -2241)). That floor is cut at the walls standing on it.
        out, build.stats["floor_wall_splits"] = split_at_walls(
            out, kinds=("floor",), select=lambda polygon: covers_lt(polygon, TRAP_ROOM_FLOOR_POINT_LT))
        return out

    # --- population ---------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        # the key of Door5 and the writ are world items (dungeon/pickups.py); the writ's pickup runs EV_WRIT
        events = {"Book": EV_BOOK, "writ": EV_WRIT, "HeadsmanBlock1": EV_BLOCK, **EV_LETTER}
        cogs = {"Book": COG_BOOK, "Capstone": COG_CAPSTONE}
        if PROPS.exists():
            content.props(PROPS, events=events, cogs=cogs)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        # The electrified pit's spikes (PropDamager Spikes5-8, 20 a second): on the pit floor under the water.
        for k in range(5, 9):
            name = f"Spikes{k}"
            p = source.properties(name)
            floor = content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 4)
            floor = -288.0 if floor is None else floor
            content.entity(name, "mm9_spikepit", project.native([p["Pos"][0], floor, p["Pos"][2]]),
                           yaw_degrees(p.get("Rotation")))
        # The pentagram's flames (PentaFire1-5): off until the puzzle starts.
        for k, (name, colour) in enumerate(PENTA_FIRES.items()):
            p = source.properties(name)
            floor = content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 8)
            content.entity(name, f"mm9_pentafire_{colour}", project.native([p["Pos"][0], floor, p["Pos"][2]]), 0,
                           primary=COG_FIRE + k)
        self.place_perception_hints(build)
        self.boxes = {name: self.box(build, name) for name in TOUCH_TRIGGERS}
        self.boxes["SawDamage"] = self.model_box(build, "saw damage")
        self.boxes["PitDamage"] = self.model_box(build, "ElectricDamager1")
        self.boxes["TrapRoom"] = self.model_box(build, TRAP_MODEL, top_lt=0.0)
        self.boxes["TortureChamber"] = self.lt_box(build, (-2900, -128, -1720), (-1850, 64, -1190))
        self.points = {name: self.native_point(build, source.properties(name)["Pos"])
                       for name in (*DOOR_SHOOTERS, *sorted(set(DUST_ON_HIT.values()) | {d for _, d, _ in SLABS.values()}))
                       if name.lower() in source.by_name}

    def native_point(self, build, pos) -> list:
        return build.project.native(pos).round().astype(int).tolist()

    def lt_box(self, build, low, high) -> list:
        a, b = build.project.native(np.array(low, float)), build.project.native(np.array(high, float))
        return [np.minimum(a, b).round().astype(int).tolist(), np.maximum(a, b).round().astype(int).tolist()]

    def box(self, build, name) -> list:
        """A Trigger's box in native units (Pos +- Dims), widened by the party's reach in x and y."""
        p = build.source.properties(name)
        pos, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
        low, high = self.lt_box(build, pos - dims, pos + dims)
        return [[low[0] - PARTY_REACH, low[1] - PARTY_REACH, low[2]], [high[0] + PARTY_REACH, high[1] + PARTY_REACH,
                                                                       high[2]]]

    def model_box(self, build, model, top_lt=None) -> list:
        points = np.array(build.source.models[model].points, float)
        low, high = points.min(0), points.max(0)
        if top_lt is not None:
            high[1] = top_lt
        return self.lt_box(build, low, high)

    def place_perception_hints(self, build) -> None:
        """MM9's PerceptionBrushes (the bolt on PrisonDoor2, the saw's wall slot, the paddle's plate, the trap room's
        drain button): their Perception polygons as untouchable translucent faces with a cog, shown by the map script
        to a party with Perception 9 (PerceptionValue)."""
        package, source = build.package, build.source
        self.hints, self.hint_faces, self.hint_value = {}, 0, 0
        for k, name in enumerate(HINTS):
            self.hint_value = max(self.hint_value, int(round(as_float(source.properties(name)["PerceptionValue"]))))
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                rooms = build.content.rooms
                room = room_id(_side_room(rooms, polygon, 1) or _side_room(rooms, polygon, -1)
                               or rooms.owner(polygon.points.mean(0)))
                node = f"TRIGGER_perception_{name}_{i}"
                package.add_polygon(node, polygon, build.stats)
                package.room_nodes[room].append(node)
                surface = {"id": node[8:], "source_node": node, "flags": ["untouchable"], "cog_number": COG_HINT + k}
                clicks = dict(HINT_EVENTS, PerceptionBrush0=CLICK_EVENT_BASE + source.by_name[BOLT.lower()]["index"])
                if name in clicks:          # a hint box round a clickable thing takes its click
                    surface["trigger"] = {"event_id": clicks[name], "type": "click"}
                package.metadata["surfaces"].append(surface)
                self.hint_faces += 1
            self.hints[name] = COG_HINT + k

    # --- actors -------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        hidden = {name: GROUP_BUSTS[trigger] for trigger, names in BUSTS.items() for name in names}
        slab_top = {name: max(float(polygon.points[:, 1].max()) for polygon in source.polygons(SLABS[trigger][0]))
                    for trigger, names in BUSTS.items() for name in names}
        out, self.actor = [], {}
        for o in source.objects:
            if o["class"] not in build.project.monster_classes or o["name"] not in bases:
                continue
            radius, height = BODIES[o["class"]]
            group = hidden.get(o["name"], 0)
            # the busts wait in the pockets over the corridor's ceiling slabs, standing on the slab, hidden (out of
            # sight and reach) until the slab breaks and they fall through
            actor = content.actor(o, bases[o["name"]], sector_of_room, group=group, hidden=o["name"] in hidden,
                                  radius=radius, height=height)
            if o["name"] in slab_top:
                # the slab is a breakable brush, not among the floors content.actor stands actors on: its top, in the
                # pocket's room
                x, _, z = o["properties"]["Pos"]
                top = slab_top[o["name"]]
                room = content.owner(np.array([x, top + 20, z]))
                actor["position"]["z"] = int(build.project.native([x, top, z]).round()[2]) + 1
                actor["sector_id"] = sector_of_room[room]
                content.report["actors"][-1]["room"] = room
            self.actor[o["name"]] = actor["actor_index"]
            out.append(actor)
        return out

    # --- map script ---------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Verhoffin Ruins")
        boxes, door = self.boxes, script.door
        script.lines += [
            "local GROUPS = {" + ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(script.groups.items()))
            + "}",
            "local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end",
            "local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end",
            "local function toggleGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end end",
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z + 170 >= b[1][3] and z <= b[2][3] end",
            "local function hurt(amount, kind) evt.DamagePlayer(Players.All, kind or const.Damage.Physical, amount) end",
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            "local function locked() evt.StatusText(\"The door is locked.\") end",
            f"local BOX = {{{', '.join(f'{k} = {{{lua.point(v[0])}, {lua.point(v[1])}}}' for k, v in sorted(boxes.items()))}}}",
            "",
        ]
        script.doors()
        script.chests()
        lines = [
            "-- Doors MM9 locks with nothing to open them (DoubleDoorL/R10, TortureChamberDoor6/7) and the trap room's dummy",
            "-- button (WaterRoomButton1: Locked, no trigger unlocks it).",
            f"handlers[{EV_LOCKED}] = locked",
            f"handlers[{EV_DUMMY_BUTTON}] = function() evt.StatusText(\"The button does not move.\") end",
            "-- Doors in broken walls (no doorway portal: the ruin joins both sides): a click swings the leaves.",
            f"handlers[{EV_DD9}] = function() toggleGroup(\"DD9\") end",
            f"handlers[{EV_PRISON14}] = function() toggleGroup(\"PrisonDoor14\") end",
            f"handlers[{EV_CELL8}] = function() toggleGroup(\"Cell8\") end",
            "",
            "-- The bolt on PrisonDoor2 (DestructableBrush12: HitPoints 50; its DamageTrigger turns PerceptionBrush0 off, its",
            "-- DeathTrigger unlocks PrisonDoor2): a scene destructible; weapons break it as in MM9, a click still does",
            "-- (the shared click's killing blow).",
            f"handlers[{EV_BOLT_HIT}] = function()   -- damaged",
            "    set(\"BoltHintOff\", 1)",
            f"    evt.SetFacetBit({self.hints['PerceptionBrush0']}, FacetBits.Invisible, true)",
            "end",
            f"handlers[{EV_BOLT}] = function()   -- broken",
            "    set(\"BoltBroken\", 1); set(\"BoltHintOff\", 1)",
            "    evt.PlaySoundName(\"events/doorbreak.wav\", 0, 0, 0)",
            f"    evt.SetFacetBit({self.hints['PerceptionBrush0']}, FacetBits.Invisible, true)",
            "end",
            f"handlers[{EV_PRISON2}] = function()",
            "    if var(\"BoltBroken\") == 0 then evt.StatusText(\"The door is bolted shut.\") return end",
            "    toggleGroup(\"PrisonDoor2\")",
            "end",
            "",
            f"-- Door5 (DoorLock.scr \"{ITEM_DOOR5_KEY} 1\"): the key (item {ITEM_DOOR5_KEY}, givetake.scr on the table in the "
            "south-east room) unlocks it and is taken.",
            f"handlers[{EV_DOOR5}] = function()",
            "    if var(\"Door5Unlocked\") == 0 then",
            f"        if MM9.hasItem({ITEM_DOOR5_KEY}, \"verhoffinruins:Door5\") == 0 then locked() return end",
            f"        MM9.takeItem({ITEM_DOOR5_KEY}, \"verhoffinruins:Door5\")",
            "        set(\"Door5Unlocked\", 1)",
            "    end",
            "    toggleGroup(\"Door5\")",
            "end",
            "",
            "-- FallingDoor: it falls flat once (its OpenTrigger2 locks it; FallingFrame and DroppingFrame are not in the map).",
            f"handlers[{EV_FALLING}] = function()",
            "    if var(\"DoorFallen\") == 1 then return end",
            "    set(\"DoorFallen\", 1)",
            "    open(\"FallingDoor\")",
            "end",
            "",
        ]
        script.add(lines, (EV_LOCKED, "Door", "Door"), (EV_DUMMY_BUTTON, "Button", "Button"), (EV_DD9, "Door", "Door"),
                   (EV_PRISON14, "Door", "Door"), (EV_CELL8, "Cell door", "Door"), (EV_BOLT, "Bolt", None), (EV_BOLT_HIT, "Bolt", None),
                   (EV_PRISON2, "Door", "Door"), (EV_DOOR5, "Door", "Door"),
                   (EV_FALLING, "Door", "Door"))
        lines = self.script_hints()
        lines += self.script_quest(build)
        lines += self.script_pentagram(build)
        lines += self.script_water(build)
        lines += self.script_traps(build)
        script.add([], *self._registrations, *[(event, f"{slab} broken", None) for slab, _, event in SLABS.values()],
                   (EV_TORTURE, "Door", "Door"),
                   *[(event, "Valve", "Valve") for event in EV_NOZZLE.values()], (EV_DRAIN, "Button", "Button"),
                   *[(timer, title, None, "timer") for timer, title in (
                       (T_POLL, "Trigger volumes"), (T_SAW_BACK, "Saw back"), (T_SAW_REARM, "Saw re-armed"),
                       (T_PADDLE_BACK, "Paddle back"), (T_PADDLE_REARM, "Paddle re-armed"), (T_WATER, "Water"),
                       (T_HINTS, "Perception hints"))])
        hide_quest = [
            f"    if MM9.hasKey({KEY_BOOK}) == 1 or MM9.hasKey({KEY_BOOK_DONE}) == 1 then evt.SetSprite({COG_BOOK}, false) end",
            f"    evt.SetSprite({COG_CAPSTONE}, MM9.hasKey({KEY_PLACED}) == 1)",
            "    for k = 0, 4 do evt.SetSprite(" + str(COG_FIRE) + " + k, var(\"PuzzleStarted\") == 1) end",
            f"    if var(\"BoltHintOff\") == 1 then evt.SetFacetBit({self.hints['PerceptionBrush0']}, FacetBits.Invisible, true) end",
        ]
        lines += ["",
                  "handlers[1] = function()   -- map load: the scripts' Init (Capstone.scr :placed, Writ.scr :Init, fakebook.scr",
                  "                           -- :deletecheck, givetake.scr :Init, PentagramPuzzle.scr :InitPentagramPuzzle)",
                  *hide_quest,
                  "    updateHints()",
                  f"    evt.StartTimer({T_POLL}, seconds(0.25))",
                  "end"]
        script.add(lines, (1, "Map load", None))
        # The busts' DamageTriggerTarget "On" (the Fire BreakOutDust0): the first hit on each puffs dust there.
        dust = {self.actor[name]: self.points[fire] for name, fire in DUST_ON_HIT.items()
                if name in self.actor and fire in self.points}
        if dust:
            table = ", ".join(f"[{a}] = {{{', '.join(map(str, p))}}}" for a, p in sorted(dust.items()))
            script.lines += [
                "-- DamageTriggerTarget \"On\" (BustWraith0-3 -> the Fire BreakOutDust0): a hit raises its dust once.",
                f"local DUST_ON_HIT = {{{table}}}",
                f"handlers[{DAMAGE_HOOK}] = function(context)",
                "    local p = DUST_ON_HIT[context.actorIndex]",
                "    if p == nil or var(\"BustDust\" .. context.actorIndex) == 1 then return end",
                "    set(\"BustDust\" .. context.actorIndex, 1)",
                "    evt.SpawnWorldEffect(\"mm9:smoke\", p[1], p[2], p[3], 1)",
                "end",
            ]
            script.hooks.append(f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Bust dust", handlers[{DAMAGE_HOOK}])')
        return script.finish(on_load=[1])

    def script_quest(self, build) -> list[str]:
        """The capstone (Capstone.scr, placeCapstone.scr), the writ (Writ.scr), the fake book (fakebook.scr), the
        diary scraps (BookLetter.scr)."""
        lines = [
            f"-- The headsman's block (HeadsmanBlock1, placeCapstone.scr :Use1): on the capstone quest (key {KEY_CAPSTONE_QUEST}) "
            f"with the Capstone of Order (item {ITEM_CAPSTONE})",
            f"-- the capstone is placed (Capstone.scr :OnPlace): key {KEY_PLACED}, {EXP_PLACED} experience, the capstone shows,",
            f"-- the writ (a world item shown with key {KEY_PLACED}) appears (Writ.scr :OnInit), the item is taken.",
            f"handlers[{EV_BLOCK}] = function()",
            f"    if MM9.hasKey({KEY_CAPSTONE_QUEST}) == 0 or MM9.hasKey({KEY_PLACED}) == 1 then return end",
            f"    if MM9.hasItem({ITEM_CAPSTONE}, \"verhoffinruins:HeadsmanBlock1\") == 0 then return end",
            f"    MM9.giveKey({KEY_PLACED})",
            f"    {experience_lua(EXP_PLACED, KEY_PLACED)}",
            "    MM9.playSound(\"sounds/events/quest.wav\")",
            f"    evt.SetSprite({COG_CAPSTONE}, true)",
            f"    MM9.takeItem({ITEM_CAPSTONE}, \"verhoffinruins:HeadsmanBlock1\")",
            "end",
            f"handlers[{EV_WRIT}] = function()   -- writ picked up, Writ.scr :Onuse: the Writ of Fate (item {ITEM_WRIT}), "
            f"key {KEY_WRIT}",
            f"    if MM9.hasKey({KEY_WRIT}) == 1 or MM9.hasKey({KEY_PLACED}) == 0 then return end",
            f"    {experience_lua(EXP_WRIT, KEY_WRIT)}",
            f"    MM9.giveKey({KEY_WRIT})",
            "    MM9.playSound(\"sounds/events/quest.wav\")",
            "end",
            f"handlers[{EV_BOOK}] = function()   -- Book, fakebook.scr :haskey: the fake Verhoffin book (item {ITEM_FAKE_BOOK}), "
            f"keys {KEY_BOOK} and {KEY_BOOK2}",
            f"    if MM9.hasKey({KEY_BOOK}) == 1 then return end",
            f"    MM9.giveKey({KEY_BOOK})",
            f"    MM9.giveKey({KEY_BOOK2})",
            f"    give({ITEM_FAKE_BOOK}, \"verhoffinruins:Book\")",
            f"    evt.SetSprite({COG_BOOK}, false)",
            "end",
        ]
        registrations = [(EV_BLOCK, "Headsman's block", "Block"), (EV_WRIT, "Writ", "Writ"), (EV_BOOK, "Book", "Book")]
        for name, event in EV_LETTER.items():
            number = int(build.source.properties(name)["ScriptParams"].split()[0])
            title, text = letter(number)
            lines.append(f"handlers[{event}] = function() evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) "
                         f"end   -- {name}, BookLetter.scr \"{number} Letter\"")
            registrations.append((event, "Scrap of Diary", "Scroll"))
        self._registrations = registrations
        return [""] + lines

    def script_pentagram(self, build) -> list[str]:
        """PentagramPuzzle.scr with the touch triggers PentaCenter (Start, the flames on) and TriggerPentagram1-5
        (First..Fifth, each off once stepped on until TriggerPuzzleOn re-arms them)."""
        return [
            "",
            "-- The pentagram (PentagramPuzzle.scr \"TortureChamberDoor0 TortureChamberDoor1\"): the torture chamber's door is",
            "-- shut and locked; the centre starts the puzzle and lights the five flames (PentaCenter); the points in the order",
            "-- of the flames' colours (red, yellow, blue, green, orange; letter 485) each latch with a click, a wrong one",
            "-- re-arms them all (OnFailure); the fifth unlocks both leaves and opens TortureChamberDoor1 only (UnlockDoor's",
            "-- \"Trigger NULL, open\" leaves TortureChamberDoor0 shut).",
            f"local POINTS = {{{', '.join(lua_string(n) for n in PENTA_ORDER)}}}",
            "local function pointsOn() for k = 1, 5 do set(\"Point\" .. k .. \"Off\", 0) end end",
            "local function puzzleStart()",
            "    if var(\"PuzzleStarted\") == 1 then return end",
            "    set(\"PuzzleStarted\", 1)",
            f"    for k = 0, 4 do evt.SetSprite({COG_FIRE} + k, true) end",
            "    pointsOn()",
            "end",
            "local function puzzleStep(k)",
            "    if var(\"PuzzleStarted\") == 0 or var(\"PuzzleSolved\") == 1 or var(\"Point\" .. k .. \"Off\") == 1 then return end",
            "    set(\"Point\" .. k .. \"Off\", 1)",
            "    if var(\"PuzzleProgress\") ~= k - 1 then        -- OnFailure",
            "        set(\"PuzzleProgress\", 0); pointsOn()",
            "        set(\"PuzzleFailures\", var(\"PuzzleFailures\") + 1)",
            "        return",
            "    end",
            "    set(\"PuzzleProgress\", k)",
            "    evt.PlaySoundName(\"door/doorlatch01.wav\", 0, 0, 0)",
            "    if k == 5 then                                   -- UnlockDoor",
            "        set(\"PuzzleSolved\", 1)",
            "        open(\"TortureChamberDoor1\"); set(\"Leaf1Open\", 1)",
            "    end",
            "end",
            "-- The leaves' OpenTriggers: TortureChamberDoor0 turns DoorShooter0/1 on, TortureChamberDoor1 turns them off.",
            f"handlers[{EV_TORTURE}] = function()",
            "    if var(\"PuzzleSolved\") == 0 then locked() return end",
            "    local opening0 = var(\"Leaf0Open\") == 0",
            "    local opening1 = var(\"Leaf1Open\") == 0",
            "    toggleGroup(\"TortureDoor\")",
            "    set(\"Leaf0Open\", opening0 and 1 or 0); set(\"Leaf1Open\", opening1 and 1 or 0)",
            "    if opening0 then set(\"ShootersOn\", 1) end",
            "    if opening1 then set(\"ShootersOn\", 0) end",
            "end",
        ]

    def script_water(self, build) -> list[str]:
        """DrainWater.scr ("MarkerFull MarkerEmpty TriggerWaterLock TriggerWaterUnlock") with the nozzles', the drain
        button's and the triggers' wiring. With `swim: true` the water is a volume on the trap's mover and the engine
        times the party's breath and drowns it (MM9: 15 s, then 1/6 of maximum HP every 2 s); without it a fixed
        drowning damage stands in."""
        if swimming(build):
            drowning = [
                f"handlers[{T_WATER}] = function()   -- the rising water: the engine drowns a party under it (breath)",
                "    if var(\"WaterState\") ~= 1 then return end",
                f"    evt.StartTimer({T_WATER}, seconds(1))",
                "    set(\"WaterSeconds\", var(\"WaterSeconds\") + 1)",
                "end",
            ]
        else:
            drowning = [
                f"handlers[{T_WATER}] = function()   -- the rising water: drowning once it is over the party's heads",
                "    if var(\"WaterState\") ~= 1 then return end",
                f"    evt.StartTimer({T_WATER}, seconds(1))",
                "    set(\"WaterSeconds\", var(\"WaterSeconds\") + 1)",
                "    local x, y, z = evt.GetPartyPosition()",
                "    if var(\"WaterSeconds\") >= 8 and inBox(BOX.TrapRoom, x, y, z) and var(\"WaterSeconds\") % 2 == 0 then",
                f"        hurt({DROWN_DAMAGE}, const.Damage.Water)",
                "        set(\"DrownHits\", var(\"DrownHits\") + 1); set(\"Drowned\", 1)",
                "    end",
                "end",
            ]
        return [
            "",
            "-- The water trap (DrainWater.scr on WaterTrap): opening any of the four nozzles fills the room (its fill: the",
            "-- TriggerWaterLock relay shuts and locks DoubleDoor5, locks the nozzles and unlocks the drain button; the",
            "-- nozzles' OpenTriggers light the drain button's PerceptionBrush and put out the nozzles' PerceptionLights).",
            "-- The water rises to the ceiling at MM9's 10 LT a second; under it the party drowns. The drain button",
            "-- (WaterRoomButton2) lowers it again and unlocks the door and the nozzles (TriggerWaterUnlock).",
            "local function trapFill()",
            "    if var(\"WaterState\") ~= 0 then return end",
            "    set(\"WaterState\", 1)",
            "    set(\"WaterFills\", var(\"WaterFills\") + 1)",
            "    closeGroup(\"DD5\")",
            "    closeGroup(\"WaterTrap\")",
            "    -- a nozzle's OpenTrigger2: PerceptionLightOff, which puts out the four nozzles' PerceptionLights",
            *[f"    {perception_light_lua(build, f'PerceptionLight{k}', False)}" for k in range(4)],
            "    evt.PlaySoundName(\"ambient/fountain_20.wav\", 0, 0, 0)",
            f"    evt.SetFacetBit({self.hints['PerceptionLightWaterTrap']}, FacetBits.Invisible, not perceptive())",
            f"    set(\"WaterSeconds\", 0); evt.StartTimer({T_WATER}, seconds(1))",
            "end",
            "local function trapDrain()",
            "    if var(\"WaterState\") ~= 1 then return end",
            "    set(\"WaterState\", 0)",
            "    set(\"WaterDrains\", var(\"WaterDrains\") + 1)",
            "    openGroup(\"WaterTrap\")",
            "    open(\"WaterRoomButton2\")",
            f"    set(\"AmbientSound{build.source.by_name['waterfill']['index']}\", 2)   -- its OpenTrigger2: waterfill off",
            "    for k = 0, 3 do close(\"WaterNozzle\" .. k) end",
            "    -- the nozzles' CloseTriggers: PerceptionLight0-3 on again",
            *[f"    {perception_light_lua(build, f'PerceptionLight{k}', True)}" for k in range(4)],
            "    evt.PlaySoundName(\"ambient/fountain_20.wav\", 0, 0, 0)",
            f"    evt.SetFacetBit({self.hints['PerceptionLightWaterTrap']}, FacetBits.Invisible, true)",
            "end",
            "local function nozzle(k)",
            "    if var(\"WaterState\") ~= 0 then evt.StatusText(\"The valve will not turn.\") return end",
            "    open(\"WaterNozzle\" .. k)",
            f"    set(\"AmbientSound{build.source.by_name['waterfill']['index']}\", 1)   -- its OpenTrigger3: waterfill on",
            "    trapFill()",
            "end",
            *[f"handlers[{event}] = function() nozzle({k}) end   -- {name}" for k, (name, event) in enumerate(EV_NOZZLE.items())],
            f"handlers[{EV_DRAIN}] = function()   -- WaterRoomButton2: locked unless the room is full",
            "    if var(\"WaterState\") ~= 1 then evt.StatusText(\"The button does not move.\") return end",
            "    close(\"WaterRoomButton2\")",
            "    trapDrain()",
            "end",
            *drowning,
        ]

    def script_traps(self, build) -> list[str]:
        """The touch triggers (polled), the saw blade, the paddle, the electrified pit, the door's shooters, the
        busts."""
        bust_groups = ", ".join(f"{name} = {group}" for name, group in GROUP_BUSTS.items())
        s0, s1 = self.points[DOOR_SHOOTERS[0]], self.points[DOOR_SHOOTERS[1]]
        return [
            "",
            "-- The saw blade (SawBladeTrigger1: SawBlade1 on, SawBladeArm1 use, its damage brush on 0.5 s later and off at",
            f"-- 5 s): blade and arm slide out across the corridor and back; {SAW_DAMAGE} to a party in the blade's path.",
            "-- The blade (RotatingBrush AttachTo SawBladeArm1: mover spin) spins up as it comes out (SawBladeTrigger1: on)",
            "-- and down once the arm is back (SawBladeArm1's CloseTrigger: off).",
            "local function saw()",
            "    openGroup(\"Saw\")",
            "    evt.SpinMover(DOORS.SawBlade1, \"on\")",
            "    evt.PlaySoundName(\"events/gears01.wav\", 0, 0, 0)",
            "    set(\"SawRuns\", var(\"SawRuns\") + 1)",
            f"    arm({T_SAW_BACK}, 2)",
            "end",
            f"handlers[{T_SAW_BACK}] = function()",
            f"    if not fired({T_SAW_BACK}) then return end",
            "    closeGroup(\"Saw\")",
            f"    arm({T_SAW_REARM}, 3)",
            "end",
            f"handlers[{T_SAW_REARM}] = function() if fired({T_SAW_REARM}) then set(\"DoneSawBladeTrigger1\", 0); "
            "evt.SpinMover(DOORS.SawBlade1, \"off\") end end",
            "",
            "-- The paddle over the electrified pit (PaddleTrigger: Paddle toggle; its OpenTrigger swings SwingPaddle, whose",
            "-- CloseTrigger swings the paddle back; the paddle's CloseTrigger re-arms PaddleTrigger): it sweeps across the",
            "-- plate toward the pit and back, pushing what stands in its way.",
            "local function paddle()",
            "    openGroup(\"Paddle\"); openGroup(\"PaddlePlate\")",
            "    set(\"PaddleRuns\", var(\"PaddleRuns\") + 1)",
            f"    arm({T_PADDLE_BACK}, 2)",
            "end",
            f"handlers[{T_PADDLE_BACK}] = function()",
            f"    if not fired({T_PADDLE_BACK}) then return end",
            "    closeGroup(\"Paddle\"); closeGroup(\"PaddlePlate\")",
            f"    arm({T_PADDLE_REARM}, 4)",
            "end",
            f"handlers[{T_PADDLE_REARM}] = function() if fired({T_PADDLE_REARM}) then set(\"DonePaddleTrigger\", 0) end end",
            "",
            "-- The busts (KingKong.scr \"BreakOut<k>\" :FallThrough on BustTrigger0/1's ForceFall): the trigger sends",
            "-- ForceFall to the pocket's KingKong monster (its first), which destroys the ceiling slab it stands on (a",
            "-- scene destructible: stone debris and MM9's crumble sound). Only alive does it take ForceFall (MM9.receives).",
            "-- A slab broken, by the bust or by the party's weapons (CanDamage, 100 HP), drops its pocket's monsters into",
            "-- the corridor, hostile, and its dust rises (its DeathTrigger: BreakOutDust<k> On).",
            f"local BUSTS = {{{bust_groups}}}",
            "local KINGKONG = {" + ", ".join(f"{t} = {{\"{names[0]}\", {self.actor[names[0]]}}}"
                                            for t, names in BUSTS.items() if names[0] in self.actor) + "}",
            "local SLABS = {" + ", ".join(f"{t} = {build.source.by_name[slab.lower()]['index']}"
                                         for t, (slab, _, _) in SLABS.items()) + "}   -- DAT index: the destructible",
            "local function bust(name)",
            "    local k = KINGKONG[name]",
            "    if k ~= nil and not MM9.receives(\"verhoffinruins\", k[1], \"ForceFall\", k[2]) then return end",
            "    set(\"Busted\" .. name, 1)",
            "    evt.DestroyDestructible(SLABS[name])",
            "end",
            *[line for t, (slab, dust, event) in SLABS.items() for line in (
                f"handlers[{event}] = function()   -- {slab} broken: the {t} pocket's monsters fall",
                f"    evt.SetMonGroupBit({GROUP_BUSTS[t]}, MonsterBits.Invisible, false)",
                f"    evt.SetMonGroupBit({GROUP_BUSTS[t]}, MonsterBits.Hostile, true)",
                f"    evt.SpawnWorldEffect(\"mm9:smoke\", {', '.join(map(str, self.points[dust]))}, 1)   -- {dust}",
                "end")],
            "",
            "-- The door's shooters (DoorShooter0/1: FireBolt, DamageAmt 20, every 4 s while on) at the far wall of the",
            "-- torture chamber, aimed at a party inside it; a bolt strikes the party in its path (strikesParty).",
            "local function shoot(sx, sy, sz, damage)",
            "    local x, y, z = evt.GetPartyPosition()",
            "    z = z + 100",
            "    local dx, dy, dz = x - sx, y - sy, z - sz",
            "    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))",
            "    local k = math.max(64 / length, 0.1)",
            "    local shot = evt.FireMissile(\"Fire\", sx + dx * k, sy + dy * k, sz + dz * k, x, y, z, damage, \"Fire\", 0, 0, "
            "true)",
            "    if shot then MM9.launchSound(\"FireBolt\", sx, sy, sz) end",
            "    set(\"ShotsFired\", var(\"ShotsFired\") + (shot and 1 or 0)); if shot then set(\"Shot\", 1) end",
            "end",
            f"handlers[{T_SHOOT}] = function()",
            "    if var(\"ShootersOn\") ~= 1 then return end",
            "    local x, y, z = evt.GetPartyPosition()",
            "    if not inBox(BOX.TortureChamber, x, y, z) then return end",
            f"    shoot({s0[0]}, {s0[1]}, {s0[2]}, {BOLT_DAMAGE}); shoot({s1[0]}, {s1[1]}, {s1[2]}, {BOLT_DAMAGE})",
            "end",
            "",
            "-- MM9's Trigger volumes, polled four times a second: each fires once on entry (Trigger0, the saw's and the",
            "-- paddle's re-arm themselves, the busts' turn themselves off).",
            "local VOLUMES = {",
            "    {name = \"Trigger0\", run = function()   -- PerceptionLightWaterTrap off (the trap room's door)",
            f"        evt.SetFacetBit({self.hints['PerceptionLightWaterTrap']}, FacetBits.Invisible, true) end, rearm = true}},",
            "    {name = \"SawBladeTrigger1\", run = saw},",
            "    {name = \"PaddleTrigger\", run = paddle},",
            "    {name = \"PentaCenter\", run = puzzleStart},",
            *[f"    {{name = \"{n}\", run = function() puzzleStep({k + 1}) end, rearm = true}}," for k, n in enumerate(PENTA_ORDER)],
            *[f"    {{name = \"{n}\", run = function() bust(\"{n}\") end}}," for n in GROUP_BUSTS],
            "}",
            "local inside, polls = {}, 0",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    local x, y, z = evt.GetPartyPosition()",
            "    polls = polls + 1",
            "    for _, v in ipairs(VOLUMES) do",
            "        local now = inBox(BOX[v.name], x, y, z)",
            "        if now and not inside[v.name] and var(\"Done\" .. v.name) == 0 then",
            "            if not v.rearm then set(\"Done\" .. v.name, 1) end",
            "            v.run()",
            "        end",
            "        inside[v.name] = now",
            "    end",
            "    if polls % 4 == 0 then",
            f"        if var(\"Armed{T_SAW_BACK}\") == 1 and inBox(BOX.SawDamage, x, y, z) then",
            f"            hurt({SAW_DAMAGE}); set(\"SawHits\", var(\"SawHits\") + 1); set(\"SawHit\", 1)",
            "        end",
            f"        if inBox(BOX.PitDamage, x, y, z) then hurt({PIT_DAMAGE}, const.Damage.Electric); "
            "set(\"PitHits\", var(\"PitHits\") + 1); set(\"PitHit\", 1) end",
            f"        if polls % 16 == 0 then handlers[{T_SHOOT}]() end",
            "    end",
            "end",
        ]

    def script_hints(self) -> list[str]:
        hints = ", ".join(str(cog) for name, cog in self.hints.items() if name != "PerceptionLightWaterTrap")
        return [
            "",
            f"-- The PerceptionBrushes (Perception {self.hint_value}): the bolt, the saw's slot and the paddle's plate show to a",
            "-- party with the Perception for them; the drain button's only while the room is full (the nozzles'",
            "-- OpenTrigger turns it on, Trigger0 and the drain turn it off). Checked on load and every 3 s.",
            f"local function perceptive() return evt.CheckSkill({PERCEPTION_SKILL}, 0, {self.hint_value}) end",
            f"local HINTS = {{{hints}}}",
            "local function updateHints()",
            "    local want = perceptive() and 2 or 1",
            "    if var(\"PerceptionHints\") == want then return end",
            "    set(\"PerceptionHints\", want)",
            "    for _, cog in ipairs(HINTS) do",
            f"        if not (cog == {self.hints['PerceptionBrush0']} and var(\"BoltHintOff\") == 1) then",
            "            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)",
            "        end",
            "    end",
            f"    if var(\"WaterState\") ~= 1 then evt.SetFacetBit({self.hints['PerceptionLightWaterTrap']}, FacetBits.Invisible, true) end",
            "end",
            f"handlers[{T_HINTS}] = updateHints",
        ]

    def scene(self, build, scene: dict) -> None:
        """The trap water (two-sided, translucent, untouchable mover faces), the perception hints (translucent, two
        sided), the animated textures' frames."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        faces = {f["index"]: f for f in blv["faces"]}

        def faces_of(texture: str) -> list[int]:
            alias = build.source.aliases[texture.lower()]["alias"].lower()
            return sorted(f["index"] for f in blv["faces"] if str(f.get("texture_name", "")).lower() == alias)

        trap = sorted(i for d in scene["initial_state"]["doors"] for i in d["face_ids"]
                      if any(m["door_id"] == d["door_id"] and m["group"] == TRAP_MODEL for m in build.movers))
        if not trap:
            raise SystemExit("the trap room's water: no mover faces")
        hints = [i for t in PERCEPTION_TEXTURES for i in faces_of(t)]
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        scene.setdefault("translucent_faces", []).extend([
            {"faces": trap, "opacity": TRAP_OPACITY, "tint": [1.0, 1.0, 1.0], "two_sided": True},
            {"faces": sorted(hints), "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0], "two_sided": True}])
        scene["initial_state"].setdefault("face_attribute_overrides", []).extend(
            {"face_index": i, "legacy_attributes": int(faces[i]["attributes"]) | UNTOUCHABLE} for i in trap)
        build.stats["trap_water_faces"] = len(trap)
        build.stats["crevasse_water_faces"] = self.crevasse_faces
        if build.project.install:
            for texture in (*PERCEPTION_TEXTURES, CREVASSE_SPR):
                if texture in build.source.aliases and build.source.aliases[texture].get("animation_frames"):
                    self.install_frames(build, texture)
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)
        if swimming(build):
            self.water_volumes(build, scene)

    def water_volumes(self, build, scene: dict) -> None:
        """The scene's `water_volumes` (dungeon/water.py, written by the shared build): the crevasse (BlueWater0/1),
        the electrified pit (ElectricWater1) and the trap room's WaterTrap, whose top follows its slide mover. The
        trap's face is built at its full height (TRAP_FULL_LT, the BLV's stored pose) and the mover lowers it to MM9's
        DAT top when open, so the volume's top is authored at the stored pose."""
        volumes = scene.get("water_volumes", [])        # the shared build's (dungeon/build.py, `swim: true`)
        if sorted(v["id"] for v in volumes) != sorted(SWIM_VOLUMES) or not any(
                v.get("mover_door_id") for v in volumes if v["id"] == TRAP_MODEL):
            raise SystemExit(f"water volumes: {[v['id'] for v in volumes]}, expected {SWIM_VOLUMES}")
        full = round(TRAP_FULL_LT * SCALE - build.project.offset[2], 1)
        for volume in volumes:
            if volume["id"] == TRAP_MODEL:
                for piece in volume["pieces"]:
                    piece["top"] = full
        objects = water.liquid_objects(build.source, SWIM_VOLUMES)
        mismatches = water.room_mismatches(build, [o for o in objects if o["name"] != TRAP_MODEL])
        build.stats["water_volumes"] = len(volumes)
        build.stats["water_volume_pieces"] = sum(len(v["pieces"]) for v in volumes)
        build.stats["water_room_mismatches"] = len(mismatches)
        holes = water.bed_holes(build, [o for o in objects if o["name"] != TRAP_MODEL])
        build.stats["water_bed_holes"] = len(holes)
        self.water_report = {"volumes": [{"id": v["id"], "pieces": len(v["pieces"]),
                                          "top": sorted({p["top"] for p in v["pieces"]}),
                                          "bottom": sorted({p["bottom"] for p in v["pieces"]}),
                                          "mover_door_id": v.get("mover_door_id")} for v in volumes],
                             "room_mismatches": mismatches, "bed_holes": holes}
        if mismatches:
            print("WARNING: water surfaces between two rooms (the engine crosses rooms only at portals):", mismatches)
        if holes:
            print(f"WARNING: {len(holes)} points of open water without a bed (build_report.json water.bed_holes)")

    def install_frames(self, build, texture: str) -> None:
        """An MM9 .spr as a texture frame sequence in the review root's engine table (as Drangheim Prison's)."""
        entry = build.source.aliases[texture]
        frames = [entry["alias"]] + [frame["alias"] for frame in entry["animation_frames"][1:]]
        relative = "engine/data_tables/texture_frame_data.txt"
        with tables.locked("review_tables.lock"):
            text = review_root.mirror_path(relative).read_text()
            if f"\n{frames[0]}\t" in text:
                return
            rows = [f"{name}\t0\t1\t{len(frames) if i == 0 else 0}\t{FRAME_FLAGS[i == 0, i < len(frames) - 1]}"
                    for i, name in enumerate(frames)]
            review_root.install(relative, (text.rstrip("\n") + "\n" + "\n".join(rows) + "\n").encode())

    def report(self, build) -> dict:
        return {"scripted": {"actors": self.actor, "boxes": self.boxes, "points": self.points, "hints": self.hints,
                             "trap_lowered_lt": getattr(self, "trap_lowered_lt", None)},
                "water": getattr(self, "water_report", None)}



if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, VerhoffinRuins()))
