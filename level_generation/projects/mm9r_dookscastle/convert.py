#!/usr/bin/env python3
"""
Dook's Castle, MM9 rework: MM9's DOOKSCASTLE.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_dookscastle/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_dookscastle/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the archway cuts, the ladder and the lake's texture; this file adds the lake's
wading surface, the castle's population (props.json from ../../props/mm9_dookscastle_claude, 47 actors) and its
scripted objects as native Lua, each citing its .scr (README.md, "Scripted objects"):
- the Dook's guards (DookGuardBasic.scr, DC_sargent.scr, DookSleepGaurd.scr through DookHostility.inc): friendly until
  the secret door opens (its OpenTrigger removes DOOK_HOSTILITY) or the party hurts or kills one (alarm bell);
- the shield over Tempbutton (RotatingDoor, OpenTrigger: doorslide open, Tempbutton lock): opens the secret door;
- the sleeping guards (DookSleepGaurd.scr) and their sargent (DC_sargent.scr), woken by SleepTrigger;
- the scurrying basilisks (ScurryCreature.scr), gone when ScurryTrigger0/1 fire;
- Baron Dook (NPC415.scr): MM9's RUDE dialogue 415;
- the two letters (BookLetter.scr 492, 493);
- the chest on the lake bed (TreasureChest6): a dive pad on the wading surface over it.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import csv  # noqa: E402
import re  # noqa: E402

import numpy as np  # noqa: E402

import dungeon  # noqa: E402
import review_root  # noqa: E402
from dungeon import lua, tables, water  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.source import ROOT, SCALE, facing_degrees  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402

PROPS = PROJECT / "props.json"
# The lake: MM9's ClearWater0 (ShowSurface 1, Ocean4.spr, SurfaceAlpha 0.9) floods the cavern under the rope bridges
# from its bed at -1920 LT to -1504. Swum since the shared water rule (2026-11-06, dungeon/water.py): the surface is
# non-solid, the bed is built, TreasureChest6 is an ordinary chest on it and Ladder0 is taken from the water (its foot 48
# LT under the surface, as MM9's). With overrides.yml `map: {swim: false}` the old stand-in: a solid surface the party
# wades on, the bed unbuilt under it (seed_exclude), the chest opened by a dive pad over it (map script).
LAKE_MODEL, LAKE_TEXTURE = "ClearWater0", "water:lake"
LAKE_TILE = 64.0
# Invisible ramps over the lake rim's rock steps (MM9's player climbs 40-48 LT risers; the party's step is 50 native,
# 20 LT): without them the party that goes down to the rope bridges cannot come back up (reach probes, README).
# (name, x0, x1, z0, z1 LT, the axis it rises along with its low and high ends (coordinate, y LT)).
RAMPS = [
    ("RampNorth1", 3960, 4068, 2290, 2408, "z", (2290, -1212), (2408, -1120)),   # bridge -1212 -> -1168 -> -1120
    ("RampNorth2", 3932, 3992, 2410, 2516, "x", (3992, -1120), (3932, -1080)),   # -1120 -> the landing at -1080
    ("RampWest", 2672, 2770, 1696, 1786, "x", (2770, -1148), (2672, -1080)),     # the planks -1148 -> -1112 -> -1080
]
# Sector minimum light (0 brightest, 31 black; the castle's is overrides.yml map.ambient 20): MM9's caves are dark and
# its lake cavern nearly black (DAT lightmaps: castle 0.38, tunnels 0.15, lake 0.017 of full): the bake's ambient floor
# follows each room's level. A room is named by an LT point inside it.
CAVE_AMBIENT = {(1000, -260, 3300): 27, (4800, -1330, 3500): 27, (3700, -1230, 1450): 29}
# The lake's surface reads as water (AGENT_BRIEF: a wading surface keeps MM9's visible blue surface): the engine's
# water shader on its Ocean4 frames (engine/liquids/liquids.yml, this world only, review root until the map is
# accepted), coloured toward MM9's SurfaceColor1 (0, 0, 64); shallow: the party wades.
LIQUID = """
  - id: ocean_mm9_dookscastle
    kind: water
    color: [70, 120, 170]
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [oceabym7ai]
"""
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"

# --- Events, timers, groups ---------------------------------------------------------------------------------------
EV_LOAD, EV_BUTTON, EV_SLEEP, EV_DIVE = 1, 70, 73, 76
EV_LETTERS = {"Prop5": (71, 492), "Prop6": (72, 493)}          # BookLetter.scr ScriptParams "492 Letter", "493 Letter 1"
EV_SCURRY = {"ScurryTrigger0": 74, "ScurryTrigger1": 75}
DAMAGE_HOOK, KILL_HOOK = 96, 97
T_POLL = 201
T_WAKE = 200                        # DC_sargent.scr: the sargent's round (its waits and a watchdog), each second
WAKE_SECONDS = 3                    # :WakeGuardUp Wait 0 3 WakeGuards
EV_SARGENT_AT_START, EV_SARGENT_AT_SLEEPER, EV_SARGENT_AT_END = 210, 211, 212   # his walks' arrivals
SARGENT_STOP = 100                  # native: he stops this far in front of a sleeper (MM9 WalkTo ... 10 LT; bodies collide)
SARGENT_LEG_SECONDS = 20            # a walk not done in this time ends where it was going (a door or the party in the way)
GROUP_GUARDS, GROUP_BARON, GROUP_SLEEPERS = 1, 2, 3
GROUP_SCURRY = {"ScurryTrigger0": 4, "ScurryTrigger1": 5}
SCURRY = {"ScurryTrigger0": ("ScurryBasilisk0", "ScurryBasilisk1", "ScurryBasilisk2"),
          "ScurryTrigger1": ("ScurryBasilisk3", "ScurryBasilisk4", "ScurryBasilisk5")}   # the triggers' Hide targets
GUARD_CLASSES = {"HalfOrcCaptain", "HalfOrcSoldier"}            # all run DookHostility.inc
FLIERS = {"WingedOddity", "WingedAberration", "WingedMutant"}   # Fly Y: they keep their DAT height
BARON_RUDE = 415                                                # NPC415.scr :OnUse DoRude 415
DIVE_CHEST = "TreasureChest6"
SWIM_LADDER_DEPTH = 160.0         # native: Ladder0's foot under the lake surface with swimming (scene hook)
                    # LT: the surface is cut to the cavern on this grid (runs of tiles in air per row)


def in_air(polygons: list, x: float, y: float, z: float) -> bool:
    """Whether (x, y, z) LT lies in air: the first polygon straight above faces down at it (a ceiling or the underside of
    a plank); in rock the first one above is the back of a floor."""
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


def surface(points_xz, y: float, texture: str, width: int, height: int, model: str, role: str) -> Polygon:
    """A horizontal face over a ring of (x, z) points, front upward, mapped one texel per LT (Beethoven's)."""
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture,
                      (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), 0x1088, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, polygon.mapping, 0x1088,
                          model, role)
    polygon.notes.update(width=width, height=height)
    return polygon


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


