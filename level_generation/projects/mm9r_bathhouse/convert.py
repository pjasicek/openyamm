#!/usr/bin/env python3
"""
The Bathhouse (Arslegard), MM9 rework: MM9's BATHHOUSE.dat as a native indoor map (BLV) on the shared dungeon converter
(../mm9r_common/dungeon/, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_bathhouse/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_bathhouse/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, archway cuts, the ladder and texture substitutes; this file the water (README
"Water": wading floors and the dives that stand in for MM9's swim), the population (props.json from
../../props/mm9_bathhouse_claude, 21 monsters) and MM9's scripted objects as native Lua (README "Scripted objects"):
Ebora and her concubines (EboraBath.scr, EboraConcubine.scr, the EboraGossip trigger), the furnace (BathFurnace.scr,
the gas valve GasRelease0, the pistons, Fatc.scr, FurnaceWarning.scr, DP2steam.scr), the drain (Switch0,
DrainWater.scr, the propeller, the locked Door6/7), the steam vents (SteamVent.scr, SteamVentDB.scr), the spore
spawns (StepTrigger0-2, SpawnMgr.scr, SpawnLoc.scr) and the two letters (BookLetter.scr).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from dungeon import lua, water  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from quest_xp import experience_lua  # noqa: E402
import cutscenes  # noqa: E402
sys.path.insert(0, str(PROJECT))
import bath_cinematics  # noqa: E402

PROPS = PROJECT / "props.json"
POOL = "water:pool"                 # overrides.yml textures: MM9's Water115.spr, first frame (WATEQOBX0Z)

# --- Water (README "Water"). Swimming (the shared rule, `water.swimming`; 2026-11-06,
# devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md):
# MM9's 12 water volumes are the scene's `water_volumes` (the shared build, ../mm9r_common/dungeon/water.py); every
# surface below is non-solid at its volume's top, the party swims down the pools' shafts and through the flooded tunnels
# as in MM9, and the dives (DIVES) are not built. With overrides.yml `map: {swim: false}` (the build before swimming)
# volume -> treatment:
#   nonsolid: the top of the volume as an untouchable translucent face; the party wades on the bottom (shallow, or with
#             a ramp out);
#   wading:   the top as a solid translucent face the party walks on (a basin it could not climb out of, a shaft);
#   the deep tunnels (BlueWater8, 10, 14 and the shafts under the pools) get nothing: no air over them, out of reach.
WATER = {      # volume: (kind, (LT x range, z range) or None for the volume's box, surface LT y or None for its top)
    "BlueWater0": ("nonsolid", None, None),          # the great hall's pool: 6 LT over its floor, 3 under the hall's
    "BlueWater6": ("nonsolid", None, None),          # Ebora's tub: sloped sides to walk out
    # The wading floors lie flush with the floor round them over the basin only (a step of a few LT would be a strip
    # of wall facing the sealed water below, which no room draws).
    "BlueWater1": ("wading", ((311, 544), (-1796, -1401)), -48.0),        # the south-west pool: 40 LT, no steps
    "WaterthatBoilsA": ("wading", ((1740, 2012), (-1920, -1492)), -48.0),  # pool A: 56 LT basin over a 400 LT shaft
    "WaterthatBoilsB": ("wading", ((756, 1136), (-1912, -1145)), 0.0),     # pool B: the same
    "BlueWater9": ("wading", ((3220, 3504), (-529, 135)), -492.0),  # the switch room's pool and the tunnel mouth
    "BlueWater4": ("wading", ((1800, 1892), (-625, 39)), -492.0),   # the channels beside the chamber under the hall
    "BlueWater7": ("wading", ((944, 1040), (-625, 39)), -492.0),
}
UNTOUCHABLE = 0x20000000          # BLV face attribute (MM7 FACE_UNTOUCHABLE)
# MM9 draws a volume's ShowSurface with SurfaceAlpha (0.5 here; BlueWater2 0.7) over Water115.spr, whose frame carries its
# own alpha (DTX PREFER4444; mean 0.42, 52-255): the ripples. The face's opacity multiplies the texture's alpha in the
# shader, so opacity 1 gives a mean of 0.42, MM9's SurfaceAlpha level with the ripple pattern (0.5 x 0.42 = 0.21, the
# literal product, read as the tinted bed alone: orchestrator review 2026-10-30).
SURFACE_OPACITY = 1.0
# MM9's swim (pool shaft -> flooded tunnels -> the dry chamber under the hall -> tunnel -> the switch room's pool) as
# moves between the dry places: a pad on the water over each shaft or tunnel mouth. name: (pad LT box low, high, the
# arrival LT point on the floor, facing degrees (native yaw), text).
DIVES = {
    "DivePoolA": ((1800, -1640), (1892, -1588), (1720, -492, -560), 90,
                  "You dive into the pool and swim down the shaft and north along the flooded tunnel."),
    "DivePoolB": ((944, -1485), (1040, -1429), (1120, -492, -560), 90,
                  "You dive into the pool and swim down the shaft and north along the flooded tunnel."),
    "DiveChamberA": ((1800, -625), (1892, -575), (1700, -48, -1560), 0,
                     "You dive and swim back south through the flooded tunnel to the boiling pool."),
    "DiveChamberB": ((944, -625), (1040, -575), (720, 0, -1560), 0,
                     "You dive and swim back south through the flooded tunnel."),
    "DiveChamberEast": ((1800, -529), (1892, -433), (3600, -492, -300), 90,
                        "You dive and swim east through the long flooded tunnel."),
    "DiveSwitchRoom": ((3220, -529), (3300, -433), (1720, -492, -480), 180,
                       "You dive and swim west through the long flooded tunnel."),
}
# The drained room (BlueWater2, DrainWater.scr): MM9's stairs lead under its surface (the party swims in). Here the party
# walks its bed; the surface is a non-solid translucent mover that sinks to its floor marker when Switch0 drains it
# (MoveToPOS at 10 LT/s: 30 s). Over the low corridor west of x 4256 the surface lies inside the ceiling.
# Lights trimmed further against MM9's own lightmaps (hue_vs_lightmaps.py, zone "east corridor north end"): the yellow
# Light108 (186/194/18, BrightScale 0.4, radius 400 LT) made the corridor's end yellow where MM9's brightest texels are
# teal (B/R 1.49 against our 0.78, hue 76 degrees off): Cycles' inverse-square point light piles it near the light.
LIGHT_TRIM = {"Light108": 0.45}
FLOOD = {"top": -126.0, "bottom": -432.0, "speed_lt": 10.0}
# The surface pieces: node -> (LT x range, z range, an LT point in the room that owns it): the drained room, and its
# stairs, whose lower steps MM9 floods (the stair corridor is its own room).
FLOOD_PARTS = {"MECH_FloodWater": ((4256, 5760), (-768, 448), (5000, -300, -150)),
               "MECH_FloodWaterStairs": ((3884, 4068), (-490, -60), (3976, -200, -300))}
PROPELLER_DEGREES = 360.0
SWIM_VOLUMES = ("BlueWater0", "BlueWater1", "BlueWater2", "BlueWater4", "BlueWater6", "BlueWater7", "BlueWater8",
                "BlueWater9", "BlueWater10", "BlueWater14", "WaterthatBoilsA", "WaterthatBoilsB")   # swimming
DRAIN_SECONDS = 30

# --- Events, timers, cogs, groups -------------------------------------------------------------------------------------
EV_LOAD, EV_VALVE, EV_SWITCH, EV_DOOR67, EV_WARNING, EV_GOSSIP = 1, 90, 91, 92, 93, 94
EV_LETTER = {"Prop8": 95, "Prop7": 96}
EV_STEP = {"StepTrigger0": 150, "StepTrigger1": 151, "StepTrigger2": 152}
EV_DIVE = {name: 160 + k for k, name in enumerate(DIVES)}
DAMAGE_HOOK, KILL_HOOK, EV_FLAP = 97, 98, 99
T_POLL, T_FATC = 300, 301
COG_FIRE = {"Fire1": 400, "Fire4": 401}          # the furnace's big fires, on with the valve
GROUP_SPAWN = {"SpawnLoc0": 60, "SpawnLoc1": 61}  # the hidden spores of SpawnMgr.scr
SPAWNS_PER_TRIGGER = 2                            # each StepTrigger sends `spawn` twice to its SpawnLoc
STEP_TARGET = {"StepTrigger0": "SpawnLoc0", "StepTrigger1": "SpawnLoc0", "StepTrigger2": "SpawnLoc1"}
# BookLetter.scr DoLetter: rows of MM9's BOOK AND SCROLL TEXT.csv.
LETTER_ROWS = {"Prop8": 500, "Prop7": 501}
# Ebora (EboraBath.scr): SetPropNumber CanDamage FALSE; three dead concubines send her off in a column of fire and
# give key 349 and 80 000 experience to a party on Gostaf's errand (key 348, NPC339.rude), else key 350.
KEY_ERRAND, KEY_CLEANED, KEY_CLEANED_UNASKED, EBORA_EXPERIENCE = 348, 349, 350, 80000
EBORA_ROW = 9301


def ebora_hp() -> int:
    """Ebora's hit points from the live MM9 monster table (the balance pass revises them; 1768 before 2026-11-06)."""
    for line in (ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt").read_text(encoding="latin-1").split("\n"):
        cells = line.split("\t")
        if cells[0] == str(EBORA_ROW):
            return int(cells[4])
    raise SystemExit(f"monster_data.txt has no row {EBORA_ROW}")


# MM9's RolloverText lines (MMIXSCRIPTTEXT.csv, mm9r_common/script_text.py): EboraBath.scr :OnGossip shows rows 2-5
# (nGossip 2, once each), :DeadConcubine row 8 + the dead count (9, 10); FurnaceWarning.scr :OnUse row 1.
from script_text import rollover_text  # noqa: E402
GOSSIP = [rollover_text(n) for n in range(2, 6)]
TAUNTS = [rollover_text(8 + dead) for dead in (1, 2)]
WARNING = rollover_text(1)
# The steam vents (SteamVent.scr: 3 s on, 3 s off; SteamVentDB.scr moves each DamageBrush, Damage 200, onto the vent
# while it blows). MM9's 200 a second is against MM9's hit points; native: VENT_DAMAGE fire damage a second.
VENTS = {"SteamVent0": "DamageBrush0", "SteamVent1": "DamageBrush1", "SteamVent2": "DamageBrush2",
         "SteamVent3": "DamageBrush3"}
VENT_ON, VENT_OFF, VENT_DAMAGE = 3, 3, 20
# Steam over the boiling water (MM9 Fire objects with white smoke and no flame): mm9:smokestack puffs near the party.
STEAM_ALWAYS = ["BoilingSteam2", "BoilingSteam3", "BoilingSteam4", "BoilingSteam5", "BoilingSteam6", "BoilingSteam7",
                "BoilingSteam8", "BoilingSteam9"]
STEAM_FURNACE = ["BoilingSteam0", "BoilingSteam1"]      # turned on by BathFurnace.scr's `turnon`
STEAM_EFFECT, STEAM_SCALE, STEAM_RANGE = "mm9:smokestack", 0.35, 2500
FIRES = {"Fire2": "mm9_gatefire_x8", "Fire3": "mm9_gatefire_x8",       # FireScale 1, burning from the start
         "Fire1": "mm9_gatefire_x33", "Fire4": "mm9_gatefire_x33"}     # FireScale 4, with the valve (hidden until)
# LesserDemon.scr p0 1 (LesserDemon0's ScriptParams "1"): :OnDeathDone spawns "GreaterDemon ScriptParams 1" at its body
GREATER_DEMON = 9242                # MM9 MONSTERS.txt row 242 Greater Demon
GREATER_ON_DEATH = ("LesserDemon0",)
MONSTERS_TXT = ROOT / "mm9/extracted/DATA/DATA/MONSTERS.txt"
CLASS_ROW = {"ColloidalWarrior": "Colloidal Warrior", "ColloidalSoldier": "Colloidal Soldier",
             "ColloidalGuardian": "Colloidal Guardian", "JellySpore": "Jellyspore", "SuccEbora": "Ebora",
             "Concubine": "Concubine", "LesserDemon": "Lesser Demon"}


def surface(x0, x1, z0, z1, y: float, model: str, role: str, source) -> Polygon:
    """A horizontal face over an LT box, front upward, MM9's pool texture at one texel per LT."""
    ring = np.array([[x0, y, z0], [x0, y, z1], [x1, y, z1], [x1, y, z0]], float)
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], POOL,
                      (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), 0x1088, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], POOL, polygon.mapping, 0x1088,
                          model, role)
    alias = source.aliases[POOL]
    polygon.notes.update(width=alias["width"], height=alias["height"])
    return polygon


