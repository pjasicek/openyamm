#!/usr/bin/env python3
"""
The Arena, MM9 rework: MM9's THEARENA.dat (Thjorgard's arena) as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_thearena/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_thearena/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the stair cut and the glass; this file adds the arena's population (props.json from
../../props/mm9_thearena_claude, four NPCs and two clan soldiers) and its scripted objects as native Lua, each citing
its .scr (README.md, "Scripted objects"):
- the Arena Master (RUDE 430, Arena.scr :OnRude): Page / Squire / Knight / Lord fights against monsters drawn from
  MM9's own arena table (PICKMON.inc, pickmon.py) at ArenaFight.scr's levels, counts and prizes; the bouts the party
  can watch and bet on (Arena.scr :pick, :OnWatch, :OnBet, :OnMonsterA/B, :OnMonsterDead; ArenaCreature.scr,
  ArenaVictory.scr, ArenaMini.scr); the Lord win for the third labor (key 214 -> 217);
- the arena's doors and pens (Arena.scr :LockDoors, ArenaFight.scr :OnPlayerInTheHouse, :OnDead);
- Jarl Sven's double, his guards and the assassin Byri the Scarred (SvenArena.scr, NPC245.scr, RUDE 428 and 245).
MM9's arena runs on its own keys and RUDE rows, not on MM6-MM8's arena rules: the shared ArenaRuntime (NPC topic 704,
6-20 opponents, MM8 awards, a teleport to the floor) is not used (README, "Why not ArenaRuntime").
"""

from __future__ import annotations

import dataclasses
import json
import struct
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import dungeon  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
import pickmon  # noqa: E402

PROPS = PROJECT / "props.json"
BARS_MODEL = "WorldObject2"           # the bars of the Arena Master's counter
SKY_TEXELS_PER_LT = 0.2            # the sky faces: one sky04 tile about 2 500 LT wide (Lindisfarne, Verhoffin, Tasar)

EV_ARENA_DOOR, EV_WEST_PEN, EV_EAST_PEN = 100, 101, 102
EV_TOKEN_A, EV_TOKEN_B = 110, 111   # the betting slips at Marker3 / Marker4 (ArenaMini.scr's figurines)
T_POLL = 120                        # the 0.25 s poll: PlayerInTheHouse, MM9's Waits
KILL_HOOK = 130
COG_TOKEN_A, COG_TOKEN_B = 300, 301

# Groups: the NPCs, Sven's party, Byri; fights and bouts take fresh groups from 100 on (map variable Serial).
GROUP_MASTER, GROUP_SVEN, GROUP_BYRI, GROUP_SPAWN_BASE = 1, 2, 3, 100

# MM9 keys (Arena.scr, ArenaFight.scr, RUDE 430/245/428)
KEY_PAGE, KEY_SQUIRE, KEY_KNIGHT, KEY_LORD = 1004, 1005, 1006, 1007
KEY_DONE_TODAY, KEY_WATCH, KEY_BOUT, KEY_BETTING, KEY_WON_BET, KEY_PICKED, KEY_FIGHT_WON = \
    1009, 1010, 1011, 1017, 1018, 1019, 1020
BET_KEYS = {1012: 50, 1013: 100, 1014: 250, 1015: 500, 1016: 1000}
KEY_LABOR, KEY_LABOR_DONE = 214, 217        # NPC61 (Fridleif): fight at Lord level and win
KEY_SVEN_PLOT, KEY_SVEN_SAVED = 230, 231    # NPC3 (Sven Forkbeard) / NPC245 (Byri the Scarred)
KEY_DOUBLE = 1034                           # SvenArena.scr :OnUse / :OnRude (RUDE 428's "You're Sven's double?")
RESET_KEYS = [1004, 1005, 1006, 1007, 1008, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019]

# ArenaFight.scr per difficulty: level range (x the party's mean level), opponents 1..n, prize per level per opponent
FIGHTS = {1: (0.8, 1.3, 2, 20), 2: (0.8, 1.5, 3, 30), 3: (1.0, 1.7, 4, 50), 4: (1.0, 2.5, 5, 100)}

# NPC bodies (no MM9 monster rows for these classes): the Arena Master (ShopkeeperElfMaleB, PeasantMale.abc) an elf
# peasant, Byri (CommonerHuman2MaleB, PeasantMale.abc) Drangheim's PeasantMale row, Sven's double (Sven.abc) a human
# peasant, the clan soldiers MM9's Guard (ClanSoldier.abc is the guards' model).
NPCS = {
    "ShopkeeperElfMaleB0": {"row": 343, "name": "Arena Master", "group": GROUP_MASTER, "hidden": False},
    "CommonerHuman2MaleB0": {"row": 367, "name": "Byri the Scarred", "group": GROUP_BYRI, "hidden": True},
    "SvenArena": {"row": 358, "name": "Sven Forkbeard", "group": GROUP_SVEN, "hidden": True},
    "ClanSoldier0": {"row": 9111, "name": "Clan Soldier", "group": GROUP_SVEN, "hidden": True},
    "ClanSoldier1": {"row": 9111, "name": "Clan Soldier", "group": GROUP_SVEN, "hidden": True},
}
# MM9's bodies (playbook: ABC AnimBinding extents x Scale x 2.56): PeasantMale.abc and Sven.abc (12, 34) LT half
# extents, ClanSoldier.abc (15, 38); every one at Scale 1.
BODIES = {"ShopkeeperElfMaleB0": (12, 34), "CommonerHuman2MaleB0": (12, 34), "SvenArena": (12, 34),
          "ClanSoldier0": (15, 38), "ClanSoldier1": (15, 38)}
