#!/usr/bin/env python3
"""
Dungeon of Secrets, MM9 rework: MM9's DUNGEONOFSECRETS.dat (the Ranger trial off Frosgard) as a native BLV on the
shared dungeon converter (../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_dungeonofsecrets/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_dungeonofsecrets/convert.py --plan     # rooms only: work/rooms*.png
    python3 level_generation/projects/mm9r_dungeonofsecrets/convert.py --lua      # only the map Lua, from the last build

overrides.yml holds every DAT world model's rule and the seed exclusions; this file adds the population (props.json
from ../../props/mm9_dungeonofsecrets_claude, Chadwick Boorsley), the perception hints, and MM9's object wiring as
native Lua (README.md, "Scripted objects"). The map has one .scr (NPC417.scr, Chadwick); everything else is MM9's own
object messaging: Trigger volumes (TargetName/MessageName, SendDelay, StartOn, ActivationCount), Door and RotatingDoor
Open/CloseTriggers (with Lock/Unlock, Sticky, CloseWaitTime, DoubleDoorName), Shooters, DamageBrush knockbacks and
RotatingBrush saws. They run through one dispatcher in the map Lua (`send(target, message)`), the DAT links carried as
data (Thousand Terrors' route), so every one of the 123 triggers is the DAT's own.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from dungeon import lua, water  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"
UNTOUCHABLE_FACE = 0x20000000
PERCEPTION_COG = 300                # PerceptionBrush<k>: cog PERCEPTION_COG + k
PERCEPTION_SKILL = 29               # evt.CheckSkill's id: the party's best Perception
PERCEPTION_OPACITY = 0.5            # the brushes' Alpha is 0.5-0.75; Dark Passageway's hints draw at 0.5

# --- events, timers, hooks ------------------------------------------------------------------------------------------
EV_LOAD = 1
EV_CLICK_BASE = 200                 # + k: the click (MM9 PushOpen "use") of the k-th clickable group (CLICKABLE)
T_POLL = 380
RUDE_CHADWICK = 417
CHADWICK = "CHADWICK"
# MM9's body (PEASANTM1.abc AnimBinding extents 12 x 34 LT half sizes x Scale 1.2 x 2.56): he stands in a ticket booth
# whose barred window starts 108 native over the floor; the row's 120-unit body would hide under the counter.
CHADWICK_BODY = (37, 209)
CHADWICK_ROW = 367                  # Peasant Human2 MaleA A: MM9's CommonerHuman2MaleA body (PeasantM1.abc)
# NPC417.scr keys (QBits 90000 + key): 243 trial started (RUDE 417 node 3), 244 a trap went off, 245 finished clean,
# 246 rewarded (RUDE), 247 the reward's experience given (:OnRude).
KEY_TRIAL, KEY_TRAPPED, KEY_CLEAN, KEY_REWARDED, KEY_PAID = 243, 244, 245, 246, 247
REWARD_EXPERIENCE = 10000

# MM9 PushOpen doors: a click is MM9's "use" (the party pushing against them). The water grate opener is MM9's
# invisible push box over the grate: the grate's click opens the pair.
CLICKABLE = ([f"axe_door_{k}" for k in ("01", "02", "03", "04", "05", "06", "08", "09", "10")]
             + [f"timer_lever_{k}" for k in ("01", "02", "03", "03a", "04", "05", "06", "08", "09", "10")]
             + [f"fake_lever_{k}" for k in range(1, 22)] + ["entrance_button", "water_grate"])
# Perception hints in front of what they mark take its click (Training Hall lesson).
HINT_TARGET = {"PerceptionBrush0": "timer_lever_10", "PerceptionBrush1": "timer_lever_09",
               "PerceptionBrush2": "timer_lever_08", "PerceptionBrush3": "timer_lever_01",
               "PerceptionBrush4": "timer_lever_02", "PerceptionBrush5": "timer_lever_03",
               "PerceptionBrush6": "timer_lever_04", "PerceptionBrush7": "timer_lever_05",
               "PerceptionBrush8": "timer_lever_06", "PerceptionBrush15": "timer_lever_03a"}
# Non-solid MM9 movers (Solid 0): the swinging blades, the axes and their carrier, the spinning wheels and saws pass
# through the party in MM9 (their DamageBrush knockbacks do the hitting): drawn untouchable.
NON_SOLID = {"Blade", "Axe Mover", "Top Axe", "Bottom Axe", "gtrap7a", "gtrap7b", "Panel Mover", "ratdoortrigger",
             "saw8a", "saw8b", "saw9",
             *[f"axe trap {k}" for k in ("01", "02", "03", "04", "05", "06", "08", "09", "10")]}
# MM9 TouchToOpen doors (a touch opens them): the double-axe trap's two plates and the elevator's floor.
TOUCH_OPEN = ["doubleaxe upper trigger", "doubleaxe lower trigger", "elevator"]
MISSILES = {"firebolt": "Fire"}
# A knockback throws the party along MM9's Current: up to PUSH_MAX_SPEED native units a second for PUSH_SECONDS (the
# flight of the hop it once was, 160 up under gravity 1280), as evt.PushParty's dash. evt.Jump's horizontal speed
# lasted one movement step on the ground (9 units).
PUSH_MAX_SPEED = 1200
PUSH_SECONDS = 0.25
PARTY_RADIUS = 37                   # native: polled boxes grow by the party's radius (MM9 tests the party's box)
PARTY_HEIGHT = 170
AXE_SLIDE_LT = 88.0
# Invisible steps where MM9's player jumps or swims higher than the party can climb (Dook's Castle and Thjorad Mine
# lessons: the party jumps about 35 LT, steps 20). A sloped invisible ramp rising from a floor is walked under, not up
# (the party keeps the floor below it): steps with risers work.
# - the elevator's column stands on a 60 LT box in the middle of section 5's octagon (MM9's player jumps onto the box,
#   then steps onto the column, whose touch takes it down): five steps of 16 LT from the octagon (256 LT) to 336 LT;
# - the flooded pool room under section 4 (floor -24 LT, MM9's water to -16) is 24 LT under the west corridor (floor 0)
#   and 32 LT under the east one (8): MM9's player climbs out of the water, the party by two and three steps.
# (name, axis the party climbs along, its sign, across (from, to), first riser, last edge, spacing, floor y, rise per
# step, steps) in LT: the risers face the way the party comes from.
# ClearWater0 (Water115.spr, SurfaceAlpha 0.3): MM9's water over the pool room under section 4's corridor, its top 16 LT
# under the hub's floor: 8 LT over the room's low floor (-24), 240 in the two shafts and the tunnel under the corridor.
# Its surface as non-solid translucent faces (Training Hall's lobby pool: the party wades), 32 LT tiles over the air.
WATER = ("ClearWater0", -16.0, "water:pool", 0.3)
WATER_TILE = 32.0
# Zone gains on the BLV light colours (LT boxes x0, y0, z0, x1, y1, z1 -> RGB), fitted to MM9's DAT lightmaps with
# ../mm9r_common/hue_vs_lightmaps.py and hue_zones.py (README: Baked lighting).
# Fitted in two rounds: the 16-sample draft (direct 2.1 then): at direct 2.4, ours was 0.75-0.9 of MM9 in most zones, 0.85 as warm
# (R against G), and about half in the red-lit plate room and gauntlet, the flooded pool room and the exit corridor.
# The default (no zone) is the warmth tilt; a zone's gain replaces it. Second round on the 64-sample bake (direct 2.4,
# work/hue_summary.txt of that bake): gain x MM9 / ours per channel / 0.92, with direct_scale 2.2.
DEFAULT_GAIN = (1.1, 1.0, 1.0)      # outside every zone (none is: every light stands in one)
LIGHT_GAINS: list = [
    ((1440, -50, -760, 2100, 200, -100), (1.1, 0.93, 0.93)),   # hub: ours/MM9 R 1.09 G 1.17 B 1.17 at the previous gain (1.1, 1.0, 1.0)
    ((2100, -50, -560, 2950, 500, -260), (1.09, 0.93, 0.93)),   # entrance_stair: ours/MM9 R 1.13 G 1.28 B 1.28 at the previous gain (1.13, 1.1, 1.1)
    ((1300, -50, -480, 1560, 200, -100), (1.15, 0.95, 0.95)),   # s10_s09_room: ours/MM9 R 1.04 G 1.15 B 1.15 at the previous gain (1.1, 1.0, 1.0)
    ((520, -50, -540, 1180, 200, 80), (1.09, 0.9, 0.9)),   # s08_room: ours/MM9 R 1.1 G 1.21 B 1.21 at the previous gain (1.1, 1.0, 1.0)
    ((520, -50, 80, 680, 200, 700), (1.44, 1.22, 1.25)),   # north_corridor: ours/MM9 R 0.86 G 0.96 B 0.94 at the previous gain (1.14, 1.08, 1.08)
    ((-520, -300, 220, 520, 120, 740), (4.0, 3.2, 1.54)),   # pool_room: ours/MM9 R 0.44 G 0.55 B 0.88 at the previous gain (1.85, 1.62, 1.25)
    ((-1160, -100, 740, -700, 250, 1800), (1.66, 3.11, 3.11)),   # plate_room: ours/MM9 R 0.83 G 0.56 B 0.56 at the previous gain (1.27, 1.6, 1.6)
    ((-1160, -100, 1800, -120, 250, 1980), (1.39, 1.15, 1.15)),   # s02_corridor: ours/MM9 R 0.96 G 1.06 B 1.06 at the previous gain (1.23, 1.12, 1.12)
    ((-360, -100, 830, -120, 250, 1800), (1.23, 1.06, 1.06)),   # s02_stair: ours/MM9 R 0.97 G 1.03 B 1.03 at the previous gain (1.1, 1.0, 1.0)
    ((-360, 240, 800, 1060, 600, 1720), (1.51, 1.28, 1.29)),   # lever_room: ours/MM9 R 0.87 G 0.97 B 0.96 at the previous gain (1.21, 1.14, 1.14)
    ((-760, 240, 420, 700, 600, 560), (1.39, 1.1, 0.99)),   # s04_corridor: ours/MM9 R 0.86 G 0.99 B 1.1 at the previous gain (1.1, 1.0, 1.0)
    ((-1000, 240, -530, -380, 600, 80), (1.13, 0.91, 0.91)),   # octagon: ours/MM9 R 1.06 G 1.19 B 1.2 at the previous gain (1.1, 1.0, 1.0)
    ((-760, -50, -530, -620, 200, -140), (1.86, 2.11, 2.11)),   # shaft_foot: ours/MM9 R 0.82 G 0.67 B 0.67 at the previous gain (1.4, 1.3, 1.3)
    ((-460, -60, -800, 1030, 250, -560), (2.99, 2.62, 2.62)),   # gauntlet: ours/MM9 R 0.71 G 0.64 B 0.64 at the previous gain (1.95, 1.54, 1.54)
    ((1030, -60, -780, 1450, 250, -600), (2.67, 2.17, 2.17)),   # exit_corridor: ours/MM9 R 0.68 G 0.8 B 0.8 at the previous gain (1.67, 1.6, 1.6)
]
# The pool room's floor (the player-light stand-in rule: no baked view under luma 10-12). The flooded pool room under
# section 4 came out at half of MM9's lightmaps whatever its lights' gains (its blue fills are over the four-per-point
# cap, bake only, and the 0.3 water drawn over the floor darkens it): its sector (the ground floor's big room 7, which
# also holds the north and west corridors and section 1's plate room) gets the sector minimum light level ROOM_LEVEL,
# which the bake turns into an ambient of max(0.18, (31 - level) / 31 x 0.97) x ambient_scale (Dark Passageway's
# route; the map's level is 30). Revert: ROOM_LEVELS = [] (rebuild, rebake).
ROOM_LEVELS = [((0, 0, 400), 20)]
# The submerged tunnel under section 4's corridor (two 232 LT deep shafts, the west one open, the east one under the
# water grate, joined at -256 LT): MM9's player swims it, and so does the party (the shared water rule, 2026-11-06).
# Only with overrides.yml `map: {swim: false}`: a party that sinks into it (below SURFACE_BELOW_LT) comes up again
# beside the west shaft, or beside the east one when the grate is open. (x0, x1, z0, z1) LT of the tunnel and both
# shafts; arrival points (x, z, floor query y) LT.
TUNNEL_LT = (-345, 345, 425, 520)
SURFACE_BELOW_LT = -80.0
SURFACE_WEST_LT, SURFACE_EAST_LT, EAST_SHAFT_X_LT = (-300, 400, 0), (296, 560, 0), 230
STEPS = [("StepsElevator", "z", -1, (-736, -640), 60, -150, 42.0, 256.0, 16.0, 5),
         ("StepsPoolWest", "x", -1, (436, 508), -480, -512, 16.0, -24.0, 12.0, 2),
         ("StepsPoolEast", "x", 1, (436, 508), 464, 512, 16.0, -24.0, 32.0 / 3.0, 3)]


def as_float(value) -> float:
    """A DAT float stored in an int property (ActivationCount, PerceptionValue, Type) back to its float."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