def install_liquid() -> None:
    """The lake's entry in the review root's liquid table (shared, so under the tables lock, added once)."""
    with tables.locked("review_tables.lock"):
        path = review_root.mirror_path("engine/liquids/liquids.yml")
        text = path.read_text()
        blocks = re.split(r"(?m)^(?=  - id: )", text)
        kept = "".join(b for b in blocks if not re.match(r"  - id: ocean_mm9_dookscastle\n", b)).rstrip("\n") + "\n"
        if kept + LIQUID != text:
            review_root.install("engine/liquids/liquids.yml", (kept + LIQUID).encode())


class DooksCastle(dungeon.Hooks):
    generator = "mm9r_dookscastle"
    # Tempbutton: MM9's invisible click box over Sheild0 (a quarter turn in the wall opens the secret door); doorslide,
    # the secret door (dookinside.dtx, no PushOpen): only the button opens it (overrides.yml click: false).
    mover_events = {"Tempbutton": (EV_BUTTON, "click")}

    # --- geometry -------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        source = build.source
        points = np.array(source.models[LAKE_MODEL].points, float)
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        alias = source.aliases[LAKE_TEXTURE]
        self.lake_y = y = float(points[:, 1].max())
        for polygon in polygons:
            polygon.bounds = (polygon.points.min(0), polygon.points.max(0))
        out, self.lake_faces = list(polygons), 0
        invisible = next(p for p in polygons if p.role == "invisible")
        for name, rx0, rx1, rz0, rz1, axis, low, high in RAMPS:
            def height(x, z):
                t = ((z if axis == "z" else x) - low[0]) / (high[0] - low[0])
                return low[1] + t * (high[1] - low[1])
            ring = np.array([[x, height(x, z), z] for x, z in ((rx0, rz0), (rx0, rz1), (rx1, rz1), (rx1, rz0))], float)
            ramp = Polygon(ring, [tuple(np.round(q, 1)) for q in ring], invisible.texture, invisible.mapping,
                           invisible.flags, name, "invisible")
            if ramp.normal[1] < 0:
                ramp = Polygon(ring[::-1].copy(), [tuple(np.round(q, 1)) for q in ring[::-1]], invisible.texture,
                               invisible.mapping, invisible.flags, name, "invisible")
            ramp.notes.update(invisible.notes)
            out.append(ramp)
        for row in np.arange(z0, z1, LAKE_TILE):
            run = None
            for column in np.arange(x0, x1 + LAKE_TILE, LAKE_TILE):
                wet = column < x1 and any(in_air(polygons, column + u * LAKE_TILE, y + 1, row + v * LAKE_TILE)
                                          for u in (0.02, 0.5, 0.98) for v in (0.02, 0.5, 0.98))
                if wet and run is None:
                    run = column
                elif not wet and run is not None:
                    top = min(row + LAKE_TILE, z1)
                    out.append(surface([(run, row), (run, top), (column, top), (column, row)], y, LAKE_TEXTURE,
                                       alias["width"], alias["height"], LAKE_MODEL, "static"))
                    self.lake_faces += 1
                    run = None
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source = build.content, build.source
        events = {name: event for name, (event, _) in EV_LETTERS.items()}
        events["Sheild0"] = EV_BUTTON                  # the shield over the invisible Tempbutton
        if PROPS.exists():
            content.props(PROPS, events=events, skip=() if water.swimming(build.project) else (DIVE_CHEST,))
        else:
            print("note: props.json is missing; no decorations or chests placed")
        # MM9's touch Triggers as boxes polled four times a second (the Chasm's route): they fire on any part of the
        # party in their box, as MM9's do, and need no level floor (ScurryTrigger0 stands on a slope).
        self.boxes = {}
        for name in ("SleepTrigger", *EV_SCURRY):
            p = source.properties(name)
            centre, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
            low, high = build.project.native(centre - dims), build.project.native(centre + dims)
            self.boxes[name] = [np.minimum(low, high).round().astype(int).tolist(),
                                np.maximum(low, high).round().astype(int).tolist()]
        self.pads = {}
        levels = {content.owner(np.array(point, float)): level for point, level in CAVE_AMBIENT.items()}
        self.room_ambient = levels
        write = build.package.write

        def write_with_levels(*args, **kwargs):
            for room in build.package.metadata["rooms"]:
                if room["id"] in levels:
                    room["min_ambient_light_level"] = levels[room["id"]]
            return write(*args, **kwargs)
        build.package.write = write_with_levels
        chest = source.properties(DIVE_CHEST)
        if not water.swimming(build.project):
            self.pads["DiveChest6"] = content.pad("DiveChest6", (chest["Pos"][0], self.lake_y, chest["Pos"][2]),
                                                  (48.0, 40.0, 48.0), EV_DIVE)
        content.report["omitted"].append({"anchor": "DOOK_HOSTILITY", "class": "ScriptObject",
                                          "reason": "the guards' object link (DookHostility.inc): the map variable "
                                                    "Hostile in the map script"})

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor, self.sleepers, self.guard_monsters = [], {}, [], set()
        for o in source.objects:
            if o["name"] not in bases:
                continue
            name, p, cls = o["name"], o["properties"], o["class"]
            base = bases[name]
            script = str(p.get("ScriptName") or "").lower()
            group, friendly, changes = 0, False, {}
            if cls in GUARD_CLASSES:
                group, friendly = GROUP_GUARDS, True        # DookHostility.inc: AddFriend Player until the link breaks
                self.guard_monsters.add(base["monster_id"])
            if "dooksleepgaurd" in script:
                group = GROUP_SLEEPERS
            if cls == "Baron":
                group, friendly = GROUP_BARON, True
            if "scurrycreature" in script:                 # ScurryCreature.scr: no fight, runs off to hide
                group = next(GROUP_SCURRY[t] for t, names in SCURRY.items() if name in names)
                friendly = True
            changes = placed_body(base["monster_id"], p)        # MM9's body: the row's, or at the DAT's own Scale
            record = content.actor(o, base, sector_of_room, group=group, friendly=friendly,
                                   floor_query_lt=p["Pos"][1] + 24, **changes)
            if cls in GUARD_CLASSES:
                # Friendly (no hostile or aggressor bit) but with the row's engagement type: when the alarm makes the
                # group hostile (evt.SetMonGroupBit) a guard engages the party it sees; with type 0 it never did.
                record["hostility_type"] = base["hostility_type"]
            if cls in FLIERS:                                # fliers keep their DAT height
                record["position"]["z"] = max(record["position"]["z"], int(round(p["Pos"][1] * SCALE)))
            if "dooksleepgaurd" in script:
                record["dormant"] = True                     # LoopAnim Sleep until WakeUp (DC_sargent.scr)
                self.sleepers.append(record["actor_index"])
            if cls == "Baron":
                record["mm9_rude_id"] = BARON_RUDE
                record["immobile"] = True
            record["mm9_source_object_index"] = o["index"]
            self.actor[name] = record["actor_index"]
            out.append(record)
        return out

    # --- scene ------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """Ladder0 rises out of the lake (its DAT foot 48 LT over MM9's surface): its foot goes down to the wading
        surface, or with swimming (the shared water rule) under it, where a party held at the surface (feet 134 under
        it) takes hold. The lake's liquid entry."""
        for ladder in scene.get("ladders", []):
            if ladder["id"] == "Ladder0":
                surface = round(self.lake_y * SCALE, 2)
                ladder["bottom"][2] = surface - SWIM_LADDER_DEPTH if water.swimming(build.project) else surface
        if build.project.install:
            install_liquid()

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Dook's Castle")
        # MM9 names the leaves "double door left 01": the DOORS table keys them with underscores (Lua identifiers).
        script.door = {name.replace(" ", "_"): door for name, door in script.door.items()}
        index = next(i for i, line in enumerate(script.lines) if line.startswith("local DOORS = {"))
        script.lines[index] = "local DOORS = {" + ", ".join(f"{k} = {v}" for k, v in sorted(script.door.items())) + "}"
        script.doors()
        script.chests()
        actor = self.actor
        container = next(c["container_id"] for c in build.content.report["chests"] if c["anchor"] == DIVE_CHEST)
        guards = ", ".join(f"[{m}] = true" for m in sorted(self.guard_monsters))
        sleepers = ", ".join(map(str, self.sleepers))
        # DC_sargent.scr's ScriptParams "HallwaySleeper 4 SMkr": the sleepers in its order and the markers
        guard_name, count, marker_name = build.source.properties("SleepCaptain")["ScriptParams"].split()
        order = [f"{guard_name}{k}" for k in range(int(count))]
        stops = []
        for name in order:
            p = build.source.properties(name)
            facing = np.radians(facing_degrees(p.get("Rotation")))
            at = build.project.native([p["Pos"][0], build.content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 24),
                                       p["Pos"][2]])
            stops.append(at + SARGENT_STOP * np.array([np.cos(facing), np.sin(facing), 0.0]) + np.array([0, 0, 1]))
        smkr = []
        for k in (0, 1):
            p = build.source.properties(f"{marker_name}{k}")["Pos"]
            smkr.append(build.project.native([p[0], build.content.floor_at(p[0], p[2], p[1] + 24), p[2]])
                        + np.array([0, 0, 1]))
        round_sleepers = ", ".join(str(actor[name]) for name in order)
        round_stops = ", ".join(lua.point(stop) for stop in stops)
        lines = [
            "-- The guards (DookGuardBasic.scr, DC_sargent.scr, DookSleepGaurd.scr, all #include DookHostility.inc): they",
            "-- AddFriend Player while the ScriptObject DOOK_HOSTILITY stands; its removal (the secret door's",
            "-- OpenTrigger, or TurnHostilityOn when the party hurts or kills a guard, with the alarm bell) makes every guard",
            "-- AddEnemy Player. Map variable Hostile carries the removal.",
            f"local GUARD_MONSTERS = {{{guards}}}",
            f"local SLEEPERS = {{{sleepers}}}",
            "local function applyHostility()",
            "    local hostile = var(\"Hostile\") == 1",
            f"    evt.SetMonGroupBit({GROUP_GUARDS}, MonsterBits.Hostile, hostile)",
            f"    evt.SetMonGroupBit({GROUP_SLEEPERS}, MonsterBits.Hostile, hostile)",
            "    if hostile then for _, index in ipairs(SLEEPERS) do evt.WakeActor(index) end end",
            "end",
            "local function hostility(bell)",
            "    if var(\"Hostile\") == 1 then return end",
            "    set(\"Hostile\", 1)",
            "    if bell then evt.PlaySoundName(\"events/alarmbell.wav\", 0, 0, 0) end",
            "    applyHostility()",
            "end",
            f"handlers[{DAMAGE_HOOK}] = function(context) if GUARD_MONSTERS[context.monsterId] then hostility(true) end end",
            f"handlers[{KILL_HOOK}] = function(context) if GUARD_MONSTERS[context.monsterId] then hostility(true) end end",
            "",
            "-- The shield over Tempbutton (RotatingDoor, OpenTriggers: doorslide open, Tempbutton lock): the secret door",
            "-- slides open and stays (Sticky, no close wait); its OpenTrigger removes DOOK_HOSTILITY.",
            f"handlers[{EV_BUTTON}] = function()",
            "    if var(\"SecretOpen\") == 1 then return end",
            "    set(\"SecretOpen\", 1)",
            "    open(\"Tempbutton_INV\")",
            "    open(\"doorslide\")",
            "    evt.PlaySoundName(\"door/doorlatch02.wav\", 0, 0, 0)",
            "    evt.PlaySoundName(\"events/boulderroll.wav\", 0, 0, 0)",
            "    hostility(false)",
            "end",
            "",
            "-- SleepTrigger -> SleepCaptain StartUp (DC_sargent.scr): the sargent walks to SMkr0 (:StartUp), then to",
            f"-- HallwaySleeper0..{len(order) - 1} in turn (:WakeGuards): at each he turns to it and wakes it (:WakeGuardUp, Trigger",
            f"-- WakeUp: it cowers, then stands watch), waits {WAKE_SECONDS} s and goes on; then he walks to SMkr1 and stays (:dn).",
            "-- MM9's PlayAnim aware there is not carried: his body (MM9's DookMilitia.abc too) has no such clip.",
            "-- Map variable SleepWoken: 0 not started, k walking to sleeper k or waiting after it, "
            f"{len(order) + 1} walking to SMkr1, {len(order) + 2} done.",
            "-- A dead sargent takes no StartUp, and once dead it walks to no more sleepers (MM9.receives); the alarm",
            "-- (DookHostility.inc AddEnemy) ends his round: he fights, and the alarm wakes every sleeper. Walks are not",
            "-- saved: a load during the round, or a walk not done in "
            f"{SARGENT_LEG_SECONDS} s, finishes it where it was going.",
            f"local CAPTAIN = {actor['SleepCaptain']}",
            f"local ROUND = {{{round_sleepers}}}   -- HallwaySleeper0..{len(order) - 1}",
            f"local ROUND_STOPS = {{{round_stops}}}   -- in front of each",
            f"local SMKR0, SMKR1 = {lua.point(smkr[0])}, {lua.point(smkr[1])}",
            "local round = {walking = false, wait = 0, ticks = 0}",
            "local function roundOver() return var(\"Hostile\") == 1 or not MM9.actorAlive(CAPTAIN) end",
            "local function sargentWalk(p, event)",
            "    round.walking, round.ticks, round.event, round.point = true, 0, event, p",
            "    evt.MoveActorTo(CAPTAIN, p[1], p[2], p[3], event)",
            f"    evt.StartTimer({T_WAKE}, seconds(1))",
            "end",
            "local function wakeGuards()   -- :WakeGuards",
            "    local step = var(\"SleepWoken\")",
            f"    if step <= #ROUND then sargentWalk(ROUND_STOPS[step], {EV_SARGENT_AT_SLEEPER})",
            f"    else set(\"SleepWoken\", #ROUND + 1); sargentWalk(SMKR1, {EV_SARGENT_AT_END}) end",
            "end",
            f"handlers[{EV_SLEEP}] = function()",
            "    if var(\"SleepWoken\") ~= 0 then return end",
            "    if not MM9.receives(\"dookscastle\", \"SleepCaptain\", \"StartUp\", CAPTAIN) then return end",
            "    set(\"SleepWoken\", 1)",
            f"    sargentWalk(SMKR0, {EV_SARGENT_AT_START})",
            "end",
            f"handlers[{EV_SARGENT_AT_START}] = function()",
            "    round.walking = false",
            "    if roundOver() or var(\"SleepWoken\") ~= 1 then return end",
            "    wakeGuards()",
            "end",
            f"handlers[{EV_SARGENT_AT_SLEEPER}] = function()   -- :WakeGuardUp",
            "    round.walking = false",
            "    local step = var(\"SleepWoken\")",
            "    if roundOver() or step < 1 or step > #ROUND then return end",
            "    local x, y = evt.GetMapActorPosition(ROUND[step])",
            "    if x ~= nil then evt.FaceActorTo(CAPTAIN, x, y, 0.5) end",
            "    evt.WakeActor(ROUND[step])",
            "    set(\"SleepWoken\", step + 1)",
            f"    round.wait = {WAKE_SECONDS}",
            f"    evt.StartTimer({T_WAKE}, seconds(1))",
            "end",
            f"handlers[{EV_SARGENT_AT_END}] = function()   -- :dn",
            "    round.walking = false",
            "    if var(\"SleepWoken\") == #ROUND + 1 then set(\"SleepWoken\", #ROUND + 2) end",
            "end",
            f"handlers[{T_WAKE}] = function()",
            f"    evt.StopTimer({T_WAKE})",
            "    local step = var(\"SleepWoken\")",
            "    if step == 0 or step > #ROUND + 1 then return end",
            "    if roundOver() then evt.StopActorMove(CAPTAIN) return end",
            "    if round.walking then",
            "        round.ticks = round.ticks + 1",
            f"        if round.ticks >= {SARGENT_LEG_SECONDS} then",
            "            local p = round.point",
            "            evt.StopActorMove(CAPTAIN)",
            "            evt.SetMapActorPosition(CAPTAIN, p[1], p[2], p[3])",
            "            handlers[round.event]()",
            "            return",
            "        end",
            "    elseif round.wait > 0 then",
            "        round.wait = round.wait - 1",
            "        if round.wait == 0 then wakeGuards() return end",
            "    else",
            "        return",
            "    end",
            f"    evt.StartTimer({T_WAKE}, seconds(1))",
            "end",
            "local function finishRound()   -- a load during the round",
            "    local step = var(\"SleepWoken\")",
            "    if step == 0 or step > #ROUND + 1 then return end",
            "    for k = math.max(step, 1), #ROUND do evt.WakeActor(ROUND[k]) end",
            "    set(\"SleepWoken\", #ROUND + 2)",
            "    if MM9.actorAlive(CAPTAIN) and var(\"Hostile\") ~= 1 then "
            "evt.SetMapActorPosition(CAPTAIN, SMKR1[1], SMKR1[2], SMKR1[3]) end",
            "end",
            "",
            "-- The touch Triggers, polled four times a second (fire on any part of the party in the box, then Off).",
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z + 170 >= b[1][3] and z <= b[2][3] end",
            "local BOXES = {" + ", ".join(
                f"{{name = \"{n}\", event = {EV_SLEEP if n == 'SleepTrigger' else EV_SCURRY[n]}, "
                f"box = {{{lua.point(b[0])}, {lua.point(b[1])}}}}}" for n, b in self.boxes.items()) + "}",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for _, b in ipairs(BOXES) do",
            "        if var(\"Fired\" .. b.name) == 0 and inBox(b.box, x, y, z) then",
            "            set(\"Fired\" .. b.name, 1)",
            "            handlers[b.event]()",
            "        end",
            "    end",
            "end",
            "",
            "-- ScurryCreature.scr: the small basilisks run to their HideMarker at six times their speed and vanish (Hide,",
            "-- sent by ScurryTrigger0/1, which then turn Off).",
        ]
        for name, event in EV_SCURRY.items():
            lines += [f"handlers[{event}] = function()   -- {name}",
                      f"    if var(\"{name}\") == 1 then return end",
                      f"    set(\"{name}\", 1)",
                      "    evt.PlaySoundName(\"animsounds/dragonredhop.wav\", 0, 0, 0)",
                      # Hide (ScurryCreature.scr :GoHide, then RemoveObject): a dead basilisk takes none, its corpse
                      # stays
                      *[f"    if MM9.receives(\"dookscastle\", \"{n}\", \"Hide\", {actor[n]}) then "
                        f"MM9.removeActor({actor[n]}) end" for n in SCURRY[name] if n in actor],
                      "end"]
        swim = water.swimming(build.project)
        lines += [""] if swim else [
            "",
            f"-- TreasureChest6 lies on the lake bed (MM9: the party dives). No swimming: the wading surface over it opens it.",
            f"handlers[{EV_DIVE}] = function()",
            f"    evt.OpenChest({container})",
            "end",
            "",
        ]
        for name, (event, number) in EV_LETTERS.items():
            title, text = letter(number)
            lines += [f"-- {name}: BookLetter.scr \"{number} Letter\" (DoLetter {number}).",
                      f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0); "
                      f"evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end", ""]
        lines += [
            "-- Map load: the guards' hostility as saved (DookHostility.inc OnPostMiniSaveLoad), the secret door's state.",
            f"handlers[{EV_LOAD}] = function()",
            "    applyHostility()",
            "    finishRound()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    if var(\"SecretOpen\") == 1 then open(\"Tempbutton_INV\") open(\"doorslide\") end",
            "end",
            ""]
        script.add(lines, (DAMAGE_HOOK, "Guards hurt", None), (KILL_HOOK, "Guards killed", None),
                   (EV_BUTTON, "Shield", "Shield"), (EV_SLEEP, "SleepTrigger", None), (T_WAKE, "Wake", None, "timer"),
                   (EV_SARGENT_AT_START, "Sargent", None), (EV_SARGENT_AT_SLEEPER, "Sargent", None),
                   (EV_SARGENT_AT_END, "Sargent", None),
                   (T_POLL, "Trigger volumes", None, "timer"),
                   *[(e, n, None) for n, e in EV_SCURRY.items()], *([] if swim else [(EV_DIVE, "Dive", None)]),
                   *[(e, "Letter", "Letter") for e, _ in EV_LETTERS.values()], (EV_LOAD, "Map load", None))
        script.hooks += [f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Guards hurt", handlers[{DAMAGE_HOOK}])',
                         f'RegisterMonsterKilledHook({KILL_HOOK}, "Guards killed", handlers[{KILL_HOOK}])']
        script.registrations = [r for r in script.registrations if r[0] not in (DAMAGE_HOOK, KILL_HOOK)]
        return script.finish(on_load=[EV_LOAD])

    def report(self, build) -> dict:
        return {"room_ambient": getattr(self, "room_ambient", {}), "lake_faces": getattr(self, "lake_faces", 0), "lake_y_lt": getattr(self, "lake_y", None),
                "scripted": {"actors": self.actor, "sleepers": self.sleepers, "pads": self.pads}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, DooksCastle()))