DESCRIPTOR_TABLES = [ROOT / "assets_dev/engine/data_tables/monster_descriptors.txt",
                     ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt"]
DATA_TABLES = [ROOT / "assets_dev/engine/data_tables/monster_data.txt",
               ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"]


def rude_exit_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a dialogue with actor object `index` runs when it closes."""
    return 50000 + index


def rude_use_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a click on dialogue actor object `index` runs instead of opening it."""
    return 53000 + index


def rude_id(properties: dict) -> int:
    """MM9's NPCNbr (a float stored as its bits) when DoRude: the old importer's mm9_npc_rude_id."""
    if not properties.get("DoRude"):
        return 0
    raw = properties.get("NPCNbr")
    if isinstance(raw, int):
        value = struct.unpack("<f", struct.pack("<I", raw))[0]
        return int(value) if value.is_integer() and 0 < value < 10000 else 0
    return 0


def table_rows(paths) -> dict:
    out = {}
    for path in paths:
        for line in path.read_text(encoding="latin-1").splitlines():
            cells = line.split("\t")
            if cells and cells[0].isdigit():
                out[int(cells[0])] = cells
    return out


def lua_str(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


class TheArena(dungeon.Hooks):
    generator = "mm9r_thearena"
    mover_events = {"ArenaDoor": (EV_ARENA_DOOR, "click"), "WestPen": (EV_WEST_PEN, "click"),
                    "EastPen": (EV_EAST_PEN, "click")}

    # --- geometry -------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        """The open sky over the stadium (MM9's skymarker faces show its SnowMtns sky box): sky04 stretched, one tile
        about 2 500 LT wide; ceilings across x and z, walls along and down (Lindisfarne's mapping)."""
        self.sky_faces, out = 0, []
        for polygon in polygons:
            if polygon.model == BARS_MODEL:
                # The bars of the Arena Master's counter (MetalBarGrey in an invisible shell, MM9 solid): the party
                # talks to him through them, and the indoor pick stops at a solid or glass face. The bars become an
                # untouchable cut-out (TRIGGER_nonsolid_*, drawn translucent by the scene hook), the shell goes;
                # the counter (48 LT, over the party's step) still keeps the party out of the booth.
                if polygon.role == "invisible":
                    self.bars_dropped = getattr(self, "bars_dropped", 0) + 1
                    continue
                polygon = dataclasses.replace(polygon, role="nonsolid")
            out.append(polygon)
        polygons = out
        for polygon in polygons:
            if "skymarker" in polygon.texture.lower():
                origin = np.asarray(polygon.mapping[0], float)
                n = polygon.normal
                if abs(n[1]) > 0.7:
                    u, v = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
                else:
                    u = np.cross([0.0, 1.0, 0.0], n)
                    u /= np.linalg.norm(u)
                    v = np.array([0.0, -1.0, 0.0])
                polygon.mapping = (origin, u * SKY_TEXELS_PER_LT, v * SKY_TEXELS_PER_LT)
                self.sky_faces += 1
        return polygons

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        if PROPS.exists():
            content.props(PROPS)
        else:
            print("note: props.json is missing; no decorations placed")
        # The betting slips: where ArenaMini.scr's figurines of the next bout stand on the counter (Marker3: monster A,
        # Marker4: monster B); a click names the contestant or, with a wager placed, bets on it.
        for name, marker, event, cog in (("BetSlipA", "Marker3", EV_TOKEN_A, COG_TOKEN_A),
                                         ("BetSlipB", "Marker4", EV_TOKEN_B, COG_TOKEN_B)):
            p = source.properties(marker)["Pos"]
            floor = content.floor_at(p[0], p[2], p[1])
            content.entity(name, "mm9_scroll", project.native([p[0], floor, p[2]]), 90.0, primary=cog, secondary=event)
        self.points = {o["name"]: project.native(o["properties"]["Pos"]).round().astype(int).tolist()
                       for o in source.objects if o["class"] == "Marker"}
        for name in self.points:            # markers stand on the floor under them (spawn and walk targets)
            p = source.properties(name)["Pos"]
            floor = content.floor_at(p[0], p[2], p[1] + 8)
            if floor is not None:
                self.points[name][2] = int(round(floor * SCALE)) + 1
        # The pens' mouths on the arena side (the pen doors stand at LT x +-600; Marker0/1 at +672 / -688 inside).
        self.gates = [[int(round(x * SCALE)), 0, 1] for x in (520, -520)]
        p = source.properties("PlayerInTheHouse")
        centre, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
        low, high = project.native(centre - dims), project.native(centre + dims)
        self.house_box = [np.minimum(low, high).round().astype(int).tolist(),
                          np.maximum(low, high).round().astype(int).tolist()]
        report = content.report["omitted"]
        for name in ("WinCheerTrigger0", "LooseBooTrigger0"):
            report.append({"anchor": name, "class": "Trigger", "reason": "a relay SvenArena.scr triggers to switch the "
                           "CrowdCheer/CrowdBoo AmbientSounds on: the map Lua plays the cheer instead"})

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        descriptors, data = table_rows(DESCRIPTOR_TABLES), table_rows(DATA_TABLES)
        out, self.actor, self.objects = [], {}, {}
        for o in source.objects:
            spec = NPCS.get(o["name"])
            if spec is None:
                continue
            row = spec["row"]
            d, m = descriptors[row], data[row]
            half, tall = BODIES[o["name"]]
            base = {"name": spec["name"], "attributes": 0, "hp": int(m[4]), "hostility_type": 0,
                    "monster_info_id": row, "monster_id": row, "radius": int(round(half * SCALE)),
                    "height": int(round(2 * tall * SCALE)), "move_speed": int(d[4])}
            actor = content.actor(o, base, sector_of_room, group=spec["group"], hidden=spec["hidden"], friendly=True,
                                  floor_query_lt=o["properties"]["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            rude = rude_id(o["properties"])
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = True
            self.actor[o["name"]] = actor["actor_index"]
            self.objects[o["name"]] = o["index"]
            out.append(actor)
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "The Arena")
        script.chests()
        ranges, groups = pickmon.parse()
        resolved = pickmon.rows({c[0] for g in groups.values() for c in g if c})
        self.unresolved = sorted(k for k, v in resolved.items() if v is None)
        group_lines = []
        for n, cases in sorted(groups.items()):
            cells = [f"{{{resolved[c[0]]}, {c[1]}, {lua_str(c[0])}}}" if c and resolved[c[0]] else "false"
                     for c in cases]
            group_lines.append(f"    [{n}] = {{{', '.join(cells)}}},")
        pts, actor, objects = self.points, self.actor, self.objects
        master, byri, sven = objects["ShopkeeperElfMaleB0"], objects["CommonerHuman2MaleB0"], objects["SvenArena"]
        keys = lambda values: "{" + ", ".join(map(str, values)) + "}"   # noqa: E731
        lines = [
            "local function hasKey(k) return MM9.hasKey(k) == 1 end",
            "",
            "-- A scheduler on the 0.25 s poll (MM9's Wait): after(seconds, fn).",
            "local tick, tasks = 0, {}",
            "local function after(s, fn) table.insert(tasks, {at = tick + math.max(1, math.floor(s * 4 + 0.5)), fn = fn}) end",
            "",
            "-- Markers (native, on the floor) and the PlayerInTheHouse box.",
            "local P = {" + ", ".join(f"{k} = {lua.point(v)}" for k, v in sorted(pts.items())) + "}",
            f"local HOUSE = {{{lua.point(self.house_box[0])}, {lua.point(self.house_box[1])}}}",
            f"local GATE_EAST, GATE_WEST = {lua.point(self.gates[0])}, {lua.point(self.gates[1])}   -- the pens' mouths",
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z >= b[1][3] - 40 and z <= b[2][3] + 40 end",
            "",
            "-- Doors: MM9's arena double door (RotatingDoor0/1), the west pen (RotatingDoor2/3) and the east pen",
            "-- (RotatingDoor4/5). Arena.scr :LockDoors / :UnLockDoors and ArenaCreature.scr lock them (map variables).",
            "local LEAVES = {ArenaDoor = {\"RotatingDoor0\", \"RotatingDoor1\"}, WestPen = {\"RotatingDoor2\", "
            "\"RotatingDoor3\"}, EastPen = {\"RotatingDoor4\", \"RotatingDoor5\"}}",
            "local function door(group, action) for _, leaf in ipairs(LEAVES[group]) do evt.SetDoorState(DOORS[leaf], action) end end",
            "local function lock(group, on) set(\"Lock\" .. group, on and 1 or 0) end",
            "local function lockDoors() door(\"ArenaDoor\", DoorAction.Close); lock(\"ArenaDoor\", true) end   -- Arena.scr :LockDoors",
            "local function unlockDoors() lock(\"ArenaDoor\", false) end                                          -- :UnLockDoors",
            "local svenWalk",
            "local function clickDoor(group)",
            "    if var(\"Lock\" .. group) == 1 then evt.StatusText(\"The door is locked.\") return end",
            "    door(group, DoorAction.Trigger)",
            "    if group == \"ArenaDoor\" then svenWalk() end            -- RotatingDoor0's OpenTrigger: SvenArena Walk",
            "end",
            f"handlers[{EV_ARENA_DOOR}] = function() clickDoor(\"ArenaDoor\") end",
            f"handlers[{EV_WEST_PEN}] = function() clickDoor(\"WestPen\") end",
            f"handlers[{EV_EAST_PEN}] = function() clickDoor(\"EastPen\") end",
            "",
            "-- MM9's arena table (PICKMON.inc :PickMonster): a level picks a group, the group one of its monsters at random",
            "-- {row, MM9 level, class}; false where the class has no runtime row (the clan soldiers, the poor town guards:",
            "-- such a draw is drawn again, as MM9 draws again a monster outside the level range).",
            "local RANGES = {" + ", ".join(f"{{{a}, {b}, {g}}}" for a, b, g in ranges) + "}",
            "local GROUPS = {", *group_lines, "}",
            "local function pickMonster(level)",
            "    for _, r in ipairs(RANGES) do",
            "        if level >= r[1] and level <= r[2] then local g = GROUPS[r[3]] return g[math.random(1, #g)] end",
            "    end",
            "    return nil",
            "end",
            "",
            "-- ArenaFight.scr :GetCharLevel: the mean level of the party.",
            "local function memberLevel(i)",
            "    evt.ForPlayer(i)",
            "    local lo, hi = 1, 400",
            "    while lo < hi do",
            "        local mid = math.floor((lo + hi + 1) / 2)",
            "        if evt.Cmp(VarTag.BaseLevel, mid) then lo = mid else hi = mid - 1 end",
            "    end",
            "    return lo",
            "end",
            "local function partyLevel()",
            "    local n, sum = math.max(1, evt.GetPartyMemberCount()), 0",
            "    for i = 0, n - 1 do sum = sum + memberLevel(i) end",
            "    evt.ForPlayer(Players.Current)",
            "    return math.max(1, math.floor(sum / n + 0.5))",
            "end",
            "",
            "-- Fresh monster groups (fights and bouts); a reload hides what a former visit left standing.",
            "local function newGroup() set(\"Serial\", var(\"Serial\") + 1) return " + str(GROUP_SPAWN_BASE) + " + var(\"Serial\") end",
            "local function spawn(row, at, group, hostile)",
            "    local hp = (70 + math.random(0, 80)) / 100                 -- :Startup / :Init: HitPoints x 0.7-1.5",
            "    return evt.SummonMonstersById({monster = row, x = at[1], y = at[2], z = at[3], radius = 48, count = 1,",
            "        group = group, hostile = hostile, loot = false, hpScale = hp})   -- GaveTreasure TRUE: no treasure",
            "end",
            "",
            "local function reset() for _, k in ipairs(" + keys(RESET_KEYS) + ") do MM9.takeKey(k) end end   -- Arena.scr :Reset",
            "",
            "-- ---- Fights against the party (ArenaFight.scr :OnPage, :OnSquire, :OnKnight, :OnLord) -------------------------",
            f"local FIGHTS = {{{', '.join(f'[{k}] = {{{a}, {b}, {n}, {r}}}' for k, (a, b, n, r) in FIGHTS.items())}}}",
            "local function prepareFight(difficulty)",
            "    local f, level = FIGHTS[difficulty], partyLevel()",
            "    local low, high = math.floor(level * f[1]), math.floor(level * f[2])",
            "    if level > 89 then high = 89 end",
            "    if level < 4 then high = 4 end",
            "    if high < low then high = low end",
            "    local count = math.random(1, f[3])",
            "    set(\"Reward\", count * level * f[4])",
            "    set(\"FightCount\", count)",
            "    for i = 1, count do",
            "        local pick, best = nil, nil",
            "        for attempt = 1, 400 do                         -- MM9: Goto OnPage until a monster in the range",
            "            local m = pickMonster(math.random(math.max(0, low), math.max(0, high)))",
            "            if m then",
            "                if m[2] >= low and m[2] <= high then pick = m break end",
            "                local miss = math.max(low - m[2], m[2] - high)",
            "                if best == nil or miss < best[1] then best = {miss, m} end",
            "            end",
            "        end",
            "        pick = pick or best[2]                          -- no monster of the range at all: the nearest",
            "        set(\"FightMonster\" .. i, pick[1])",
            "    end",
            "    if difficulty == 4 and hasKey(" + str(KEY_LABOR) + ") then set(\"Lord\", 1) end   -- ArenaFight :OnLord -> Arena :OnLord",
            f"    MM9.giveKey({KEY_BOUT})                                -- ArenaFightPlayer.scr :Main",
            "    set(\"Waiting\", 1)                                     -- SetConsoleNumVar WaitingForPlayer, TRUE",
            "end",
            "-- :OnPlayerInTheHouse: the party past the arena doors shuts them behind it; the opponents come out of the pens",
            "-- (ArenaFightPlayer.scr :Startup: the first at Marker0 in the east pen, the others at Marker1 in the west).",
            "local function startFight()",
            "    set(\"Waiting\", 0)",
            "    lockDoors()",
            "    local group = newGroup()",
            "    set(\"FightGroup\", group)",
            "    for i = 1, var(\"FightCount\") do",
            "        spawn(var(\"FightMonster\" .. i), i == 1 and P.Marker0 or P.Marker1, group, true)",
            "    end",
            "    door(\"EastPen\", DoorAction.Open); door(\"WestPen\", DoorAction.Open)",
            "end",
            "local function fightDead()   -- ArenaFight.scr :OnDead: all down -> key 1020, the arena door unlocked",
            "    local group = var(\"FightGroup\")",
            "    if group == 0 or not evt.CheckMonstersKilled(ActorKillCheck.Group, group, 0, true) then return end",
            "    set(\"FightGroup\", 0)",
            f"    MM9.giveKey({KEY_FIGHT_WON})",
            "    unlockDoors()",
            "    evt.PlaySoundName(\"ambient/people/crowdnoise-cheer01.wav\", 0, 0, 0)",
            "end",
            "local function fightWin()    -- Arena.scr :FightWin",
            "    if var(\"Lord\") == 1 then",
            f"        MM9.giveKey({KEY_LABOR_DONE})                      -- the third labor: no purse (MM9)",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            "        set(\"Lord\", 0)",
            "    else",
            "        MM9.giveGold(var(\"Reward\"))",
            "    end",
            f"    MM9.giveKey({KEY_DONE_TODAY}); MM9.takeKey({KEY_FIGHT_WON})",
            "end",
            "",
            "-- ---- Bouts to watch and bet on (Arena.scr :pick, :Init, :OnWatch, :OnBet, :OnMonsterDead) ------------------",
            "local function pickPair()   -- Arena.scr :pick: monster A at a random level, B within 4 levels of it",
            "    local a, b, la",
            "    repeat la = math.random(1, 89) a = pickMonster(la) until a",
            "    local low = math.max(1, la - 4)",
            "    local high = math.min(89, low + 8)",
            "    low = high - 8",
            "    repeat",
            "        local lb = math.random(low, high)",
            "        if lb == la then lb = la - 1 if lb < 1 then lb = la + 1 end end",
            "        b = pickMonster(lb)",
            "    until b",
            "    set(\"BoutA\", a[1]); set(\"BoutLevelA\", a[2]); set(\"BoutB\", b[1]); set(\"BoutLevelB\", b[2])",
            "    NAMES.A, NAMES.B = a[3], b[3]",
            "end",
            "local function initBout()   -- Arena.scr :Init: three bouts a visit, then 'no more fights today'",
            f"    if var(\"Bouts\") >= 3 then MM9.giveKey({KEY_DONE_TODAY}) return end",
            "    set(\"Bouts\", var(\"Bouts\") + 1)",
            "    pickPair()",
            "end",
            "local function watch()      -- Arena.scr :OnWatch: A from the east pen, B from the west; the crowd cheers",
            "    local ga, gb = newGroup(), newGroup()",
            "    set(\"BoutGroupA\", ga); set(\"BoutGroupB\", gb); set(\"BoutDead\", 0)",
            "    local a, b = var(\"BoutA\"), var(\"BoutB\")",
            "    evt.SetMonsterRelation(a, b, 2); evt.SetMonsterRelation(b, a, 2)   -- :OnArrive HateAll (ArenaCreature :OnHate)",
            f"    MM9.giveKey({KEY_BOUT})                                     -- ArenaCreature.scr :Main",
            "    lockDoors()",
            "    evt.PlaySoundName(\"ambient/people/crowdnoise-cheer01.wav\", 0, 0, 0)",
            "    door(\"WestPen\", DoorAction.Open); door(\"EastPen\", DoorAction.Open)   -- :Init: the pens open",
            "    -- MM9 runs both to Marker2 and sets them on each other there. Native actors do not walk to a marker and do",
            "    -- not wake in a pen out of the party's room: each steps out of its open pen (spawned at the gate on the",
            "    -- arena side), where the two see each other across the floor.",
            "    after(3, function()",
            "        spawn(a, GATE_EAST, ga, false)                          -- AddFriend Player: not hostile to the party",
            "        spawn(b, GATE_WEST, gb, false)",
            "    end)",
            "end",
            "local function boutOver()   -- ArenaVictory.scr :RunAway, :Delete: the winner leaves, the next pair is drawn",
            f"    MM9.takeKey({KEY_WATCH}); MM9.takeKey({KEY_BOUT}); MM9.takeKey({KEY_BETTING})",
            "    for _, g in ipairs({var(\"BoutGroupA\"), var(\"BoutGroupB\")}) do",
            "        if g ~= 0 then evt.SetMonGroupBit(g, MonsterBits.Invisible, true) end",
            "    end",
            "    set(\"BoutGroupA\", 0); set(\"BoutGroupB\", 0)",
            "    door(\"WestPen\", DoorAction.Close); door(\"EastPen\", DoorAction.Close)",
            "    unlockDoors()",
            "    initBout()",
            "end",
            "local function boutDead()   -- Arena.scr :OnMonsterDead",
            "    local ga, gb = var(\"BoutGroupA\"), var(\"BoutGroupB\")",
            "    if ga == 0 then return end",
            "    local deadA = evt.CheckMonstersKilled(ActorKillCheck.Group, ga, 0, true)",
            "    local deadB = evt.CheckMonstersKilled(ActorKillCheck.Group, gb, 0, true)",
            "    if deadA and deadB then                                      -- both of them: reset, the next pair",
            "        reset(); set(\"BoutGroupA\", 0); set(\"BoutGroupB\", 0); initBout(); unlockDoors()",
            "        return",
            "    end",
            "    if (deadA or deadB) and var(\"BoutDead\") == 0 then",
            "        set(\"BoutDead\", 1)",
            f"        MM9.takeKey({KEY_PICKED})",
            "        local winner = deadA and \"B\" or \"A\"",
            f"        if hasKey({KEY_BETTING}) then                               -- :OnMonsterAWin / :OnMonsterBWin",
            "            if var(\"BetOn\") == (winner == \"A\" and 1 or 2) then",
            f"                MM9.giveKey({KEY_WON_BET})",
            "                evt.StatusText(\"You won your bet! The Arena Master has your winnings.\")",
            "            else",
            "                evt.StatusText(\"You lost your bet.\")",
            "            end",
            "        end",
            "        evt.PlaySoundName(\"ambient/people/crowdnoise-cheer01.wav\", 0, 0, 0)",
            "        after(20, boutOver)                                       -- Wait 20 -> :BeVictorious",
            "    end",
            "end",
            "local function bet()        -- Arena.scr :OnBet2: the wager is taken, or 'no gold' and the talk is undone",
            "    lockDoors()",
            f"    for key, amount in pairs({{{', '.join(f'[{k}] = {v}' for k, v in BET_KEYS.items())}}}) do",
            "        if hasKey(key) then",
            "            if MM9.hasGold(amount) == 0 then",
            "                evt.StatusText(\"You do not have enough gold.\")    -- NoGold.inc",
            "                reset(); unlockDoors()",
            "            else",
            "                MM9.takeKey(key); MM9.takeGold(amount); set(\"BetAmount\", amount)",
            "            end",
            "            return",
            "        end",
            "    end",
            "end",
            "local function slip(which)  -- ArenaMini.scr :OnUse, Arena.scr :OnMonsterA / :OnMonsterB",
            "    local mine, other = var(\"BoutLevel\" .. which), var(\"BoutLevel\" .. (which == \"A\" and \"B\" or \"A\"))",
            f"    if not hasKey({KEY_BETTING}) or hasKey({KEY_PICKED}) then",
            "        local name = tr(NAMES[which] or \"?\")",
            "        if which == \"A\" then",
            "            evt.StatusText(tr(\"Contestant from the east gate: {name} (level {level})\", {name = name, level = mine}))",
            "        else",
            "            evt.StatusText(tr(\"Contestant from the west gate: {name} (level {level})\", {name = name, level = mine}))",
            "        end",
            "        return",
            "    end",
            "    set(\"BetOn\", which == \"A\" and 1 or 2)",
            "    local d, amount = other - mine, var(\"BetAmount\")",
            "    if d < 0 then amount = math.floor(amount * 1.5) elseif d > 5 then amount = amount * 2 end   -- MM9's odds",
            "    set(\"BetAmount\", amount)",
            f"    MM9.giveKey({KEY_PICKED})",
            "    evt.StatusText(tr(\"You bet on the {name}.\", {name = NAMES[which] and tr(NAMES[which]) or tr(\"contestant\")}))",
            "    after(3, watch)                                               -- wait 1 3 Fight -> Arena :OnWatch",
            "end",
            f"handlers[{EV_TOKEN_A}] = function() slip(\"A\") end",
            f"handlers[{EV_TOKEN_B}] = function() slip(\"B\") end",
            "local function giveWin()    -- Arena.scr :GiveWin",
            f"    MM9.takeKey({KEY_WON_BET}); MM9.takeKey({KEY_PICKED}); reset()",
            "    MM9.giveGold(var(\"BetAmount\"))",
            "end",
            "",
            f"-- The Arena Master (Arena.scr :OnRude, after RUDE 430): the keys his rows gave decide what happens.",
            f"handlers[{rude_exit_event(master)}] = function()",
            f"    if not hasKey({KEY_SVEN_SAVED}) and hasKey({KEY_SVEN_PLOT}) then reset() return end   -- Sven's day: no fights",
            f"    if hasKey({KEY_WON_BET}) then giveWin() return end",
            f"    if hasKey({KEY_DONE_TODAY}) then return end",
            f"    if hasKey({KEY_BOUT}) then if hasKey({KEY_FIGHT_WON}) then fightWin() end return end",
            f"    if hasKey({KEY_WATCH}) then watch() return end",
            f"    if hasKey({KEY_BETTING}) then bet() return end",
            f"    for difficulty, key in ipairs({keys([KEY_PAGE, KEY_SQUIRE, KEY_KNIGHT, KEY_LORD])}) do   -- :FightCheck",
            "        if hasKey(key) then prepareFight(difficulty); unlockDoors() return end",
            "    end",
            "end",
            "",
            "-- ---- Jarl Sven's double and the assassin (SvenArena.scr, NPC245.scr) ----------------------------------------",
            f"-- With key {KEY_SVEN_PLOT} (Sven's plan) and without {KEY_SVEN_SAVED}: opening the arena door brings Sven's double",
            "-- and his two soldiers into the box (:OnWalk; MM9 walks them there), the crowd cheers (:OnWave), the east pen",
            "-- opens and Byri the Scarred comes out to the middle (NPC245 :OnEnter), and the crowd boos (:Boo).",
            "svenWalk = function()",
            f"    if hasKey({KEY_SVEN_SAVED}) or not hasKey({KEY_SVEN_PLOT}) or var(\"SvenWalked\") == 1 then return end",
            "    -- A dead or removed actor takes none of these messages (MM9.receives): the double's Walk, the soldiers' Guard",
            "    -- (sent by his :OnWalk), Byri's enter (sent by their :OnStart waits, which fire even after a death).",
            f"    if not MM9.receives(\"thearena\", \"SvenArena\", \"Walk\", {actor['SvenArena']}) then return end",
            "    set(\"SvenWalked\", 1)",
            f"    evt.SetMapActorPosition({actor['SvenArena']}, P.Sven0[1], P.Sven0[2], P.Sven0[3])",
            f"    evt.SetMonsterBit({actor['SvenArena']}, MonsterBits.Invisible, false)",
            *[f"    if MM9.receives(\"thearena\", \"{s}\", \"Guard\", {actor[s]}) then "
              f"evt.SetMapActorPosition({actor[s]}, P.Soldier{s[-1]}[1], P.Soldier{s[-1]}[2], P.Soldier{s[-1]}[3]); "
              f"evt.SetMonsterBit({actor[s]}, MonsterBits.Invisible, false) end"
              for s in ("ClanSoldier0", "ClanSoldier1")],
            "    evt.PlaySoundName(\"events/trumpets02.wav\", 0, 0, 0)",
            "    -- :OnArrive wait 2 :OnWave: the cheer and PlayAnim Bless (the soldiers' bodies, MM9's ClanSoldier too, have",
            "    -- no Bless: only the double's plays)",
            "    after(2, function()",
            "        evt.PlaySoundName(\"ambient/people/crowdnoise-cheer01.wav\", 0, 0, 0)",
            f"        if MM9.actorAlive({actor['SvenArena']}) then evt.PlayActorClip({actor['SvenArena']}, \"bless\", false) end",
            "    end)",
            "    local byriEnters = false",
            "    after(4, function()",
            "        door(\"EastPen\", DoorAction.Open)",
            f"        byriEnters = MM9.receives(\"thearena\", \"CommonerHuman2MaleB0\", \"enter\", {actor['CommonerHuman2MaleB0']})",
            f"        if byriEnters then evt.SetMonsterBit({actor['CommonerHuman2MaleB0']}, MonsterBits.Invisible, false) end",
            "    end)",
            f"    after(5, function() if byriEnters then evt.SetMapActorPosition({actor['CommonerHuman2MaleB0']}, P.Marker2[1], "
            "P.Marker2[2], P.Marker2[3]) end end)",
            "    after(6, function() evt.PlaySoundName(\"ambient/people/crowdnoise-cheer01.wav\", 0, 0, 0) end)   -- :Boo",
            "end",
            f"-- Byri (NPC245.scr :OnRude, :Run, :OnVanish): once he gave himself away (key {KEY_SVEN_SAVED}), he opens the arena",
            "-- door and runs off (Marker6, in the hall) and is gone.",
            f"handlers[{rude_exit_event(byri)}] = function()",
            f"    if not hasKey({KEY_SVEN_SAVED}) then return end",
            "    after(2, function()",
            "        lock(\"ArenaDoor\", false); door(\"ArenaDoor\", DoorAction.Open)",
            f"        evt.SetMapActorPosition({actor['CommonerHuman2MaleB0']}, P.Marker6[1], P.Marker6[2], P.Marker6[3])",
            "    end)",
            f"    after(4, function() evt.SetMonGroupBit({GROUP_BYRI}, MonsterBits.Invisible, true) end)",
            "end",
            f"-- Sven's double (SvenArena.scr :OnUse gives key {KEY_DOUBLE} before his talk, RUDE 428; :OnRude takes it).",
            f"handlers[{rude_use_event(sven)}] = function() MM9.giveKey({KEY_DOUBLE}); MM9.openRude(428) end",
            f"handlers[{rude_exit_event(sven)}] = function() MM9.takeKey({KEY_DOUBLE}) end",
            "",
            "-- A bout creature's DeathTrigger sends the Arena Master IDied (ArenaCreature.scr): a dead master takes none",
            "-- (MM9.receives), so no winner, no bet paid, no next pair.",
            f"handlers[{KILL_HOOK}] = function(context)",
            "    fightDead()",
            f"    if var(\"BoutGroupA\") ~= 0 and MM9.receives(\"thearena\", \"ShopkeeperElfMaleB0\", \"IDied\", "
            f"{actor['ShopkeeperElfMaleB0']}) then boutDead() end",
            "end",
            "",
            "-- The poll: PlayerInTheHouse (a touch box, polled as MM9's fire on any part of the party) and the waits.",
            "local inHouse = false",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    tick = tick + 1",
            "    local x, y, z = evt.GetPartyPosition()",
            "    local now = inBox(HOUSE, x, y, z)",
            "    if now and not inHouse and var(\"Waiting\") == 1 then startFight() end",
            "    inHouse = now",
            "    local due = {}",
            "    for i = #tasks, 1, -1 do if tasks[i].at <= tick then table.insert(due, 1, tasks[i].fn) table.remove(tasks, i) end end",
            "    for _, fn in ipairs(due) do fn() end",
            "end",
            "",
            "-- Map load (Arena.scr :Main, :OnPostStartWorld; ArenaFight.scr :Main; SvenArena.scr / NPC245.scr :Init): every",
            "-- visit starts afresh: the day's keys go, three new bouts, Sven's party and Byri hidden, what an earlier visit",
            "-- left standing in the arena is gone, the doors unlocked.",
            "handlers[1] = function()",
            f"    MM9.takeKey({KEY_DONE_TODAY}); reset(); MM9.takeKey({KEY_DOUBLE})",
            "    for g = " + str(GROUP_SPAWN_BASE + 1) + ", " + str(GROUP_SPAWN_BASE) + " + var(\"Serial\") do evt.SetMonGroupBit(g, MonsterBits.Invisible, true) end",
            # Sven's party and Byri one by one: the engine keeps a group bit and applies it after the actors' own
            # bits, so a group-wide hide here would keep hiding them when svenWalk shows each one
            "    for _, i in ipairs({" + ", ".join(str(actor[n]) for n in ("SvenArena", "ClanSoldier0", "ClanSoldier1",
                                                                         "CommonerHuman2MaleB0")) + "}) do "
            "evt.SetMonsterBit(i, MonsterBits.Invisible, true) end",
            "    for _, name in ipairs({\"Waiting\", \"FightGroup\", \"BoutGroupA\", \"BoutGroupB\", \"Bouts\", \"Lord\", \"SvenWalked\", "
            "\"BetAmount\", \"BetOn\"}) do set(name, 0) end",
            "    for _, g in ipairs({\"ArenaDoor\", \"WestPen\", \"EastPen\"}) do lock(g, false) end",
            "    initBout()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "end",
            "",
        ]
        lines.insert(0, "local NAMES = {}")
        script.add(lines, (EV_ARENA_DOOR, "Door", "Door"), (EV_WEST_PEN, "Door", "Door"), (EV_EAST_PEN, "Door", "Door"),
                   (EV_TOKEN_A, "Betting slip", "Betting slip"), (EV_TOKEN_B, "Betting slip", "Betting slip"),
                   (rude_exit_event(master), "Arena Master", None), (rude_exit_event(byri), "Byri the Scarred", None),
                   (rude_use_event(sven), "Sven Forkbeard", None), (rude_exit_event(sven), "Sven Forkbeard", None),
                   (KILL_HOOK, "Arena kills", None), (T_POLL, "Poll", None, "timer"), (1, "Map load", None))
        script.hooks += [f'RegisterMonsterKilledHook({KILL_HOOK}, "Arena kills", handlers[{KILL_HOOK}])']
        return script.finish(on_load=[1])

    def scene(self, build, scene: dict) -> None:
        """The counter's bars as a two-sided cut-out (MetalBarGrey's alpha; the faces are untouchable TRIGGER_nonsolid_
        nodes, which faces.yml does not list: found in the compiled BLV by texture, as Beethoven's webs). The old
        map has no `_authored` sidecars (checked 2026-10-31); any would be removed from the review root here."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        alias = next(entry["alias"] for name, entry in build.source.aliases.items() if name.endswith("metalbargrey.dtx"))
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        bars = sorted(f["index"] for f in blv["faces"] if not f["is_portal"] and f["texture_name"] == alias)
        if bars:
            scene.setdefault("translucent_faces", []).append({"faces": bars, "opacity": 1.0, "tint": [1.0, 1.0, 1.0],
                                                              "two_sided": True})
        build.stats["bar_faces"] = len(bars)
        # No saving here, as in MM6-MM8's arenas (zarena, 7d05, d42): the arena's state lives in its map Lua (the waits
        # of a fight or bout, Sven's staging), which a load would start afresh, losing a won fight's purse (the user,
        # 2026-11-09). Not `arena: true`: that is MM6-MM8's ArenaRuntime, which this map does not use.
        scene["runtime_restrictions"] = {"allow_save_game": False, "allow_lloyds_beacon": False}
        for stem in ("thearena_authored.scene.yml",):
            path = ROOT / "output/mm9_rework/assets_dev/worlds/mm9/maps" / stem
            if path.exists():
                path.unlink()
        lua_path = ROOT / "output/mm9_rework/assets_dev/worlds/mm9/events/maps/thearena_authored.lua"
        if lua_path.exists():
            lua_path.unlink()

    def report(self, build) -> dict:
        return {"sky_faces": getattr(self, "sky_faces", 0),
                "scripted": {"actors": self.actor, "objects": self.objects, "points": self.points,
                             "house_box": self.house_box, "unresolved_arena_classes": getattr(self, "unresolved", [])}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, TheArena()))