def lua_str(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def messages(properties: dict, prefix_target: str, prefix_message: str, first: int, last: int) -> list:
    out = []
    for k in range(first, last + 1):
        target = properties.get(f"{prefix_target}{k}")
        message = properties.get(f"{prefix_message}{k}")
        if target and message:
            out.append((str(target), str(message).lower()))
    return out


def in_air(polygons: list, x: float, y: float, z: float) -> bool:
    """Whether (x, y, z) LT lies in air: the first polygon straight above faces down at it (Dook's Castle's)."""
    best, facing = None, False
    for polygon in polygons:
        low, high = polygon.bounds
        if not (low[0] <= x <= high[0] and low[2] <= z <= high[2]) or high[1] < y:
            continue
        n = polygon.normal
        if abs(n[1]) < 1e-6:
            continue
        hit = y + float(np.dot(polygon.points[0] - np.array([x, y, z]), n)) / n[1]
        if hit < y or (best is not None and hit >= best):
            continue
        ring = polygon.points[:, [0, 2]]
        edges = np.roll(ring, -1, axis=0) - ring
        cross = edges[:, 0] * (z - ring[:, 1]) - edges[:, 1] * (x - ring[:, 0])
        if (cross >= -1e-6).all() or (cross <= 1e-6).all():
            best, facing = hit, n[1] < 0
    return best is not None and facing


def flat(points_xz, y: float, texture: str, notes: dict, model: str, role: str, flags: int):
    """A horizontal face over a ring of (x, z) points, front upward, mapped one texel per LT (Training Hall's)."""
    from dungeon.geometry import Polygon
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture,
                      (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), flags, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, polygon.mapping, flags,
                          model, role)
    polygon.notes.update(notes)
    return polygon