def split_at(polygon: Polygon, y: float) -> list:
    """A convex polygon cut by the horizontal plane at LT height y (both halves; the polygon itself if not crossed)."""
    points = polygon.points
    d = points[:, 1] - y
    if d.max() <= 0.01 or d.min() >= -0.01:
        return [polygon]
    halves = ([], [])
    count = len(points)
    for i in range(count):
        a, b = points[i], points[(i + 1) % count]
        da, db = d[i], d[(i + 1) % count]
        (halves[0] if da >= 0 else halves[1]).append(a)
        if (da > 0 > db) or (da < 0 < db):
            cut = a + (b - a) * (da / (da - db))
            halves[0].append(cut)
            halves[1].append(cut)
    out = []
    for ring in halves:
        if len(ring) >= 3:
            ring = np.array(ring, float)
            out.append(Polygon(ring, [tuple(np.round(q, 1)) for q in ring], polygon.texture, polygon.mapping,
                               polygon.flags, polygon.model, polygon.role, notes=dict(polygon.notes)))
    return [q for q in out if q.area > 1.0] or [polygon]


def mm9_bodies() -> dict:
    """MM9's monster bodies: class -> (radius, height) in native units for an object Scale of 1, from the ABC's first
    AnimBinding extents (half sizes, LT) x MONSTERS.txt Scale x 2.56 (AGENT_BRIEF: bodies carry MM9's sizes)."""
    sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
    from convert_abc_model import read_abc
    rows = {r["Monster Name"]: r for r in csv.DictReader(MONSTERS_TXT.open(encoding="latin-1"), delimiter="\t")}
    models = {p.name.lower(): p for p in (ROOT / "mm9/extracted/MODELS/MODELS").rglob("*.abc")}
    models.update({p.name.lower(): p for p in (ROOT / "mm9/extracted/MODELS/MODELS").rglob("*.ABC")})
    out = {}
    for cls, name in CLASS_ROW.items():
        row = rows[name]
        ex, ey, _ = read_abc(models[row["ModelName"].lower()]).anim_bindings[0].extents
        scale = float(row["Scale"] or 1)
        out[cls] = (ex * scale * SCALE, 2 * ey * scale * SCALE)
    return out


