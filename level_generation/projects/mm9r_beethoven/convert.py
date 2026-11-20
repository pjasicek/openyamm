#!/usr/bin/env python3
"""
Beethoven (the Sturmford sewers), MM9 rework: MM9's BEETHOVEN.dat as a native indoor map (BLV) on the shared dungeon
converter (../mm9r_common/dungeon/, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_beethoven/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_beethoven/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, archway cuts, ladders and texture substitutes; this file the map's own changes to
the polygons (water surfaces, the wading floor of the Grand Entrance), its population and its scripted objects as native
Lua (README.md, "Scripted objects").
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
import review_root  # noqa: E402
from dungeon import lua, tables, water  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.source import SCALE  # noqa: E402
from dungeon.bodies import mm9_bodies, placed_body  # noqa: E402

SLIME, WATER = "Sprites\\Water\\slime.spr", "Sprites\\Water\\water125.spr"
BED = "slime_0000.dtx"
# The channels' surfaces: MM9's WaterTop1/WaterTop10 are one quad each over the whole storey (only the channels show,
# the rest lies in the rock). The native surface is the channel's bed raised to the water's height, so it stops at the
# channel's walls and each room keeps its own part. Bed height (LT) -> surface height (LT).
CHANNELS = {0.0: 12.0, -1216.0: -1191.0}
SHORE_LT = 26.0                     # the surface reaches this far past the bed, up the ramps either side of the channel
SLIVER_LT = 24.0                    # a bed polygon narrower than this keeps no surface of its own
# Volume surfaces: MM9's water volumes (ShowSurface 1) as the top face of their box. Model -> texture.
POOLS = {"frigidarium water": WATER, "Caldarium water": WATER, "BlueWater4": WATER, "BlueWater1": WATER,
         "BlueWater5": WATER, "BlueWater2": WATER}
# The Grand Entrance: a cavern flooded to y -784 over a floor at -1152 (MM9's ClearWater, the party swims; bottom
# of Ladder0 at -832). Swum since the shared water rule (2026-11-06, dungeon/water.py): its surface is non-solid and the
# shaft's walls hang 48 under it as MM9's, so the party swims under them to the corridors and takes Ladder0 from the
# water. With overrides.yml `map: {swim: false}` the old stand-in: a solid surface the party wades on, from the foot of
# the ladder to the corridors' sills at -768, and the shaft's walls stop above the party's head.
ENTRANCE_WATER = "GrandEntrance Water"
SHAFT_BOX = ((-790.0, -1045.0), (-555.0, -840.0))      # (x, z) low and high of the shaft's four walls
SHAFT_BOTTOM = -696.0
RUNGS_BOTTOM = -784.0


def grown(ring: np.ndarray, distance: float) -> np.ndarray:
    """A convex (x, z) ring moved outward by `distance` on every side."""
    sign = 1.0 if float(np.sum(ring[:, 0] * np.roll(ring[:, 1], -1) - np.roll(ring[:, 0], -1) * ring[:, 1])) > 0 else -1.0
    edges = np.roll(ring, -1, axis=0) - ring
    normals = sign * np.stack([edges[:, 1], -edges[:, 0]], 1) / np.linalg.norm(edges, axis=1, keepdims=True)
    previous = np.roll(normals, 1, axis=0)
    bisector = normals + previous
    scale = distance / np.maximum(1.0 + (normals * previous).sum(1), 0.3)
    return ring + bisector * scale[:, None]


def surface(points_xz, y: float, texture: str, width: int, height: int, model: str, role: str) -> Polygon:
    """A horizontal face over a ring of (x, z) points, front upward, mapped one texel per LT."""
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture,
                      (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), 0x1088, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, polygon.mapping, 0x1088,
                          model, role)
    polygon.notes.update(width=width, height=height)
    return polygon


PROPS = PROJECT / "props.json"
# --- Events, timers, cogs, groups -------------------------------------------------------------------------------------
EV_LOAD, EV_MANUSCRIPT, EV_GREAT_LEVER = 1, 90, 91
EV_HEDGE = {"HedgeDoor1": 92, "HedgeDoor2": 93, "HedgeDoor3": 94}
EV_COFFIN = 150                     # 150 + k: coffin k's touch trigger
EV_BOTTLE = 170                     # 170 + k: the touch trigger at bottle k's start
T_COFFIN = 200                      # 200 + k: coffin k's lid has risen (CoffinRaise.scr), the mummy stirs
T_KICK = 220                        # 220 + k: coffin k's mummy kicks it to pieces (CoffinMummy.scr's AtKick)
COG_COFFIN, COG_DEBRIS = 310, 330
GROUP_MUMMY = 80                    # 80 + k: the mummy of coffin k
KEY_LUDWIG, KEY_FOUND_FOR_LUDWIG, KEY_FOUND_UNASKED = 14, 16, 110       # Ludwigsmanuscript.scr
ITEM_MANUSCRIPT = 248
LOBBER_POD_A = 9084
# Light54 is a 90-degree spot up out of the well: as a point light it floods the maze hall.
NOT_BAKED = {"Light54"}
DIMMED_IN_BAKE = {"Light136": 0.45}
# CoffinRaise.scr and the Trigger that fires it: trigger -> coffin -> mummy (CoffinMummy.scr).
COFFINS = [("Trigger7", "CoffinRaised9", "PetrifiedMummy7"), ("Trigger6", "CoffinRaised8", "PetrifiedMummy6"),
           ("Trigger3", "CoffinRaised6", "PetrifiedMummy3"), ("Trigger5", "CoffinRaised7", "PetrifiedMummy5"),
           ("Trigger1", "CoffinRaised5", "PetrifiedMummy1"), ("Trigger0", "CoffinRaised3", "PetrifiedMummy0"),
           ("Trigger2", "CoffinRaised15", "PetrifiedMummy2"), ("Trigger4", "CoffinRaised4", "PetrifiedMummy4")]
BOTTLES = [("TriggerBottleSW", "BottleSW", "sw"), ("TriggerBottleNW", "BottleNW", "nw"),
           ("TriggerBottleNE", "BottleNE", "ne"), ("TriggerBottleSE", "BottleSE", "se")]
BOTTLE_MODEL = "engine/models/mm9_bottlefloat.glb"
COFFIN_LID_SECONDS = 1             # CoffinFancy's `open` clip (the lid part's, scripts/coffin_parts.py in the props project)
KICK_SECONDS = 3.232               # Wakeup2's AtKick key (ZOMBIE.abc; the Rotter row draws the zombie model)
COFFIN_BED_LT = 35                  # a mummy lies this far above its coffin's base (five DAT heights; the other
                                    # three are MoveToFloor, which settles them on the coffin's bed)
# MM9's translucent surfaces other than water, as translucent faces: source texture -> (alias, opacity): brush Alpha
# (the webs' 0.7), the texture's alpha on top (devdocs/INDOOR_TRANSLUCENT_FACES.md). Soft edges need the blend: a BLV
# face only discards fully transparent texels.
TRANSLUCENT = {"WEB32N735S": 0.7, "XEENF0606E": 1.0, "STEEKFFKSJ": 1.0, "GRIL2FJ7QI": 1.0, "GRILF0RNTM": 1.0,
               "CHAIFV6LUO": 1.0}
# The water shader for the sewers' slime and the baths' water (engine/liquids/liquids.yml, this world only, review root
# until the map is accepted); the colours are the mean of MM9's own frames, as bright as the sector ambient lets them read.
LIQUIDS = """
  - id: slime_mm9
    kind: water
    color: [118, 132, 62]
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [slim91p4yn]

  - id: water_mm9
    kind: water
    color: [44, 92, 102]
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [wate27jpcx]
"""


# Ladder0 and Ladder1 stand in holes in the floor: a party on the hole's lip takes them, drifting to the rungs while it
# climbs a little (MM9's ladder volumes hold it as it steps in); `top_lt`: how far it can rise above the lip.
LADDER_LIPS = {"Ladder0": {"reach": 300, "top_lt": 100}, "Ladder1": {"reach": 300, "top_lt": -640}}


def install_liquids() -> None:
    """MM9's water textures in the review root's liquid table (shared, so under the tables lock, added once)."""
    with tables.locked("review_tables.lock"):
        path = review_root.mirror_path("engine/liquids/liquids.yml")
        text = path.read_text()
        blocks = re.split(r"(?m)^(?=  - id: )", text)
        kept = "".join(b for b in blocks if not re.match(r"  - id: (slime|water)_mm9\n", b)).rstrip("\n") + "\n"
        if kept + LIQUIDS != text:
            review_root.install("engine/liquids/liquids.yml", (kept + LIQUIDS).encode())


class Beethoven(dungeon.Hooks):
    generator = "mm9r_beethoven"
    mover_events = {"GreatDoorLevers": (EV_GREAT_LEVER, "click"),
                    **{group: (event, "click") for group, event in EV_HEDGE.items()}}

    def edit_polygons(self, build, polygons: list) -> list:
        source = build.source
        swim = water.swimming(build.project)
        kept = []
        for polygon in polygons:
            if polygon.model.startswith("WaterTop"):
                continue
            if swim:
                # The shared water rule: the Grand Entrance is swum, under the shaft's walls as MM9 hangs them
                kept.append(polygon)
                continue
            low, high = polygon.points.min(0), polygon.points.max(0)
            in_shaft = SHAFT_BOX[0][0] <= low[0] and high[0] <= SHAFT_BOX[1][0] and SHAFT_BOX[0][1] <= low[2] \
                and high[2] <= SHAFT_BOX[1][1]
            if in_shaft and low[1] < SHAFT_BOTTOM and high[1] >= SHAFT_BOTTOM - 140:
                bottom = RUNGS_BOTTOM if polygon.model == "WorldObject0" else SHAFT_BOTTOM
                polygon.points = polygon.points.copy()
                polygon.points[:, 1] = np.maximum(polygon.points[:, 1], bottom)
                polygon.keys = [tuple(np.round(p, 1)) for p in polygon.points]
                if polygon.area < 1.0:          # a wall wholly under the new bottom
                    continue
            kept.append(polygon)
        out = list(kept)
        for polygon in kept:
            bed = polygon.texture.replace("\\", "/").split("/")[-1].lower() == BED
            y = float(round(polygon.points[:, 1].mean()))
            if bed and polygon.normal[1] > 0.99 and y in CHANNELS:
                ring = polygon.points[:, [0, 2]]
                alias = source.aliases[SLIME.lower()]
                perimeter = float(np.linalg.norm(ring - np.roll(ring, -1, axis=0), axis=1).sum())
                if 2.0 * polygon.area / perimeter < SLIVER_LT:
                    # A strip between the ramps of a junction: no air above it at the surface's height, so a surface
                    # would be dropped as a face without air and the bed would show. The bed itself draws the water.
                    polygon.texture = SLIME
                    polygon.notes.update(width=alias["width"], height=alias["height"])
                    continue
                out.append(surface(grown(ring, SHORE_LT), CHANNELS[y], SLIME, alias["width"], alias["height"],
                                   "WaterTop1", "nonsolid"))
        for model, texture in POOLS.items():
            points = np.array(source.models[model].points, float)
            (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
            alias = source.aliases[texture.lower()]
            out.append(surface([(x0, z0), (x0, z1), (x1, z1), (x1, z0)], float(points[:, 1].max()), texture,
                               alias["width"], alias["height"], model, "nonsolid"))
        points = np.array(source.models[ENTRANCE_WATER].points, float)
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        alias = source.aliases[SLIME.lower()]
        out.append(surface([(x0, z0), (x0, z1), (x1, z1), (x1, z0)], float(points[:, 1].max()), SLIME, alias["width"],
                           alias["height"], ENTRANCE_WATER, "static"))
        return out


    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        events = {"Manuscript": EV_MANUSCRIPT}
        cogs = {}
        cogs.update({coffin: COG_COFFIN + k for k, (_, coffin, _) in enumerate(COFFINS)})
        if PROPS.exists():
            # MM9 names five chests Treasurechest<k> and six TreasureChest<k>: the compiler's node names ignore case.
            entries = json.loads(PROPS.read_text())
            for entry in entries:
                if entry["source_name"].startswith("Treasurechest"):
                    entry["source_name"] = "Chest" + entry["source_name"][len("Treasurechest"):]
            unique = build.project.work / "props_unique.json"
            unique.write_text(json.dumps(entries))
            content.props(unique, events=events, cogs=cogs)
        else:
            print("note: props.json is missing; no decorations, chests or quest objects placed")
        # A coffin breaks up when its mummy kicks free (CoffinMummy.scr -> `destroy`): rubble, hidden until then.
        for k, (trigger, coffin, _) in enumerate(COFFINS):
            p = source.properties(coffin)
            floor = content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 40)
            content.entity(f"{coffin}Rubble", "mm9_stonedebris03", project.native([p["Pos"][0], floor, p["Pos"][2]]),
                           0, primary=COG_DEBRIS + k)
            t = source.properties(trigger)
            content.pad(trigger, t["Pos"], t["Dims"], EV_COFFIN + k)
        self.bottle_starts = []
        for k, (trigger, _, _) in enumerate(BOTTLES):
            t = source.properties(trigger)
            content.pad(trigger, t["Pos"], t["Dims"], EV_BOTTLE + k)
            self.bottle_starts.append(project.native(t["Pos"]).round().astype(int).tolist())

    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        # LobberPodA has no row in the old importer's replacement table: MM9's first Lobber Pod tier (9084), hp 4; the
        # second tier resolves (LobberPodB). Both are `CacheOnly 1` in the DAT (the Lobbers' thrown pods, never placed),
        # so monster_bases() leaves them out (2026-11-05) and this only applies should a placed pod come back.
        if "LobberPodB0" in bases:
            height, radius = mm9_bodies().body(LOBBER_POD_A - 9000)        # its own body, not the Scale 2 pod's
            bases["LobberPodA0"] = dict(bases["LobberPodB0"], monster_info_id=LOBBER_POD_A, monster_id=LOBBER_POD_A,
                                        hp=4, radius=radius, height=height)
            content.report["omitted"] = [o for o in content.report["omitted"] if o["anchor"] != "LobberPodA0"]
        mummy_group = {mummy: GROUP_MUMMY + k for k, (_, _, mummy) in enumerate(COFFINS)}
        self.mummy_index = {}               # coffin k -> its mummy's actor index
        indices = {o["name"]: o["index"] for o in source.objects}
        self.coffin_destructible = {k: indices[coffin] for k, (_, coffin, _) in enumerate(COFFINS)}
        out = []
        for o in source.objects:
            name, p = o["name"], o["properties"]
            if name not in bases:
                continue
            group = mummy_group.get(name, 0)
            query = p["Pos"][1] + 40
            record = content.actor(o, bases[name], sector_of_room, group=group, hidden=bool(group), floor_query_lt=query)
            if group:
                # CoffinMummy.scr: it lies on its coffin's bed (gravity off), hidden behind the lid and dormant until
                # the map's script wakes it at the kick.
                floor = content.floor_at(p["Pos"][0], p["Pos"][2], query)
                bed = source.properties(COFFINS[group - GROUP_MUMMY][1])["Pos"][1] + COFFIN_BED_LT
                record["position"]["z"] += int(round((bed - floor) * SCALE))
                record["dormant"] = True
            if o["class"] == "AirBorneIcky":
                record["position"]["z"] = int(round(p["Pos"][1] * SCALE)) - 120
            record.update(placed_body(record["monster_id"], p))   # MM9's body at the DAT's own Scale (replaces the row's)
            if group:
                self.mummy_index[group - GROUP_MUMMY] = record["actor_index"]
            out.append(record)
        return out

    # --- scene --------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """Ladders in holes (a party on the lip takes them), MM9's translucent faces, the liquid table."""
        sys.path.insert(0, str(dungeon.source.ROOT))
        from util.map_export import parse_blv_file
        for ladder in scene.get("ladders", []):
            rule = LADDER_LIPS.get(ladder["id"])
            if rule:
                ladder["reach"] = rule["reach"]
                ladder["top"][2] = round(rule["top_lt"] * SCALE, 2)
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        faces = {}
        for face in blv["faces"]:
            if not face["is_portal"] and face["texture_name"] in TRANSLUCENT:
                faces.setdefault(TRANSLUCENT[face["texture_name"]], []).append(face["index"])
        entries = scene.setdefault("translucent_faces", [])
        for opacity, ids in sorted(faces.items()):
            entries.append({"faces": sorted(ids), "opacity": opacity, "tint": [1.0, 1.0, 1.0], "two_sided": False})
        build.stats["translucent_faces"] = sum(len(e["faces"]) for e in entries)
        if build.project.install:
            install_liquids()
        liquids.apply(build, scene)     # see-through water and slime where MM9's are (../mm9r_common/liquids.py)

    # --- map script ---------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Beethoven")
        script.doors()
        script.chests()
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
            "",
            "-- The great door to the maze (Door SDoor11/12, Lever5/6): either lever (they are one double door, Lever6",
            "-- carries the triggers) parts the two halves for good: MM9 locks the door and the lever behind it.",
            f"handlers[{EV_GREAT_LEVER}] = function()   -- Lever5, Lever6",
            "    if var(\"GreatDoor\") == 1 then return end",
            "    set(\"GreatDoor\", 1)",
            "    open(\"Lever5\"); open(\"Lever6\"); open(\"SDoor11\"); open(\"SDoor12\")",
            "end",
            "",
            "-- The maze's stone doors (RotatingDoor HedgeDoor1-3): MM9 swings them on a push.",
        ]
        script.add([], (EV_GREAT_LEVER, "Lever", "Lever"), (EV_MANUSCRIPT, "Manuscript", None))
        for group, event in EV_HEDGE.items():
            lines.append(f"handlers[{event}] = function() evt.SetDoorState(DOORS.{group}, DoorAction.Trigger) end")
            script.add([], (event, "Stone door", "Door"))
        lines += [
            "",
            f"-- Ludwig's manuscript (Ludwigsmanuscript.scr): a world item ({ITEM_MANUSCRIPT}, dungeon/pickups.py); its pickup "
            f"gives key {KEY_FOUND_FOR_LUDWIG} if the party",
            f"-- has spoken to Ludwig (key {KEY_LUDWIG}), else key {KEY_FOUND_UNASKED}.",
            "local function manuscriptTaken()",
            f"    return MM9.hasKey({KEY_FOUND_FOR_LUDWIG}) == 1 or MM9.hasKey({KEY_FOUND_UNASKED}) == 1",
            "end",
            f"handlers[{EV_MANUSCRIPT}] = function()   -- Manuscript",
            "    if manuscriptTaken() then return end",
            f"    MM9.giveKey(MM9.hasKey({KEY_LUDWIG}) == 1 and {KEY_FOUND_FOR_LUDWIG} or {KEY_FOUND_UNASKED})",
            "    MM9.playSound(\"sounds/events/quest.wav\")",
            "end",
            "",
            "-- The coffins (CoffinRaise.scr, CoffinMummy.scr): touching a coffin's trigger opens its lid with a stone",
            "-- groan (the lid part's open clip). Its mummy lies inside, dormant (LoopAnim coffin2); when the lid is up it",
            "-- wakes (PlayAnim wakeup2), and at the clip's kick (AtKick) the coffin breaks (the destructible: its",
            "-- crumble and debris; rubble stays) and the mummy fights. Coffin<k>: 0 shut, 1 lid opening, 3 waking, 2 broken.",
            "-- coffin k -> its mummy's actor index (CoffinMummy.scr: CanDamage 0 until it kicks free), its destructible",
            f"local MUMMIES = {{{', '.join(f'[{k}] = {self.mummy_index[k]}' for k in sorted(self.mummy_index))}}}",
            f"local COFFINS = {{{', '.join(f'[{k}] = {self.coffin_destructible[k]}' for k in sorted(self.coffin_destructible))}}}",
            f"local function coffin(k)   -- {EV_COFFIN} + k",
            "    if var(\"Coffin\" .. k) ~= 0 then return end",
            "    set(\"Coffin\" .. k, 1)",
            "    evt.PlaySoundName(\"sounds/door/stone_door02.wav\", 0, 0, 0)",
            f"    evt.PlayDecorationClip({COG_COFFIN} + k, \"open\")",
            f"    evt.SetMonGroupBit({GROUP_MUMMY} + k, MonsterBits.Invisible, false)",
            "    evt.PlayActorClip(MUMMIES[k], \"coffin_idle\", true)",
            f"    arm({T_COFFIN} + k, {COFFIN_LID_SECONDS})",
            "end",
            "local function mummy(k)",
            f"    if not fired({T_COFFIN} + k) or var(\"Coffin\" .. k) ~= 1 then return end",
            "    set(\"Coffin\" .. k, 3)",
            "    evt.PlayActorClip(MUMMIES[k], \"wakeup2\", \"hold\")",
            f"    arm({T_KICK} + k, {KICK_SECONDS})",
            "end",
            "-- :OnPostDestroy (the kick): the coffin's destroy, SetPropNumber CanDamage, TRUE, gravity, then baseMelee.",
            "local function kicked(k)",
            "    set(\"Coffin\" .. k, 2)",
            "    evt.DestroyDestructible(COFFINS[k])",
            f"    evt.SetSprite({COG_DEBRIS} + k, true)",
            "    evt.ClearActorPresentation(MUMMIES[k])",
            f"    evt.SetMonGroupBit({GROUP_MUMMY} + k, MonsterBits.Invisible, false)",
            f"    evt.SetMonGroupBit({GROUP_MUMMY} + k, MonsterBits.Hostile, true)",
            "    MM9.setCanDamage(MUMMIES[k], true)",
            "    evt.WakeActor(MUMMIES[k])",
            "end",
            "local function kick(k)",
            f"    if not fired({T_KICK} + k) or var(\"Coffin\" .. k) ~= 3 then return end",
            "    kicked(k)",
            "end",
        ]
        for k, (trigger, name, mummy) in enumerate(COFFINS):
            lines += [f"handlers[{EV_COFFIN + k}] = function() coffin({k}) end   -- {trigger} -> {name}",
                      f"handlers[{T_COFFIN + k}] = function() mummy({k}) end   -- {mummy} wakes",
                      f"handlers[{T_KICK + k}] = function() kick({k}) end   -- {mummy} kicks free"]
            script.add([], (EV_COFFIN + k, trigger, None), (T_COFFIN + k, f"{mummy} wakes", None, "timer"),
                       (T_KICK + k, f"{mummy} kicks free", None, "timer"))
        starts = ", ".join(lua.point(p) for p in self.bottle_starts)
        clips = ", ".join(f'"{clip}"' for _, _, clip in BOTTLES)
        lines += [
            "",
            "-- The bottle (BottleFollow.scr): when the party arrives, the start's bottle bobs on the sewage six seconds,",
            "-- then drifts along the channels (MarkerSW/NW/NE/SE) to the shaft of the Grand Entrance, on from the",
            "-- MarkerLower path under the catacombs to Ludwig's manuscript, and starts again: it shows the way. The",
            "-- other three are removed. The bottle is one looping model (scripts/bottle.py in the props project), which",
            "-- the map spawns again on each load: Bottle says which, reset at load.",
            f"local BOTTLE_STARTS = {{{starts}}}",
            f"local BOTTLE_CLIPS = {{{clips}}}",
            "local function startBottle(k)",
            "    if var(\"Bottle\") ~= 0 then return end",
            "    set(\"Bottle\", k)",
            f"    evt.SpawnWorldModel(\"{BOTTLE_MODEL}\", 0, 0, 0, 1, 0, BOTTLE_CLIPS[k])",
            "end",
        ]
        for k, (trigger, _, _) in enumerate(BOTTLES):
            lines.append(f"handlers[{EV_BOTTLE + k}] = function() startBottle({k + 1}) end   -- {trigger}")
            script.add([], (EV_BOTTLE + k, trigger, None))
        lines += [
            f"handlers[{EV_LOAD}] = function()   -- map load",
            f"    for k = 0, {len(COFFINS) - 1} do",
            "        -- a save taken while a coffin opened: its mummy is up and the coffin broken",
            "        if var(\"Coffin\" .. k) == 1 or var(\"Coffin\" .. k) == 3 then kicked(k) end",
            f"        evt.SetSprite({COG_COFFIN} + k, var(\"Coffin\" .. k) ~= 2)",
            f"        evt.SetSprite({COG_DEBRIS} + k, var(\"Coffin\" .. k) == 2)",
            "    end",
            "    set(\"Bottle\", 0)",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for k, p in ipairs(BOTTLE_STARTS) do",
            "        if math.abs(x - p[1]) < 300 and math.abs(y - p[2]) < 300 and math.abs(z - p[3]) < 500 then startBottle(k) end",
            "    end",
            "end",
            "",
        ]
        script.add(lines, (EV_LOAD, "Map load", None))
        return script.finish(on_load=[EV_LOAD])

    def report(self, build) -> dict:
        # DirLights (20 torch spots, FOV 210 against the wall, so nearly omnidirectional; Light54 over the well) fed
        # MM9's lightmaps: bake-only lights here (lighting.py reads the capped lights of work/lights.json).
        # Since the re-light (2026-10-30) bake.py drops these point-light copies and bakes the DirLights as MM9's spots
        # (profile dirlights: true); lighting.py alone still bakes them as point lights (the capture-matched alternative).
        for o in build.source.objects:
            if o["class"] != "DirLight" or o["name"] in NOT_BAKED:
                continue
            p = o["properties"]
            build.lights.append({"name": o["name"], "position_lt": p["Pos"], "kept": False,
                                 "position": build.project.native(p["Pos"]).round().tolist(),
                                 "radius": int(round(float(p["LightRadius"]) * SCALE)),
                                 "colour": [int(round(c)) for c in p["InnerColor"]],
                                 "bright_scale": float(p.get("BrightScale", 1.0)),
                                 "reason": "a floor point already under four lights"})
        for light in build.lights:
            if light["name"] in DIMMED_IN_BAKE:     # the octagon's great brazier, full strength in a bake-only light
                light["bright_scale"] *= DIMMED_IN_BAKE[light["name"]]
        return {"scripted": {"bottle_starts": self.bottle_starts}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, Beethoven()))