def native_box(project, low_lt, high_lt) -> list:
    low, high = project.native(np.asarray(low_lt, float)), project.native(np.asarray(high_lt, float))
    return [np.minimum(low, high).round().astype(int).tolist(), np.maximum(low, high).round().astype(int).tolist()]


def lua_box(box) -> str:
    return "{" + lua.point(box[0]) + ", " + lua.point(box[1]) + "}"


class DungeonOfSecrets(dungeon.Hooks):
    generator = "mm9r_dungeonofsecrets"
    mover_events = {group: (EV_CLICK_BASE + k, "click") for k, group in enumerate(CLICKABLE)}

    # --- the double axes ride their carrier (AttachTo Axe Mover) ---------------------------------------------------
    def extra_seeds(self, build) -> list:
        """MM9 slides the two axes out with their carrier (Axe Mover, 88 LT along -x) and then swings them up and down
        through the floor slots. Native movers do not ride movers: the axes are built where the carrier puts them
        (under the corridor floor, out of sight) and swing about their pivots moved the same way (README:
        Deviations)."""
        self.adjust_source(build.source)
        return super().extra_seeds(build)

    @staticmethod
    def adjust_source(source) -> None:
        """The source edits above and the blade's single turn, once per Source; `--lua` needs them too (it builds a
        fresh Source: without them the Lua timed the blade's MM9 1080 degrees, 3.6 s)."""
        plain = source.polygons
        shift = np.array([-AXE_SLIDE_LT, 0.0, 0.0])

        def polygons(name):
            found = plain(name)
            if name not in ("Top Axe", "Bottom Axe"):
                return found
            from dungeon.geometry import Polygon
            return [Polygon(p.points + shift, p.keys, p.texture, (p.mapping[0] + shift,) + tuple(p.mapping[1:]),
                            p.flags, p.model, p.role, notes=dict(p.notes)) for p in found]
        if not getattr(source, "axes_shifted", False):
            source.polygons = polygons
            for name in ("Top Axe", "Bottom Axe"):
                p = source.properties(name)
                p["RotationPoint"] = [float(p["RotationPoint"][0]) - AXE_SLIDE_LT] + list(p["RotationPoint"][1:])
            # The spinning blade under the stairs turns 1080 degrees in MM9; a native rotating mover turns at most 360:
            # one turn at MM9's speed (README: Deviations).
            blade = source.properties("Blade")
            blade["RotationAngles"] = [0.0, 360.0, 0.0]
            source.axes_shifted = True

    def edit_polygons(self, build, polygons: list) -> list:
        from dungeon.geometry import Polygon
        out = []
        invisible = next(p for p in polygons if p.role == "invisible")
        out.extend(polygons)

        def face(name, ring, up):
            ring = np.asarray(ring, float)
            polygon = Polygon(ring, [tuple(np.round(q, 1)) for q in ring], invisible.texture, invisible.mapping,
                              invisible.flags, name, "invisible")
            if (polygon.normal @ up) < 0:
                ring = ring[::-1].copy()
                polygon = Polygon(ring, [tuple(np.round(q, 1)) for q in ring], invisible.texture, invisible.mapping,
                                  invisible.flags, name, "invisible")
            polygon.notes.update(invisible.notes)
            out.append(polygon)
        model, y, texture, _ = WATER
        points = np.array(build.source.models[model].points, float)
        (wx0, wz0), (wx1, wz1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        alias = build.source.aliases[texture]
        for polygon in polygons:
            polygon.bounds = (polygon.points.min(0), polygon.points.max(0))
        self.water_faces = 0
        for row in np.arange(wz0, wz1, WATER_TILE):
            run = None
            for column in np.arange(wx0, wx1 + WATER_TILE, WATER_TILE):
                wet = column < wx1 and sum(in_air(polygons, min(column + u * WATER_TILE, wx1 - 0.5), y + 1,
                                                  min(row + v * WATER_TILE, wz1 - 0.5))
                                           for u in (0.05, 0.5, 0.95) for v in (0.05, 0.5, 0.95)) >= 5
                if wet and run is None:
                    run = column
                elif not wet and run is not None:
                    top = min(row + WATER_TILE, wz1)
                    out.append(flat([(run, row), (run, top), (column, top), (column, row)], y, texture,
                                    {"width": alias["width"], "height": alias["height"]}, model, "nonsolid", 0x1088))
                    self.water_faces += 1
                    run = None
        for name, axis, sign, (a0, a1), first, last, spacing, floor, rise, count in STEPS:
            def point(along, across, height):
                return [along, height, across] if axis == "x" else [across, height, along]
            for i in range(count):
                at = first + sign * i * spacing
                low, high = floor + i * rise, floor + (i + 1) * rise
                face(f"{name}{i}top", [point(at, a0, high), point(at, a1, high), point(last, a1, high),
                                       point(last, a0, high)], np.array([0.0, 1.0, 0.0]))
                facing = np.array([-sign, 0.0, 0.0]) if axis == "x" else np.array([0.0, 0.0, -sign])
                face(f"{name}{i}riser", [point(at, a0, low), point(at, a1, low), point(at, a1, high),
                                         point(at, a0, high)], facing)
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        self.scale_lights(build)
        levels = {content.owner(np.array(point, float)): level for point, level in ROOM_LEVELS}
        self.room_levels = levels
        write = build.package.write

        def write_with_levels(*args, **kwargs):
            for room in build.package.metadata["rooms"]:
                if room["id"] in levels:
                    room["min_ambient_light_level"] = levels[room["id"]]
            return write(*args, **kwargs)
        build.package.write = write_with_levels
        if PROPS.exists():
            content.props(PROPS)
        else:
            print("note: props.json is missing; no decorations placed")
        self.place_perception_hints(build)
        # MM9 Trigger volumes with Dims as native boxes (polled in the map Lua).
        self.boxes = {}
        for o in source.objects:
            p = o["properties"]
            if o["class"] in ("Trigger",) and any(p.get("Dims") or []):
                centre, dims = np.asarray(p["Pos"], float), np.asarray(p["Dims"], float)
                self.boxes[o["name"]] = native_box(project, centre - dims, centre + dims)
        # DamageBrush volumes: their model's bounds.
        self.damage = {}
        for o in source.objects:
            if o["class"] != "DamageBrush":
                continue
            p = o["properties"]
            points = np.asarray(source.models[o["name"]].points, float)
            current = np.asarray(p.get("Current") or [0, 0, 0], float)
            push = project.native(current) - project.native(np.zeros(3))      # LT vector -> native axes
            self.damage[o["name"]] = {"box": native_box(project, points.min(0), points.max(0)),
                                      "on": bool(p.get("StartOn", 1)), "damage": int(round(float(p.get("Damage", 5)))),
                                      "push": [float(push[0]), float(push[1])]}
        # TouchToOpen doors: a box over the model's top (the party stands on the plate or the elevator's floor).
        self.touch = {}
        for name in TOUCH_OPEN:
            points = np.asarray(source.models[name].points, float)
            low, high = points.min(0), points.max(0)
            self.touch[name] = native_box(project, [low[0], high[1] - 4, low[2]], [high[0], high[1] + 8, high[2]])
        # The tunnel's surfacing (only without swimming, overrides.yml `map: {swim: false}`): its box and the two
        # arrivals on the room's floor.
        self.swim = water.swimming(project)
        x0, x1, z0, z1 = TUNNEL_LT
        self.tunnel = native_box(project, [x0, -300, z0], [x1, SURFACE_BELOW_LT, z1])
        self.surface = {}
        for name, (x, z, query) in (("west", SURFACE_WEST_LT), ("east", SURFACE_EAST_LT)):
            floor = content.floor_at(x, z, query)
            self.surface[name] = project.native([x, floor, z]).round().astype(int).tolist()
            self.surface[name][2] += 2
        self.east_shaft_x = int(round(EAST_SHAFT_X_LT * SCALE))
        # Shooters: position and the point they aim at (MM9 fires along the object's rotation, pitch then yaw).
        self.shooters = {}
        for o in source.objects:
            if o["class"] != "Shooter":
                continue
            p = o["properties"]
            pitch, yaw = float(p["Rotation"][0]), float(p["Rotation"][1])
            forward = np.array([math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch)])
            at = np.asarray(p["Pos"], float)
            self.shooters[o["name"]] = {
                "at": project.native(at).round().astype(int).tolist(),
                "to": project.native(at + forward * 1500.0).round().astype(int).tolist(),
                "damage": int(round(float(p.get("DamageAmt", 5)))), "every": as_float(p.get("ShootInterval")) or 4.0,
                "missile": MISSILES.get(str(p.get("ProjectileName", "")).lower(), "Fire"),
                "projectile": str(p.get("ProjectileName") or "")}

    def scale_lights(self, build) -> None:
        """BLV light colour = MM9 colour x BrightScale (Ruined Temple lesson: MM9 weights each Light by it, 0.2-1.0
        here), times a zone gain fitted to MM9's DAT lightmaps (LIGHT_GAINS); the bake-only lights the same (Training
        Hall lesson)."""
        gains = {}
        for light in build.lights:
            x, y, z = light["position_lt"]
            gain = np.array(DEFAULT_GAIN, float)
            for (x0, y0, z0, x1, y1, z1), rgb in LIGHT_GAINS:
                if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1:
                    gain = np.array(rgb, float)
            gains[light["name"]] = gain * light["bright_scale"]
        for record in build.package.metadata["lights"]:
            factor = gains.get(record["id"], np.ones(3))
            record["color"] = [int(min(255, round(c * f))) for c, f in zip(record["color"], factor)]
        kept = sorted(light["bright_scale"] for light in build.lights if light["kept"])
        typical = kept[len(kept) // 2] if kept else 1.0
        for light in build.lights:
            light["colour_in_blv"] = [int(min(255, round(c * f))) for c, f in zip(light["colour"], gains[light["name"]])]
            if not light["kept"]:
                light["mm9_colour"], light["mm9_bright_scale"] = light["colour"], light["bright_scale"]
                light["colour"] = light["colour_in_blv"]
                light["bright_scale"] = typical

    def place_perception_hints(self, build) -> None:
        """Each PerceptionBrush's visible polygons (Perception.spr) as untouchable translucent faces with a cog
        (Dark Passageway's route); a hint over a lever takes the lever's click."""
        package, source = build.package, build.source
        self.hints, self.hint_difficulty, self.hint_faces = {}, {}, 0
        difficulties = perception_difficulties_by_model_name(source.world)
        events = {group: event for group, (event, _) in self.mover_events.items()}
        for lower in sorted(difficulties, key=lambda n: int(n[len("perceptionbrush"):])):
            k = int(lower[len("perceptionbrush"):])
            name = next(model for model in source.models if model.lower() == lower)
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                rooms = build.content.rooms
                room = room_id(_side_room(rooms, polygon, 1) or _side_room(rooms, polygon, -1)
                               or rooms.owner(polygon.points.mean(0)))
                node = f"TRIGGER_perception_{name}_{i}"
                package.add_polygon(node, polygon, build.stats)
                package.room_nodes[room].append(node)
                surface = {"id": node[8:], "source_node": node, "flags": ["untouchable"],
                           "cog_number": PERCEPTION_COG + k}
                event = events.get(HINT_TARGET.get(name))
                if event:
                    surface["trigger"] = {"event_id": event, "type": "click"}
                package.metadata["surfaces"].append(surface)
                self.hint_faces += 1
            self.hints[name] = PERCEPTION_COG + k
            self.hint_difficulty[PERCEPTION_COG + k] = difficulties[lower]

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """Chadwick Boorsley (CHADWICK, NPC417.scr), the trial's warden: friendly, immobile, RUDE 417."""
        content, source = build.content, build.source
        o = source.by_name[CHADWICK.lower()]
        base = {"name": "Chadwick Boorsley", "attributes": 0, "hp": 100, "hostility_type": 0,
                "monster_info_id": CHADWICK_ROW, "monster_id": CHADWICK_ROW, "radius": CHADWICK_BODY[0],
                "height": CHADWICK_BODY[1],
                "move_speed": 0}
        record = content.actor(o, base, sector_of_room, friendly=True, floor_query_lt=o["properties"]["Pos"][1] + 24)
        record["mm9_rude_id"] = RUDE_CHADWICK
        record["mm9_source_object_index"] = o["index"]
        record["immobile"] = True
        self.chadwick = {"actor_index": record["actor_index"], "object_index": o["index"]}
        return [record]

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        if not getattr(build, "lua_only", False):
            import pickle
            state = {"hooks": dict(self.__dict__), "movers": build.movers, "report": build.content.report}
            (build.project.work / "lua_state.pkl").write_bytes(pickle.dumps(state))
        script = lua.Script(build, "Dungeon of Secrets")
        script.door = {name.replace(" ", "_"): door for name, door in script.door.items()}
        script.lines[4] = "local DOORS = {" + ", ".join(f"{k} = {v}" for k, v in sorted(script.door.items())) + "}"
        source = build.source
        rules = build.project.overrides["models"]
        groups = {g: ids for g, ids in script.groups.items()}
        # Door groups: DAT model -> group, and each group's MM9 door data (from its first model).
        model_group, door_lines = {}, []
        first_model = {}
        for model, rule in rules.items():
            if isinstance(rule, dict) and source.object_class(model) in ("Door", "RotatingDoor"):
                model_group[model] = rule["group"]
                first_model.setdefault(rule["group"], model)
        # Door objects with no faces (overrides.yml skip: MM9's invisible carriers) still take and send messages.
        for model, rule in rules.items():
            if rule == "skip" and source.object_class(model) in ("Door", "RotatingDoor"):
                group = model.replace(" ", "_")
                model_group[model] = group
                first_model.setdefault(group, model)
                groups.setdefault(group, [])
        for group, model in sorted(first_model.items()):
            p = source.properties(model)
            rotating = source.object_class(model) == "RotatingDoor"
            travel = (max(abs(float(a)) for a in p["RotationAngles"]) if rotating else float(p.get("MoveDist", 0)))
            speed = float(p.get("Speed", 50) or 50)
            closing = float(p.get("ClosingSpeed", speed) or speed)
            on_open = messages(p, "OpenTriggerTarget", "OpenTrigger", 0, 3)
            on_close = messages(p, "CloseTriggerTarget", "CloseTrigger", 0, 3)
            double = model_group.get(str(p.get("DoubleDoorName") or ""))
            door_lines.append(
                f"    {group} = {{ids = {{{', '.join(map(str, groups[group]))}}}, open = {travel / speed:.3f}, "
                f"close = {travel / closing:.3f}, wait = {float(p.get('CloseWaitTime', 0) or 0):.2f}, "
                f"sticky = {'true' if p.get('Sticky') else 'false'}, locked = {'true' if p.get('Locked') else 'false'}, "
                f"double = {lua_str(double) if double else 'nil'}, "
                f"onOpen = {{{', '.join('{' + lua_str(t) + ', ' + lua_str(m) + '}' for t, m in on_open)}}}, "
                f"onClose = {{{', '.join('{' + lua_str(t) + ', ' + lua_str(m) + '}' for t, m in on_close)}}}}},"
                f"   -- {model}")
        # Triggers: box (polled), StartOn, PlayerTriggerable, SendDelay, ActivationCount and messages 1-10.
        trigger_lines, kinds = [], {}
        for o in source.objects:
            p, name = o["properties"], o["name"]
            if o["class"] == "Trigger":
                kinds[name] = "trigger"
                box = self.boxes.get(name)
                count = int(round(as_float(p.get("ActivationCount"))))
                msgs = messages(p, "TargetName", "MessageName", 1, 10)
                trigger_lines.append(
                    f"    [{lua_str(name)}] = {{box = {lua_box(box) if box else 'nil'}, "
                    f"on = {'true' if p.get('StartOn', 1) else 'false'}, "
                    f"touch = {'true' if p.get('PlayerTriggerable', 1) and box else 'false'}, "
                    f"delay = {float(p.get('SendDelay', 0) or 0):.2f}, count = {count}, "
                    f"msgs = {{{', '.join('{' + lua_str(t) + ', ' + lua_str(m) + '}' for t, m in msgs)}}}}},")
            elif o["class"] == "Shooter":
                kinds[name] = "shooter"
            elif o["class"] == "DamageBrush":
                kinds[name] = "damage"
            elif o["class"] == "RotatingBrush":
                kinds[name] = "saw"
        for model in model_group:
            if kinds.get(model) != "saw":       # a saw riding its trap is a spinner, not a door of its group
                kinds[model] = "door"
        kinds[CHADWICK] = "npc"
        self.unmatched_targets = sorted({t for o in source.objects for t, _ in
                                         messages(o["properties"], "TargetName", "MessageName", 1, 10)
                                         + messages(o["properties"], "OpenTriggerTarget", "OpenTrigger", 0, 3)
                                         + messages(o["properties"], "CloseTriggerTarget", "CloseTrigger", 0, 3)
                                         if t not in kinds})
        shooter_lines = [f"    [{lua_str(n)}] = {{at = {lua.point(s['at'])}, to = {lua.point(s['to'])}, "
                         f"damage = {s['damage']}, every = {s['every']:.2f}, missile = {lua_str(s['missile'])}, "
                         f"projectile = {lua_str(s['projectile'])}}},"
                         for n, s in sorted(self.shooters.items())]
        damage_lines = [f"    [{lua_str(n)}] = {{box = {lua_box(d['box'])}, on = {'true' if d['on'] else 'false'}, "
                        f"damage = {d['damage']}, push = {{{d['push'][0]:.0f}, {d['push'][1]:.0f}}}}},"
                        for n, d in sorted(self.damage.items())]
        touch_lines = [f"    [{lua_str(model_group[n])}] = {lua_box(b)},   -- {n}" for n, b in sorted(self.touch.items())]
        click_lines = []
        for k, group in enumerate(CLICKABLE):
            click_lines.append(f"handlers[{EV_CLICK_BASE + k}] = function() use({lua_str(group)}) end")
            script.registrations.append((EV_CLICK_BASE + k, "Lever" if "lever" in group or "button" in group else "Door",
                                         "Lever" if "lever" in group or "button" in group else "Door", "event"))
        hint_lines = [f"    {{cog = {cog}, need = {self.hint_difficulty[cog]}}},"
                      for cog in sorted(self.hint_difficulty)]

        lines = [
            "local function key(n) return (string.gsub(n, \"[^%w]\", \"_\")) end   -- a DAT name as a map variable name",
            "local function hurt(amount) evt.DamagePlayer(Players.All, const.Damage.Physical, amount) end",
            "",
            "-- MM9 Door / RotatingDoor data (overrides.yml groups): door ids, open and close seconds (MoveDist or",
            "-- RotationAngles over Speed / ClosingSpeed), CloseWaitTime, Sticky, Locked, DoubleDoorName and Open/CloseTriggers.",
            "local DOOR = {", *door_lines, "}",
            "local MODEL_GROUP = {" + ", ".join(f"[{lua_str(m)}] = {lua_str(g)}" for m, g in sorted(model_group.items())) + "}",
            "local KIND = {" + ", ".join(f"[{lua_str(n)}] = \"{k}\"" for n, k in sorted(kinds.items())) + "}",
            "local TRIGGER = {", *trigger_lines, "}",
            "local SHOOTER = {", *shooter_lines, "}",
            "local DAMAGE = {", *damage_lines, "}",
            "local TOUCH = {", *touch_lines, "}",
            "local HINTS = {", *hint_lines, "}",
            f"local TUNNEL = {lua_box(self.tunnel)}",
            f"local SURFACE_WEST, SURFACE_EAST = {lua.point(self.surface['west'])}, {lua.point(self.surface['east'])}",
            "",
            "-- A scheduler on the poll (MM9's delays): after(seconds, fn). The poll re-arms itself every 0.1 s and",
            "-- keeps that period (a timer's restart of itself counts from its alarm), so the clock is its ticks.",
            "local tick, tasks, clock, nextHints = 0, {}, 0, 3",
            "local function after(seconds, fn)",
            "    table.insert(tasks, {at = clock + math.max(0.05, seconds), fn = fn})",
            "end",
            "local send",
            "local function run(list) if list then for _, m in ipairs(list) do send(m[1], m[2]) end end end",
            "",
            "-- Doors (MM9 DoorBase): state 0 shut, 1 opening, 2 open, 3 closing (map variables S<group>), locks L<group>.",
            "-- A locked door ignores open and close (from messages and clicks alike: a timer lever's lock holds its axe",
            "-- trap). Open/CloseTriggers go out when the door has finished moving; a door that is not Sticky closes",
            "-- CloseWaitTime after it opened (unless locked then); a DoubleDoorName partner moves with it.",
            "local seq = {}",
            "local function state(g) return var(\"S\" .. g) end",
            "local function locked(g) return var(\"L\" .. g) == 1 end",
            "local doorOpen, doorClose",
            "doorOpen = function(g, partner)",
            "    local d = DOOR[g]",
            "    if d == nil or locked(g) then return end",
            "    local s = state(g)",
            "    if s == 1 or s == 2 then return end",
            "    for _, id in ipairs(d.ids) do evt.SetDoorState(id, DoorAction.Open) end",
            "    set(\"S\" .. g, 1)",
            "    seq[g] = (seq[g] or 0) + 1",
            "    local mine = seq[g]",
            "    after(d.open, function()",
            "        if seq[g] ~= mine then return end",
            "        set(\"S\" .. g, 2)",
            "        set(\"Opened\" .. g, var(\"Opened\" .. g) + 1)",
            "        run(d.onOpen)",
            "        if not d.sticky then after(d.wait, function() if seq[g] == mine then doorClose(g) end end) end",
            "    end)",
            "    if d.double ~= nil and not partner then doorOpen(d.double, true) end",
            "end",
            "doorClose = function(g, partner)",
            "    local d = DOOR[g]",
            "    if d == nil or locked(g) then return end",
            "    local s = state(g)",
            "    if s == 0 or s == 3 then return end",
            "    for _, id in ipairs(d.ids) do evt.SetDoorState(id, DoorAction.Close) end",
            "    set(\"S\" .. g, 3)",
            "    seq[g] = (seq[g] or 0) + 1",
            "    local mine = seq[g]",
            "    after(d.close, function()",
            "        if seq[g] ~= mine then return end",
            "        set(\"S\" .. g, 0)",
            "        run(d.onClose)",
            "    end)",
            "    if d.double ~= nil and not partner then doorClose(d.double, true) end",
            "end",
            "local function toggle(g) local s = state(g) if s == 0 or s == 3 then doorOpen(g) else doorClose(g) end end",
            "-- A click (MM9 PushOpen): a locked door jiggles; an open lever or door that is not Sticky closes again.",
            "local function use(g)",
            "    if locked(g) then evt.StatusText(\"Locked\") return end",
            "    set(\"Used\" .. g, var(\"Used\" .. g) + 1)",
            "    toggle(g)",
            "end",
            "",
            "-- Shooters (MM9 Shooter: ProjectileName, DamageAmt, ShootInterval, aimed along the object's rotation): on, a",
            "-- shot at once and one every ShootInterval until off; a shot strikes the party in its path (strikesParty).",
            "local firing = {}",
            "local function fire(name)",
            "    local s = SHOOTER[name]",
            "    if evt.FireMissile(s.missile, s.at[1], s.at[2], s.at[3], s.to[1], s.to[2], s.to[3], s.damage, s.missile, 0, 0, true) then",
            "        MM9.launchSound(s.projectile, s.at[1], s.at[2], s.at[3])",
            "    end",
            "    set(\"Shots\", var(\"Shots\") + 1)",
            "    set(\"Shot\" .. key(name), var(\"Shot\" .. key(name)) + 1)",
            "end",
            "",
            "-- DamageBrush knockbacks (Damage, Current): while on, the party in the box takes Damage once and is thrown",
            f"-- along Current (evt.PushParty: Current's speed, at most {PUSH_MAX_SPEED}, for {PUSH_SECONDS} s).",
            "local hitBy = {}",
            "local function damageOn(name) return var(\"D\" .. key(name)) == 1 or (var(\"D\" .. key(name)) == 0 and DAMAGE[name].on) end",
            "",
            "-- Chadwick (NPC417.scr): DoTrap (key " + str(KEY_TRAPPED) + " while the trial runs, key " + str(KEY_TRIAL)
            + "), RemoveTrap (the entrance button:",
            "-- the trap mark goes), done (the exit gate: with no trap, key " + str(KEY_CLEAN) + " and the quest sound).",
            "local function chadwick(msg)",
            f"    if MM9.hasKey({KEY_TRIAL}) == 0 then return end",
            f"    if msg == \"dotrap\" then set(\"Trap\", 1) set(\"Traps\", var(\"Traps\") + 1) MM9.giveKey({KEY_TRAPPED})",
            f"    elseif msg == \"removetrap\" then set(\"Trap\", 0) MM9.takeKey({KEY_TRAPPED})",
            f"    elseif msg == \"done\" and var(\"Trap\") == 0 then MM9.giveKey({KEY_CLEAN}) MM9.playSound(\"sounds/events/quest.wav\") end",
            "end",
            "",
            "-- Triggers (MM9 Trigger): enabled from StartOn (T<name>: 1 on, 2 off); a touch (any part of the party in the box,",
            "-- PlayerTriggerable) or a 'trigger' message fires an enabled trigger with no activation pending; SendDelay",
            "-- delays the messages; ActivationCount limits touches (on and trigger reset the count).",
            "local pending = {}",
            "local function triggerOn(name)",
            "    local s = var(\"T\" .. key(name))",
            "    if s == 0 then return TRIGGER[name].on end",
            "    return s == 1",
            "end",
            "local function fireTrigger(name, touched)",
            "    local t = TRIGGER[name]",
            "    if t == nil or not triggerOn(name) or pending[name] then return end",
            "    if touched and t.count > 0 and var(\"C\" .. key(name)) >= t.count then return end",
            "    if not touched then set(\"C\" .. key(name), 0) end",
            "    pending[name] = true",
            "    after(t.delay, function()",
            "        pending[name] = nil",
            "        set(\"C\" .. key(name), var(\"C\" .. key(name)) + 1)",
            "        set(\"Fired\" .. key(name), var(\"Fired\" .. key(name)) + 1)",
            "        run(t.msgs)",
            "    end)",
            "end",
            "",
            "-- The dispatcher: MM9's object messages (target, message) as the DAT links them; targets the DAT does not have",
            "-- (rat, ratnormal ... the cut rat cameo, knockback25-29) are ignored, as MM9 ignores them.",
            "send = function(target, msg)",
            "    local kind = KIND[target]",
            "    msg = string.lower(msg)",
            "    if kind == \"trigger\" then",
            "        if msg == \"on\" then set(\"T\" .. key(target), 1) set(\"C\" .. key(target), 0)",
            "        elseif msg == \"off\" then set(\"T\" .. key(target), 2)",
            "        elseif msg == \"trigger\" then fireTrigger(target, false) end",
            "    elseif kind == \"door\" then",
            "        local g = MODEL_GROUP[target]",
            "        if msg == \"open\" then doorOpen(g)",
            "        elseif msg == \"close\" then doorClose(g)",
            "        elseif msg == \"toggle\" or msg == \"use\" or msg == \"trigger\" then toggle(g)",
            "        elseif msg == \"lock\" then set(\"L\" .. g, 1)",
            "        elseif msg == \"unlock\" then set(\"L\" .. g, 0) end",
            "    elseif kind == \"shooter\" then",
            "        if msg == \"on\" then if firing[target] == nil then fire(target) firing[target] = clock + "
            "SHOOTER[target].every end",
            "        elseif msg == \"off\" then firing[target] = nil end",
            "    elseif kind == \"damage\" then",
            "        if msg == \"on\" then set(\"D\" .. key(target), 1) hitBy[target] = nil",
            "        elseif msg == \"off\" then set(\"D\" .. key(target), 2) end",
            "    elseif kind == \"saw\" then   -- RotatingBrush: its mover's spin (scene mover.spin)",
            "        if msg == \"on\" then set(\"Saw\" .. key(target), 1) elseif msg == \"off\" then set(\"Saw\" .. key(target), 0) end",
            "        if DOORS[target] ~= nil and (msg == \"on\" or msg == \"off\" or msg == \"toggle\" or msg == \"reverse\") then",
            "            evt.SpinMover(DOORS[target], msg)",
            "        end",
            "    elseif kind == \"npc\" then",
            f"        if MM9.receives(\"dungeonofsecrets\", target, msg, {self.chadwick['actor_index']}) then chadwick(msg) end",
            "    end",
            "end",
            "",
            "-- Clicks: MM9 PushOpen doors and levers (axe doors, timer levers, the fake levers, the entrance button, the",
            "-- water grate).",
            *click_lines,
            "",
            "-- Chadwick's dialogue exit (NPC417.scr :OnRude, RUDE 417): with key " + str(KEY_REWARDED)
            + " (the reward topic) and no key " + str(KEY_PAID) + ", " + str(REWARD_EXPERIENCE) + " experience,",
            "-- the quest sound and key " + str(KEY_PAID) + ".",
            f"handlers[{50000 + self.chadwick['object_index']}] = function()",
            f"    if MM9.hasKey({KEY_PAID}) == 0 and MM9.hasKey({KEY_REWARDED}) == 1 then",
            f"        {experience_lua(REWARD_EXPERIENCE, KEY_PAID)}",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            f"        MM9.giveKey({KEY_PAID})",
            "    end",
            "end",
            "",
            "-- Perception hints (PerceptionBrush, PerceptionValue): shown to a party with that Perception (checked every",
            "-- 3 s, Dark Passageway's route).",
            "local function showHints()",
            "    for _, h in ipairs(HINTS) do",
            f"        local want = evt.CheckSkill({PERCEPTION_SKILL}, 0, h.need) and 2 or 1",
            "        if var(\"Hint\" .. h.cog) ~= want then",
            "            set(\"Hint\" .. h.cog, want)",
            "            evt.SetFacetBit(h.cog, FacetBits.Invisible, want == 1)",
            "        end",
            "    end",
            "end",
            "",
            "-- The poll (ten times a second): MM9's touch volumes against the party's path since the last poll (a fast",
            "-- party crosses a 4-unit plate trigger in one step), TouchToOpen doors, knockbacks, shooters, waits.",
            "local function crosses(b, ax, ay, az, bx, by, bz)",
            f"    local lo = {{b[1][1] - {PARTY_RADIUS}, b[1][2] - {PARTY_RADIUS}, b[1][3] - {PARTY_HEIGHT}}}",
            f"    local hi = {{b[2][1] + {PARTY_RADIUS}, b[2][2] + {PARTY_RADIUS}, b[2][3]}}",
            "    local a, d = {ax, ay, az}, {bx - ax, by - ay, bz - az}",
            "    local t0, t1 = 0, 1",
            "    for i = 1, 3 do",
            "        if math.abs(d[i]) < 0.001 then",
            "            if a[i] < lo[i] or a[i] > hi[i] then return false end",
            "        else",
            "            local u, v = (lo[i] - a[i]) / d[i], (hi[i] - a[i]) / d[i]",
            "            if u > v then u, v = v, u end",
            "            if u > t0 then t0 = u end",
            "            if v < t1 then t1 = v end",
            "            if t0 > t1 then return false end",
            "        end",
            "    end",
            "    return true",
            "end",
            "local sunk = false",
            "local last, inside = nil, {}   -- a touch fires when the party comes into a box (MM9 touches while it moves)",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.1))",
            "    tick = tick + 1",
            "    clock = tick * 0.1",
            "    set(\"Clock10\", math.floor(clock * 10))",
            "    local x, y, z = evt.GetPartyPosition()",
            "    local px, py, pz = x, y, z",
            "    if last ~= nil and math.abs(last[1] - x) + math.abs(last[2] - y) + math.abs(last[3] - z) < 600 then",
            "        px, py, pz = last[1], last[2], last[3]",
            "    end",
            "    last = {x, y, z}",
            "    for name, t in pairs(TRIGGER) do",
            "        if t.touch then",
            "            local now = crosses(t.box, px, py, pz, x, y, z)",
            "            if now and not inside[name] then fireTrigger(name, true) end",
            "            inside[name] = now",
            "        end",
            "    end",
            "    for g, b in pairs(TOUCH) do",
            "        if state(g) == 0 and not locked(g) and crosses(b, px, py, pz, x, y, z) then doorOpen(g) end",
            "    end",
            "    for name, d in pairs(DAMAGE) do",
            "        if damageOn(name) and not hitBy[name] and crosses(d.box, px, py, pz, x, y, z) then",
            "            hitBy[name] = true",
            "            hurt(d.damage)",
            "            set(\"Knocked\" .. key(name), var(\"Knocked\" .. key(name)) + 1)",
            "            local speed = math.sqrt(d.push[1] * d.push[1] + d.push[2] * d.push[2])",
            "            if speed > 1 then",
            f"                evt.PushParty(d.push[1], d.push[2], math.min(speed, {PUSH_MAX_SPEED}) * {PUSH_SECONDS})",
            "            end",
            "        elseif not damageOn(name) then hitBy[name] = nil end",
            "    end",
            # The submerged tunnel: swum (the shared water rule, dungeon/water.py); with overrides.yml
            # `map: {swim: false}` the old stand-in, a party that sank in comes up beside a shaft.
            *([] if self.swim else [
                "    -- The submerged tunnel (no swimming): a party that sank in comes up beside a shaft.",
                "    local sunkNow = crosses(TUNNEL, x, y, z, x, y, z) and z < TUNNEL[2][3]",
                "    if sunkNow and not sunk then   -- the frame loop applies the move: once per sinking",
                "        local a = SURFACE_WEST",
                f"        if x > {self.east_shaft_x} and state(\"water_grate\") == 2 then a = SURFACE_EAST end",
                "        set(\"Surfaced\", var(\"Surfaced\") + 1)",
                "        evt.StatusText(\"You swim up out of the flooded tunnel.\")",
                "        evt.MoveToMap(a[1], a[2], a[3], 0, 0, 0, 0, 0)",
                "    end",
                "    sunk = sunkNow"]),
            "    for name, at in pairs(firing) do",
            "        if clock >= at then fire(name) firing[name] = clock + SHOOTER[name].every end",
            "    end",
            "    local due = {}",
            "    for i = #tasks, 1, -1 do if tasks[i].at <= clock then table.insert(due, 1, tasks[i].fn) table.remove(tasks, i) end end",
            "    for _, fn in ipairs(due) do fn() end",
            "    if clock >= nextHints then nextHints = clock + 3 showHints() end",
            "end",
            "",
            "-- Map load: the doors' DAT locks once; doors caught moving by a save end where they were going; NPC417.scr :Init",
            f"-- (a fresh trial on every visit: keys {KEY_TRIAL} and {KEY_TRAPPED} go); the hints; the poll.",
            f"handlers[{EV_LOAD}] = function()",
            "    if var(\"Loaded\") == 0 then",
            "        set(\"Loaded\", 1)",
            "        for g, d in pairs(DOOR) do if d.locked then set(\"L\" .. g, 1) end end",
            "    end",
            "    for g, _ in pairs(DOOR) do",
            "        if state(g) == 1 then set(\"S\" .. g, 2) elseif state(g) == 3 then set(\"S\" .. g, 0) end",
            "        if state(g) == 2 and not DOOR[g].sticky and not locked(g) then doorClose(g) end",
            "    end",
            f"    MM9.takeKey({KEY_TRIAL})",
            f"    MM9.takeKey({KEY_TRAPPED})",
            "    set(\"Trap\", 0)",
            "    for _, h in ipairs(HINTS) do set(\"Hint\" .. h.cog, 0) end",
            "    showHints()",
            f"    evt.StartTimer({T_POLL}, seconds(0.1))",
            "end",
        ]
        script.add(lines, (EV_LOAD, "Map load", None), (T_POLL, "Poll", None, "timer"), 
                   (50000 + self.chadwick["object_index"], "Chadwick", None))
        return script.finish(on_load=[EV_LOAD])

    # --- scene ------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """The perception hints drawn translucent; MM9's non-solid movers untouchable (face attribute overrides on
        their compiled faces); no saving in here."""
        # No saving in Chadwick's course (the user, 2026-11-09, as in the Arena): its map-load handler starts a fresh
        # trial on every load (NPC417.scr :Init; MM9 kept the trial on a full save load, which our map load cannot
        # tell apart), so a save made mid-course restarted the trial when loaded.
        scene["runtime_restrictions"] = {"allow_save_game": False, "allow_lloyds_beacon": False}
        sys.path.insert(0, str(ROOT))
        import yaml
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        hint_alias = build.source.aliases["sprites\\perception.spr"]["alias"].lower()
        hints = [f["index"] for f in blv["faces"]
                 if str(f.get("texture_name", "")).lower() == hint_alias and not f["is_portal"]]
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        scene.setdefault("translucent_faces", []).append(
            {"faces": sorted(hints), "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        water_alias = build.source.aliases[WATER[2]]["alias"].lower()
        water = [f["index"] for f in blv["faces"]
                 if str(f.get("texture_name", "")).lower() == water_alias and not f["is_portal"]]
        scene["translucent_faces"].append({"faces": sorted(water), "opacity": WATER[3], "tint": [1.0, 1.0, 1.0],
                                           "two_sided": True})
        build.stats["water_faces"] = len(water)
        # MM9's Clouds1 pane in the window between the lever room and its sealed east twin (WorldObject0, a 4 LT box of
        # Invisible.dtx with one Clouds1 face): drawn two-sided at full opacity, as the three skymarker faces by the exit
        # (the tour's view from the twin, which no party reaches, saw its back).
        sky_alias = build.source.aliases["textures\\skybox\\clouds1.dtx"]["alias"].lower() \
            if "textures\\skybox\\clouds1.dtx" in build.source.aliases else "clouvksjd0"
        sky = [f["index"] for f in blv["faces"] if str(f.get("texture_name", "")).lower() == sky_alias and not f["is_portal"]]
        scene["translucent_faces"].append({"faces": sorted(sky), "opacity": 1.0, "tint": [1.0, 1.0, 1.0],
                                           "two_sided": True})
        build.stats["sky_faces"] = len(sky)
        doors = yaml.safe_load((build.runtime / f"{build.project.stem}.doors.yml").read_text()) or []
        faces_of = {d["door_id"]: d["face_ids"] for d in doors}
        attributes = {f["index"]: int(f["attributes"]) for f in blv["faces"]}
        non_solid = set()
        for m in build.movers:
            if any(model in NON_SOLID for model in m["dat_models"]):
                non_solid |= set(faces_of.get(m["door_id"], []))
        scene["initial_state"].setdefault("face_attribute_overrides", []).extend(
            {"face_index": f, "legacy_attributes": attributes[f] | UNTOUCHABLE_FACE} for f in sorted(non_solid))
        build.stats["non_solid_mover_faces"] = len(non_solid)
        build.stats["perception_faces"] = len(hints)
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)

    def report(self, build) -> dict:
        return {"scripted": {"boxes": getattr(self, "boxes", {}), "damage": getattr(self, "damage", {}),
                             "touch": getattr(self, "touch", {}), "shooters": getattr(self, "shooters", {}),
                             "hints": getattr(self, "hints", {}), "chadwick": getattr(self, "chadwick", {}),
                             "unmatched_targets": getattr(self, "unmatched_targets", [])}}


def lua_only() -> int:
    """Regenerate and install only the map Lua from the last build's state (work/lua_state.pkl)."""
    import pickle
    from types import SimpleNamespace
    from dungeon.source import Project, Source
    import review_root
    state = pickle.loads((PROJECT / "work/lua_state.pkl").read_bytes())
    hooks = DungeonOfSecrets()
    hooks.__dict__.update(state["hooks"])
    project = Project.load(PROJECT)
    source = Source(project)
    DungeonOfSecrets.adjust_source(source)
    build = SimpleNamespace(project=project, source=source, movers=state["movers"], hooks=hooks,
                            content=SimpleNamespace(report=state["report"]), runtime=project.work / "runtime",
                            lua_only=True)
    text = hooks.map_script(build)
    (build.runtime / f"{project.stem}.lua").write_text(text)
    review_root.install_file(Path("worlds/mm9/events/maps") / f"{project.stem}.lua", build.runtime / f"{project.stem}.lua")
    print("installed", project.stem + ".lua", len(text.splitlines()), "lines")
    return 0


if __name__ == "__main__":
    if "--lua" in sys.argv:
        sys.exit(lua_only())
    sys.exit(dungeon.main(PROJECT, DungeonOfSecrets()))