def letters() -> dict:
    rows = {}
    with (ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv").open(encoding="latin-1", newline="") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip().isdigit():
                rows[int(row[0])] = (row[1], row[2])
    return {name: rows[number] for name, number in LETTER_ROWS.items()}


def lua_string(text: str) -> str:
    return json.dumps(text)


def swimming(build) -> bool:
    """MM9's water volumes, swum in (the shared rule, dungeon/water.py; module constants, "Water")."""
    return water.swimming(build.project)


class Bathhouse(dungeon.Hooks):
    generator = "mm9r_bathhouse"
    mover_events = {"GasRelease0": (EV_VALVE, "click"), "Switch0": (EV_SWITCH, "click"),
                    "Door67": (EV_DOOR67, "click"), "RotatingDoor0": (EV_FLAP, "click")}
    # BlueWater2's surface is the FloodWater movers (flood_mover), not the shared rule's drawn face (water.drawn_surfaces)
    own_water_surfaces = {"BlueWater2"}

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        source = build.source
        # WaterProp turns 9000 degrees (25 turns over the 30 s drain); a rotating mover turns at most 360: one turn,
        # which the drain's poll drives back and forth while the water sinks (map Lua).
        source.by_name["waterprop"]["properties"]["RotationAngles"] = [0.0, 0.0, PROPELLER_DEGREES]
        # The walls round a wading floor are cut at its height, so the strip of wall just over the water belongs to the
        # room above it and not to the sealed water under it (a black band otherwise: assignment samples a voxel grid).
        swim = swimming(build)
        out = []
        for polygon in polygons:
            if swim:            # one air over and under the surface: no strip of wall faces a sealed water room
                out.append(polygon)
                continue
            pieces = [polygon]
            low, high = polygon.points.min(0), polygon.points.max(0)
            for kind, box, height in WATER.values():
                if kind != "wading" or abs(polygon.normal[1]) > 0.5:
                    continue
                (x0, x1), (z0, z1) = box
                if low[0] <= x1 + 8 and high[0] >= x0 - 8 and low[2] <= z1 + 8 and high[2] >= z0 - 8:
                    pieces = [q for piece in pieces for q in split_at(piece, height)]
            out += pieces
        for model, (kind, box, height) in WATER.items():
            points = np.array(source.models[model].points, float)
            (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
            if box:
                (x0, x1), (z0, z1) = box
            if swim:            # the volume's own top, non-solid: the party swims under it
                out.append(surface(x0, x1, z0, z1, float(points[:, 1].max()), model, "nonsolid", source))
                continue
            y = float(points[:, 1].max()) if height is None else height
            out.append(surface(x0, x1, z0, z1, y, model, "static" if kind == "wading" else "nonsolid", source))
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project, package = build.content, build.source, build.project, build.package
        self.dim_lights(build)
        events = dict(EV_LETTER)
        if PROPS.exists():
            entries = json.loads(PROPS.read_text())
            for entry in entries:
                if entry["source_name"].lower() in content.ids:
                    entry["source_name"] += "_prop"
            placed = project.work / "props_entities.json"
            placed.write_text(json.dumps(entries) + "\n")
            content.props(placed, events=events)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        # The furnace's fires (MM9 Fire objects, flame cards; Fire1/4 hidden until the valve opens).
        for name, decoration in FIRES.items():
            p = source.properties(name)["Pos"]
            floor = content.floor_at(p[0], p[2], p[1] + 10)
            content.entity(name, decoration, project.native([p[0], floor, p[2]]), 0, primary=COG_FIRE.get(name, 0))
        # The warning plate on the furnace (FurnaceWarning.scr: a click shows its text): its faces carry the click.
        node = "TRIGGER_FurnaceWarning"
        for polygon in source.polygons("FurnaceWarning"):
            package.add_polygon(node, polygon, build.stats)
        centre = np.concatenate([p.points for p in source.polygons("FurnaceWarning")]).mean(0)
        package.room_nodes[content.owner(centre + [0, 0, 24])].append(node)
        package.metadata["surfaces"].append({"id": "FurnaceWarning", "source_node": node, "flags": [],
                                             "trigger": {"event_id": EV_WARNING, "type": "click"}})
        # Pads: the spore triggers, Ebora's gossip trigger, the dives (not with swimming: the party swims).
        for name, event in EV_STEP.items():
            t = source.properties(name)
            content.pad(name, t["Pos"], t["Dims"], event)
        t = source.properties("EboraGossip")
        content.pad("EboraGossip", t["Pos"], t["Dims"], EV_GOSSIP)
        for name, (low, high, _, _, _) in ({} if swimming(build) else DIVES).items():
            centre = ((low[0] + high[0]) / 2, 0.0, (low[1] + high[1]) / 2)
            floor = content.floor_at(centre[0], centre[2], 40 if name.startswith("DivePool") else -400)
            content.pad(name, (centre[0], floor + 10, centre[2]), ((high[0] - low[0]) / 2, 10, (high[1] - low[1]) / 2),
                        EV_DIVE[name])
        self.flood_mover(build)

    def dim_lights(self, build) -> None:
        """MM9 authors many of its lights dimmer (BrightScale 0.3-0.8; the map's typical one is 0.7), which a BLV light
        cannot carry: its colour is scaled by BrightScale over the typical one (at most 1), as the bake-only lights' strength
        is (dungeon/lighting.py). Without it the dim lights burnt walls white beside them (Light99 at the drained room's
        stair foot, BrightScale 0.5, 6 LT from the wall)."""
        kept = sorted(light["bright_scale"] for light in build.lights if light["kept"])
        typical = kept[len(kept) // 2]
        scale = {light["name"]: min(1.0, light["bright_scale"] / typical) for light in build.lights if light["kept"]}
        self.dimmed = {}
        for entry in build.package.metadata["lights"]:
            factor = scale.get(entry["id"], 1.0) * LIGHT_TRIM.get(entry["id"], 1.0)
            if factor < 1.0:
                entry["color"] = [int(round(c * factor)) for c in entry["color"]]
                self.dimmed[entry["id"]] = round(factor, 2)
        build.stats["lights_dimmed_by_bright_scale"] = len(self.dimmed)

    def flood_mover(self, build) -> None:
        """The drained room's water: linear movers, non-solid, sinking from MM9's surface to under the floor."""
        package, source = build.package, build.source
        self.flood_doors = []
        length = int(round((FLOOD["top"] - FLOOD["bottom"]) * SCALE))
        speed = int(round(FLOOD["speed_lt"] * SCALE))
        for node, ((x0, x1), (z0, z1), owner_lt) in FLOOD_PARTS.items():
            polygon = surface(x0, x1, z0, z1, FLOOD["top"], "BlueWater2", "static", source)
            package.add_polygon(node, polygon, build.stats)
            owner = build.content.owner(np.array(owner_lt, float))
            package.room_nodes[owner].append(node)
            door_id = max(m["door_id"] for m in build.movers) + 1
            package.metadata["mechanisms"].append({"id": node[5:], "kind": "linear", "source_nodes": [node],
                                                   "door": {"door_id": door_id, "initial_state": "closed",
                                                            "source_pose": "closed", "direction": [0.0, 0.0, 1.0],
                                                            "move_length": length, "open_speed": speed,
                                                            "close_speed": speed}})
            package.metadata["surfaces"].append({"id": node[5:], "source_node": node, "flags": ["untouchable"]})
            build.movers.append({"node": node, "dat_models": ["BlueWater2"], "group": "FloodWater",
                                 "door_id": door_id, "event": 0, "motion": "drain", "room": owner,
                                 "move_length": length, "initial_state": "closed", "doorway": False,
                                 "open_direction": [0.0, 0.0, -1.0], "open_speed": speed, "mm9_class": "BlueWater",
                                 "invisible": False, "glass": None, "mover": None, "extra_rooms": [],
                                 "sounds": {}})          # MM9's flood names no sound (movers.door_sounds)
            self.flood_doors.append(door_id)

    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        # The SuccEbora class has no row in the old importer's replacement table: MM9's Ebora row (301 -> 9301).
        bases["Ebora"] = dict(bases["Concubine1"], name="Ebora", monster_info_id=EBORA_ROW, monster_id=EBORA_ROW,
                              hp=ebora_hp())
        content.report["omitted"] = [o for o in content.report["omitted"] if o["anchor"] != "Ebora"]
        bodies = mm9_bodies()
        out = []
        self.actor_index = {}
        for o in source.objects:
            name, p = o["name"], o["properties"]
            if name not in bases:
                continue
            scale = float(p.get("Scale", 1.0) or 1.0)
            radius, height = bodies[o["class"]]
            changes = {"radius": int(round(radius * scale)), "height": int(round(height * scale))}
            friendly = o["class"] == "SuccEbora"
            record = content.actor(o, bases[name], sector_of_room, friendly=friendly,
                                   floor_query_lt=p["Pos"][1] + 40, **changes)
            if friendly:
                record["immobile"] = True           # EboraBath.scr: she stays in her tub
            self.actor_index[name] = record["actor_index"]
            out.append(record)
        # SpawnMgr.scr's spores: hidden placed Jellyspores at each SpawnLoc (two per `spawn` pair), shown and set hostile
        # by the first StepTrigger.
        template = next(o for o in source.objects if o["class"] == "JellySpore")
        self.spawned = {}
        for loc, group in GROUP_SPAWN.items():
            pos = source.properties(loc)["Pos"]
            for k in range(SPAWNS_PER_TRIGGER):
                clone = dict(template, name=f"{loc}Spore{k}",
                             properties=dict(template["properties"], Pos=[pos[0] + (k * 2 - 1) * 60, pos[1], pos[2]],
                                             Scale=1.0))
                radius, height = bodies["JellySpore"]
                record = content.actor(clone, bases[template["name"]], sector_of_room, group=group, hidden=True,
                                       floor_query_lt=pos[1] + 40, radius=int(round(radius)),
                                       height=int(round(height)))
                self.spawned.setdefault(loc, []).append(record["actor_index"])
                out.append(record)
        return out

    # --- scene ------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """MM9's water surfaces as translucent faces; the drained room's water two-sided (the party walks under it)."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        alias = build.source.aliases[POOL]["alias"].upper()
        flood = [f for d in scene["initial_state"]["doors"] if d["door_id"] in self.flood_doors for f in d["face_ids"]]
        # Only the non-solid surfaces are see-through: under a wading floor lies a sealed, portal-less tunnel room the
        # renderer never draws from above, so a solid surface stays opaque (Beethoven's cavern does the same).
        nonsolid = {f["index"] for f in blv["faces"] if f["attributes"] & UNTOUCHABLE}
        water = [f["index"] for f in blv["faces"]
                 if not f["is_portal"] and f["texture_name"].upper() == alias and f["index"] not in set(flood)
                 and f["index"] in nonsolid]
        entries = scene.setdefault("translucent_faces", [])
        entries.append({"faces": sorted(water), "opacity": SURFACE_OPACITY, "tint": [1.0, 1.0, 1.0],
                        "two_sided": False})
        entries.append({"faces": sorted(flood), "opacity": 1.0, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        build.stats["water_faces"] = len(water)
        build.stats["flood_faces"] = len(flood)
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)
        if swimming(build):
            # The shared build's volumes (dungeon/water.py): all 12, the drained room's BlueWater2 on the FloodWater
            # movers (both pieces sink together: its top follows the door, which starts at MM9's full surface).
            volumes = {v["id"]: v for v in scene.get("water_volumes", [])}
            if sorted(volumes) != sorted(SWIM_VOLUMES) or volumes["BlueWater2"].get("mover_door_id") not in self.flood_doors:
                raise SystemExit(f"water volumes: {sorted(volumes)} (BlueWater2 door "
                                 f"{volumes.get('BlueWater2', {}).get('mover_door_id')}), expected {SWIM_VOLUMES} "
                                 f"with BlueWater2 on {self.flood_doors}")

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        project, source, content = build.project, build.source, build.content
        script = lua.Script(build, "Bathhouse")
        script.doors()
        script.chests()

        def native(name):
            return project.native(source.properties(name)["Pos"]).round().astype(int)

        def box(name):
            p = source.properties(name) if name in {o["name"] for o in source.objects} else None
            points = np.array(source.models[name].points, float)
            low, high = project.native(points.min(0)), project.native(points.max(0))
            return np.minimum(low, high).round().astype(int).tolist() + np.maximum(low, high).round().astype(int).tolist()

        texts = letters()
        concubines = [self.actor_index[n] for n in ("Concubine1", "Concubine2", "Concubine3")]
        ebora, fatc = self.actor_index["Ebora"], self.actor_index["BigColWinPool2"]
        vents = ", ".join("{" + ", ".join(map(str, box(brush))) + "}" for brush in VENTS.values())
        vent_points = ", ".join(lua.point(native(v)) for v in VENTS)
        steam_always = ", ".join(lua.point(native(s)) for s in STEAM_ALWAYS)
        steam_furnace = ", ".join(lua.point(native(s)) for s in STEAM_FURNACE)
        lines = [
            "-- Bits every handler below shares. One-shot timers: the map's timers run from load (RegisterMapTimerEvent",
            "-- repeats), so each is armed by a variable when started and acts only when armed.",
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "local function near(p, range)",
            "    local x, y, z = evt.GetPartyPosition()",
            "    return math.abs(x - p[1]) < range and math.abs(y - p[2]) < range and math.abs(z - p[3]) < range",
            "end",
            bath_cinematics.RUMBLE_LOCAL,
            "",
            "-- The furnace (BathFurnace.scr on the gas valve GasRelease0, a RotatingDoor: 180 degrees, sticky). Opening it lights",
            "-- the big fires (Fire1/4, DP2steam.scr), starts the steam over both pools and the pistons (PistonDown/Up 0/1",
            "-- toggle each other while the valve is open), quakes the first time (TriggerEffects -> EffectsMgr.scr) and 2 s",
            "-- later boils Ebora's fat friend in pool A to death (KillFatc -> Fatc.scr `Die`). Closing it puts all out.",
            f"handlers[{EV_VALVE}] = function()   -- GasRelease0",
            "    if var(\"Furnace\") == 0 then",
            "        set(\"Furnace\", 1)",
            "        open(\"GasRelease0\")",
            *[f"        evt.SetSprite({cog}, true)   -- {name}" for name, cog in COG_FIRE.items()],
            *bath_cinematics.quake_lua(),
            f"        if var(\"FatcBoiled\") == 0 then arm({T_FATC}, 2) end",
            "    else",
            "        set(\"Furnace\", 0)",
            "        close(\"GasRelease0\")",
            *[f"        evt.SetSprite({cog}, false)   -- {name}" for name, cog in COG_FIRE.items()],
            "    end",
            "    evt.PlaySoundName(\"sounds/door/metaldoorslide01.wav\", 0, 0, 0)",
            "end",
            f"handlers[{T_FATC}] = function()   -- KillFatc",
            f"    if not fired({T_FATC}) or var(\"FatcBoiled\") == 1 then return end",
            "    -- Fatc.scr's Die: a Fatc the party has killed takes none (its corpse stays; each turnon tries again)",
            f"    if not MM9.receives(\"bathhouse\", \"BigColWinPool2\", \"Die\", {fatc}) then return end",
            "    set(\"FatcBoiled\", 1)",
            f"    MM9.removeActor({fatc})   -- BigColWinPool2",
            "    evt.PlaySoundName(\"sounds/ambient/water/liquidboiling.wav\", 0, 0, 0)",
            "end",
            f"handlers[{EV_WARNING}] = function() evt.StatusText({lua_string(WARNING)}) end   -- FurnaceWarning",
            "",
            "-- The drain (Switch0, a Switch authored thrown open: one click throws it). Its targets: the propeller WaterProp",
            "-- spins (9000 degrees at 300/s), BlueWater2 drains (DrainWater.scr: the surface sinks to FloodRoomMarker at",
            "-- 10 LT/s) and Door6/Door7 unlock.",
            f"handlers[{EV_SWITCH}] = function()   -- Switch0",
            "    if var(\"Drained\") == 1 then return end",
            "    set(\"Drained\", 1)",
            "    close(\"Switch0\"); open(\"WaterProp\"); set(\"PropellerTurns\", 0)",
            "    open(\"FloodWater\"); open(\"FloodWaterStairs\")   -- the drained room's water",
            "    evt.PlaySoundName(\"sounds/ambient/fountain_20.wav\", 0, 0, 0)   -- DrainWater.scr :DrainWater",
            "    evt.PlaySoundName(\"sounds/ambient/machinery03.wav\", 0, 0, 0)",
            "end",
            f"handlers[{EV_DOOR67}] = function()   -- Door6/Door7: Locked until Switch0 unlocks them",
            "    if var(\"Drained\") == 0 then evt.StatusText(\"The door is locked.\") return end",
            "    evt.SetDoorState(DOORS.Door6, DoorAction.Trigger); evt.SetDoorState(DOORS.Door7, DoorAction.Trigger)",
            "end",
            f"handlers[{EV_FLAP}] = function() evt.SetDoorState(DOORS.RotatingDoor0, DoorAction.Trigger) end"
            "   -- RotatingDoor0, the flap over SteamVent0 (swings 90 on a push, back after 10 s)",
            "",
        ]
        if not swimming(build):
            lines.append("-- The dives: MM9's swim through the flooded tunnels (no swimming: README \"Water\").")
        script.add([], (EV_VALVE, "Gas valve", "Valve"), (T_FATC, "KillFatc", None, "timer"),
                   (EV_WARNING, "Warning", "Warning"), (EV_SWITCH, "Switch", "Switch"), (EV_DOOR67, "Door", "Door"),
                   (EV_FLAP, "Flap", "Flap"))
        for name, (_, _, arrival, facing, text) in ({} if swimming(build) else DIVES).items():
            point = project.native(arrival).round().astype(int)
            yaw = int(round(facing / 360 * 2048)) % 2048
            lines.append(f"handlers[{EV_DIVE[name]}] = function()   -- {name}")
            lines.append(f"    evt.StatusText({lua_string(text)})")
            lines.append(f"    set(\"LastDive\", {EV_DIVE[name]})")
            lines.append(f"    evt.MoveToMap({point[0]}, {point[1]}, {point[2] + 1}, {yaw}, 0, 0, 0, 0)")
            lines.append("end")
            script.add([], (EV_DIVE[name], name, None))
        lines += [
            "",
            "-- The letters (BookLetter.scr DoLetter): MM9's book and scroll texts.",
        ]
        for name, event in EV_LETTER.items():
            title, text = texts[name]
            lines.append(f"handlers[{event}] = function() set(\"Read{name}\", 1); "
                         f"evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end   -- {name}")
            script.add([], (event, "Scroll", "Scroll"))
        spawn_rows = ", ".join(f"{loc} = {{{', '.join(map(str, ids))}}}" for loc, ids in self.spawned.items())
        lines += [
            "",
            "-- The spores (StepTrigger0-2 -> SpawnLoc0/1 `spawn` twice, SpawnMgr.scr '1 1 JellySpore', then all three",
            "-- triggers and the manager off): the first trigger stepped on shows its location's two hidden Jellyspores.",
            f"local SPAWNED = {{{spawn_rows}}}",
            "local function spores(loc)",
            "    if var(\"Spores\") == 1 then return end",
            "    set(\"Spores\", 1)",
            "    for _, index in ipairs(SPAWNED[loc]) do",
            "        evt.SetMonsterBit(index, MonsterBits.Invisible, false)",
            "        evt.SetMonsterBit(index, MonsterBits.Hostile, true)",
            "    end",
            "end",
        ]
        for name, event in EV_STEP.items():
            lines.append(f"handlers[{event}] = function() spores(\"{STEP_TARGET[name]}\") end   -- {name}")
            script.add([], (event, name, None))
        gossip = ", ".join(lua_string(g) for g in GOSSIP)
        taunts = ", ".join(lua_string(t) for t in TAUNTS)
        lines += [
            "",
            "-- Ebora (EboraBath.scr): she cannot be hurt (CanDamage FALSE) and stays in her tub; the gossip trigger by",
            "-- Door5 has her taunt the party (OnGossip, up to four lines); each dead concubine (EboraConcubine.scr OnDeath",
            "-- -> DeadConcubine) a taunt; the third sends her off in a column of fire (DitchTheJoint): key 349 and 80 000",
            "-- experience for a party on Gostaf's errand (key 348), else key 350 (NPC339.rude reads both): the cinematic",
            f"-- {bath_cinematics.CINEMA_ID} (bathhouse.cinematics.yml; its steps at the end of this file, bath_cinematics.py).",
            f"local GOSSIP = {{{gossip}}}",
            f"local TAUNTS = {{{taunts}}}",
            f"local EBORA = {ebora}",
            f"local CONCUBINES = {{[{concubines[0]}] = true, [{concubines[1]}] = true, [{concubines[2]}] = true}}",
            "local GREATER_ON_DEATH = {" + ", ".join(f"[{self.actor_index[n]}] = true" for n in GREATER_ON_DEATH
                                                     if n in self.actor_index) + "}",
            f"handlers[{EV_GOSSIP}] = function()   -- EboraGossip",
            "    local n = var(\"Gossip\")",
            "    if var(\"EboraGone\") == 1 or n >= #GOSSIP then return end",
            "    set(\"Gossip\", n + 1)",
            "    evt.StatusText(GOSSIP[n + 1])",
            "end",
            f"handlers[{DAMAGE_HOOK}] = function(context)",
            "    if context.actorIndex == EBORA then evt.SetHookDamage(0) end",
            "end",
            f"handlers[{KILL_HOOK}] = function(context)",
            f"    if GREATER_ON_DEATH[context.actorIndex] then   -- LesserDemon.scr :OnDeathDone (p0 1)",
            "        local x, y, z = evt.GetMapActorPosition(context.actorIndex)",
            f"        if x ~= nil then evt.SummonMonstersById({{monster = {GREATER_DEMON}, x = x, y = y, z = z, "
            "radius = 32, count = 1, effect = \"mm9:GreaterDemon\"}) end   -- GreaterDemon.scr :SpawnIn's DoClientFX",
            "        return",
            "    end",
            "    if not CONCUBINES[context.actorIndex] or var(\"EboraGone\") == 1 then return end",
            "    local dead = var(\"DeadConcubines\") + 1",
            "    set(\"DeadConcubines\", dead)",
            f"    if dead >= 3 then MM9Cinematic.start(\"{bath_cinematics.CINEMA_ID}\") else evt.StatusText(TAUNTS[dead]) end",
            "end",
            "",
            "-- The steam vents (SteamVent.scr: on 3 s, off 3 s; SteamVentDB.scr moves the DamageBrush onto the vent while",
            "-- it blows) and the steam over the hot water: one poll four times a second. A party in a blowing vent's box",
            f"-- takes {VENT_DAMAGE} fire damage a second; steam puffs (mm9:smokestack) rise near the party.",
            f"local VENTS = {{{vents}}}",
            f"local VENT_POINTS = {{{vent_points}}}",
            f"local STEAM = {{{steam_always}}}",
            f"local STEAM_FURNACE = {{{steam_furnace}}}",
            "local polls = 0",
            f"local DRAIN_TURNS = {int(DRAIN_SECONDS / 1.25)}",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    polls = polls + 1",
            f"    local cycle = math.floor(polls / 4) % {VENT_ON + VENT_OFF}",
            f"    local blowing = cycle < {VENT_ON}",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for k, b in ipairs(VENTS) do",
            "        if blowing and x > b[1] - 40 and x < b[4] + 40 and y > b[2] - 40 and y < b[5] + 40 and z > b[3] - 200",
            "                and z < b[6] then",
            "            if polls % 4 == 0 then",
            f"                evt.DamagePlayer(Players.All, const.Damage.Fire, {VENT_DAMAGE})",
            "                set(\"VentHits\", var(\"VentHits\") + 1); set(\"VentHit\", 1)",
            "            end",
            "        end",
            f"        if blowing and polls % 4 == 0 and cycle == 0 and near(VENT_POINTS[k], {STEAM_RANGE}) then",
            f"            local p = VENT_POINTS[k]; evt.SpawnWorldEffect(\"{STEAM_EFFECT}\", p[1], p[2], p[3], {STEAM_SCALE})",
            "        end",
            "    end",
            "    if polls % 12 == 0 then",
            "        for _, p in ipairs(STEAM) do",
            f"            if near(p, {STEAM_RANGE}) then evt.SpawnWorldEffect(\"{STEAM_EFFECT}\", p[1], p[2], p[3], {STEAM_SCALE}) end",
            "        end",
            "        if var(\"Furnace\") == 1 then",
            "            for _, p in ipairs(STEAM_FURNACE) do",
            f"                if near(p, {STEAM_RANGE}) then evt.SpawnWorldEffect(\"{STEAM_EFFECT}\", p[1], p[2], p[3], {STEAM_SCALE}) end",
            "            end",
            "        end",
            "    end",
            "    -- the propeller turns while the room drains (a turn each 1.25 s at MM9's 300 degrees a second)",
            "    if var(\"Drained\") == 1 and var(\"PropellerTurns\") < DRAIN_TURNS and polls % 5 == 0 then",
            "        local turns = var(\"PropellerTurns\") + 1",
            "        set(\"PropellerTurns\", turns)",
            "        if turns % 2 == 1 then close(\"WaterProp\") else open(\"WaterProp\") end",
            "    end",
            *bath_cinematics.rumble_poll_lua(),
            "    -- the pistons pump while the valve is open (PistonUp0's close trigger `repeat0` toggles it again)",
            "    if var(\"Furnace\") == 1 and polls % 4 == 0 then",
            "        local p = (polls / 4) % 2 == 0",
            "        evt.SetDoorState(DOORS.PistonDown0, p and DoorAction.Open or DoorAction.Close)",
            "        evt.SetDoorState(DOORS.PistonUp0, p and DoorAction.Open or DoorAction.Close)",
            "        evt.SetDoorState(DOORS.PistonDown1, p and DoorAction.Close or DoorAction.Open)",
            "        evt.SetDoorState(DOORS.PistonUp1, p and DoorAction.Close or DoorAction.Open)",
            "    end",
            "end",
            "",
            f"handlers[{EV_LOAD}] = function()   -- map load: the saved states, the poll",
            "    local furnace = var(\"Furnace\") == 1",
            *[f"    evt.SetSprite({cog}, furnace)   -- {name}" for name, cog in COG_FIRE.items()],
            f"    if var(\"FatcBoiled\") == 1 then MM9.removeActor({fatc}) end",
            "    if var(\"EboraGone\") == 1 then MM9.removeActor(EBORA) end",
            "    if var(\"Drained\") == 1 then open(\"FloodWater\"); open(\"FloodWaterStairs\") end",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "end",
            "",
        ]
        script.add(lines, (EV_GOSSIP, "EboraGossip", None), (T_POLL, "Steam and vents", None, "timer"),
                   (EV_LOAD, "Map load", None))
        script.hooks += [f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Ebora cannot be hurt", handlers[{DAMAGE_HOOK}])',
                         f'RegisterMonsterKilledHook({KILL_HOOK}, "Ebora concubines", handlers[{KILL_HOOK}])']
        return script.finish(on_load=[EV_LOAD]) + cutscenes.lua_block(bath_cinematics.scenes(ebora))

    def report(self, build) -> dict:
        return {"scripted": {"flood_doors": self.flood_doors, "actors": self.actor_index,
                             "spawned": self.spawned}}


if __name__ == "__main__":
    hooks = Bathhouse()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        # Ebora's escape (bath_cinematics.py): the engine loads it beside the map
        scenes = bath_cinematics.scenes(hooks.actor_index["Ebora"])
        print(f"cinematics installed: {cutscenes.install(bath_cinematics.STEM, scenes)}")
    sys.exit(code)
