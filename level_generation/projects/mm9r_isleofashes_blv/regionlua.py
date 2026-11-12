"""
Isle of Ashes map Lua: MM9's story scripts on the isle as native handlers, each citing its .scr and lines
(mm9/extracted/SCRIPTS/SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests
and ForadWorld.scr (the location key 1024, the shops' night key 5017), as every region's regionlua.py. Actor
indices, door ids, cogs and points are resolved here from the built scene and the DAT and written as named Lua locals.

- Yrsa (YRSA.scr, RUDE 1) and Forad Darre (FORAD.scr, RUDE 2): their click (53000 + DAT index) runs the script's
  OnUse (Forad's also his DAT GreetingSound, which MM9's NPC use plays) and opens the dialogue; the dialogue's
  exit (50000 + index) its OnRudeExit routine. Neither talks by approach in MM9. Forad's hire row (RUDE 2)
  gives key 29 and the hireling; his exit then removes him. Annud Redeye (HideModel.scr "28 unhide", RUDE 138) is
  shown with key 28; his click plays his GreetingSound and opens his dialogue (no script of his own runs on it).
- KillControl (TM_Hardrock.scr "8 27 200"): the twelve flyers whose DeathTriggerTarget it is count their deaths; the
  eighth gives key 27 and 200 experience.
- The DAT triggers the party walks into: Trigger1 and Trigger2 raise the Bone Thrashers (AutoResurrect.scr),
  TriggerStarters makes the Lich summon (Isle_Summoner.scr, Isle_SpawnCreature.scr: at most six Skeletoids, each
  runs to MarkerFrom and teleports to MarkerTo; each death asks for the next; the Lich's death ends it).
- The bunker (DoorLock.scr "568 1": the Turret Key opens both leaves and is taken) and Yrsa's hut door (a click
  toggles it).
- The book and its lectern (IsleAshesBook.scr, PropTrigger.scr "Book Use"): the cinematic book_sinking
  (isleofashes.cinematics.yml, ../mm9r_isleofashes/story.py `Story.cinematics`) runs the script's gameplay steps as
  map events: the bunker's FortWall breaks, the Shooters fire, FortWall0 breaks (TriggerEffects: the islet's five
  explosions and the Lich's end), the islet sinks (Terrain3), the boat leaves (IS_Boat.scr), key 28 and 5200
  experience, then ExitTrigger1 (Sturmford).
- The shipwreck movie (game.cpp, cshell.dll 0x100a6e40): the first arrival before the cinema plays MM9Shipwreck
  (movies\\Shipwreck.bik) and gives key 481.

Map vars keep the names the generic runtime used (Isle.SummonCount, Isle.TriggerCount.<trigger>, Isle.CinemaStep.<step>
...), so saves carry over.
"""

from __future__ import annotations

import math
import re
import struct

import review_root
from dungeon import voices          # ../mm9r_common/dungeon/voices.py: MM9 sound names
import story as isle_story          # ../mm9r_isleofashes/story.py: the cinematic and its events
from quest_xp import balanced_experience

MAP = "isleofashes"
SCALE = 2.56                        # MM9 units -> engine units
EV_TICK = 31000                     # the story's 0.25 s timer (make_story_scenario.py runs it as ticks)
EV_LEAVE = 31002
EV_KILLED = 31003
TICK_SECONDS = 0.25
OBJECT_EVENT_BASE = isle_story.OBJECT_EVENT_BASE    # a DAT object's Use event: 30000 + its index
RUDE_EXIT, RUDE_USE = 50000, 53000                  # game/mm9/Mm9RudeDialogue.h
PLAYER_TRIGGERS = ("Trigger1", "Trigger2", "TriggerStarters")
TRIGGER_Z_SLACK = 192               # a trigger box reaches this far above and below its DAT height (the party's feet)
AIBASE_RADIUS_LT = 500              # IsleAshesBook.scr:86 GetObjects AIBase, 500
SHOOTER_RANGE = 4000                # where the bunker's Shooter aims: this far along its DAT facing
SKELETOID_RUN_SECONDS = 20          # a run the path planner cannot finish teleports anyway


def obj(build, name: str) -> dict:
    found = build.source.by_name.get(name.lower())
    if found is None:
        raise SystemExit(f"{MAP}: no DAT object {name}")
    return found


def number(value) -> float:
    """MM9 stores some counts and ids as raw float bits (ActivationCount 1065353216 is 1.0, NPCNbr 1073741824 2.0)."""
    if isinstance(value, int) and value > 65535:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


def native(build, name: str) -> list[int]:
    """A DAT object's position in this map's frame (not dropped to the floor)."""
    return [int(round(v)) for v in build.project.native(obj(build, name)["properties"]["Pos"])]


def on_floor(build, name: str) -> list[int]:
    """A DAT object's position dropped onto the rebuilt floor under it: where a scripted teleport puts an actor, which
    the game places only on a floor within 16 units (IndoorWorldRuntime::placeMapActorAt). MarkerTo hangs 23 units over
    the rebuilt shore, so the Lich's Skeletoids never left his islet (found 2026-11-09)."""
    pos = obj(build, name)["properties"]["Pos"]
    floor = build.content.floor_at(pos[0], pos[2], pos[1] + 400)
    if floor is None:
        raise SystemExit(f"{MAP}: no floor under {name}")
    return [int(round(v)) for v in build.project.native([pos[0], floor, pos[2]])]


def lua_point(p) -> str:
    return "{" + ", ".join(str(int(round(v))) for v in p) + "}"


def const(name: str) -> str:
    """A DAT name as a Lua constant: BoneThrasher0 -> BONE_THRASHER0, ExplosionEffect3 -> EXPLOSION_EFFECT3."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).upper()


def messages(build, name: str) -> list[tuple[str, str]]:
    """A Trigger object's messages in order (TargetName1..10, MessageName1..10)."""
    p = obj(build, name)["properties"]
    return [(str(p[f"TargetName{k}"]), str(p[f"MessageName{k}"])) for k in range(1, 11)
            if p.get(f"TargetName{k}") and p.get(f"MessageName{k}")]


def prop_events(build) -> tuple[dict, dict]:
    """The book and its lectern run the book's Use on a click; the boat answers SetSprite by its DAT index."""
    events = {name: OBJECT_EVENT_BASE + obj(build, name)["index"] for name in ("Book", "Prop159")}
    cogs = {name: obj(build, name)["index"] for name in ("Book", "Boat")}
    return events, cogs


def exit_row(build, name: str) -> dict:
    """The exit's row of the review root's map_transitions.txt (its source object and this map)."""
    path = review_root.mirror_path("worlds/mm9/data_tables/map_transitions.txt")
    rows = path.read_text(encoding="latin-1").splitlines()
    header = rows[0].split("\t")
    index = obj(build, name)["index"]
    for line in rows[1:]:
        row = dict(zip(header, line.split("\t")))
        if row.get("SourceMapFile", "").lower() == build.project.map and int(row["SourceObjectIndex"]) == index:
            return row
    raise SystemExit(f"{MAP}: {name} ({index}) has no row in {path}")


def extend(hooks, build, script) -> None:
    actors = {a["anchor"]: a["actor_index"] for a in build.content.report["actors"]}

    def actor(name: str) -> int:
        if name not in actors:
            raise SystemExit(f"{MAP}: the story actor {name} is not placed")
        return actors[name]

    def index(name: str) -> int:
        return obj(build, name)["index"]

    def door(group: str, model: str | None = None) -> int:
        """A door id: the mover of the DAT model (a leaf of the bunker pair), else the group's first."""
        movers = [m for m in build.movers if m["group"] == group]
        for m in movers:
            if model is None or model in m.get("dat_models", []):
                return m["door_id"]
        raise SystemExit(f"{MAP}: no door {model or group}")

    story_actors = sorted(actor(o["name"]) for o in build.source.objects if o["index"] in hooks.exclude_sources)
    yrsa, forad, annud, lich = (actor(n) for n in ("Yrsa", "ForadDarre", "ShopkeeperHuman2MaleA0", "LichSummoner"))
    rude = {name: int(number(obj(build, name)["properties"]["NPCNbr"])) for name in ("Yrsa", "ForadDarre")}

    # TM_Hardrock.scr's object and its parameters, and the actors whose death sends it OneDown
    kill = obj(build, "KillControl")
    pieces, kill_key, kill_xp = (int(w) for w in str(kill["properties"]["ScriptParams"]).split())
    senders = [o["name"] for o in build.source.objects
               if str(o["properties"].get("DeathTriggerTarget") or "") == "KillControl"
               and str(o["properties"].get("DeathTriggerMessage") or "").lower() == "onedown"]
    sender_actors = sorted(actor(name) for name in senders)

    # The Lich's ScriptParams: the creature (its placed row) and the spawn point
    creature, location = str(obj(build, "LichSummoner")["properties"]["ScriptParams"]).split()
    skeletoid_row = next((a["monster_id"] for a in build.content.report["actors"] if a["class"] == creature), None)
    if skeletoid_row is None:
        raise SystemExit(f"{MAP}: no placed {creature} gives the summons' monster row")

    # Bone Thrashers by the trigger that raises them (AutoResurrect.scr)
    risers = {name: [target for target, message in messages(build, name) if message.lower() == "resurrect"]
              for name in PLAYER_TRIGGERS}

    shooter = obj(build, "Shooter")["properties"]
    pitch, yaw = (shooter.get("Rotation") or [0, 0])[:2]
    aim = [a + d * SHOOTER_RANGE for a, d in zip(native(build, "Shooter"),
                                                 (math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch),
                                                  -math.sin(pitch)))]
    boat, marker = native(build, "Boat"), native(build, "BoatMarker")
    glide = (marker[0] - boat[0], marker[1] - boat[1])
    glide_seconds = math.hypot(*glide) / (100 * SCALE)
    leave = exit_row(build, "ExitTrigger1")
    cinema = isle_story.CINEMA_EVENTS

    def bone_thrashers() -> list[str]:
        names = [n for name in PLAYER_TRIGGERS for n in risers[name]]
        return [f"local {const(n)} = {actor(n)}" for n in names]

    def trigger_calls(name: str) -> list[str]:
        """A Trigger's messages as calls, in its order (an 'off' to itself: it fires once, its ActivationCount)."""
        calls = []
        for target, message in messages(build, name):
            m = message.lower()
            if m == "resurrect":
                calls.append(f"    resurrect(\"{target}\", {const(target)})")
            elif m == "off" and target == name:
                calls.append(f"    -- {target} off: it fires once")
            elif m == "spawn" and target == "LichSummoner":
                calls.append("    lichSpawn()")
            elif m == "explode" and target.startswith("ExplosionEffect"):
                calls.append(f"    explode({const(target)})   -- {target} (Isle_IslandExplosion.scr)")
            elif m == "destroy" and target == "LichSummoner":
                calls.append("    lichDestroyed()")
            else:
                raise SystemExit(f"{MAP}: {name} sends {target} '{message}', which regionlua.py does not port")
        return calls

    lines = [
        "-- Isle of Ashes (regionlua.py): MM9's story scripts as native handlers, each citing its .scr and lines.",
        f"local MAP = \"{MAP}\"",
        f"local TICK_SECONDS = {TICK_SECONDS}               -- the story tick (event {EV_TICK}, a game-time timer)",
        f"local EFFECT_SCALE = {SCALE}               -- MM9 effects at the world scale",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function ticks() return var(\"Isle.Ticks\") end",
        "",
        "-- The story's actors (convert.py places them first, from the old import's records), doors, cogs and points.",
        f"local YRSA = {yrsa}                  -- Yrsa the Troll (YRSA.scr, RUDE {rude['Yrsa']})",
        f"local FORAD = {forad}                 -- Forad Darre (FORAD.scr, RUDE {rude['ForadDarre']})",
        f"local ANNUD = {annud}                 -- Annud Redeye, ShopkeeperHuman2MaleA0 (HideModel.scr \"28 unhide\", RUDE 138)",
        f"local LICH = {lich}                  -- LichSummoner (Isle_Summoner.scr \"{creature} {location}\")",
        *bone_thrashers(),
        f"local STORY_ACTORS = {{{', '.join(map(str, story_actors))}}}",
        f"local BUNKER_DOOR1, BUNKER_DOOR2 = {door('BunkerDoor', 'BunkerDoor1')}, {door('BunkerDoor', 'BunkerDoor2')}",
        f"local HUT_DOOR = {door('RotatingDoor8')}                -- RotatingDoor8, Yrsa's hut",
        f"local ISLET = {door('Terrain3')}                   -- Terrain3, the islet the cinema sinks (MM9's Door, 1000 LT down)",
        f"local FORT_WALL, FORT_WALL0 = {index('FortWall')}, {index('FortWall0')}   -- cogs of their faces (DAT index)",
        f"local BOAT = {index('Boat')}                   -- the boat's decoration (SetSprite key: DAT index)",
        f"local BOOK = {lua_point(native(build, 'Book'))}",
        f"local SPAWN_LOCATION = {lua_point(native(build, location))}",
        f"local MARKER_FROM = {lua_point(native(build, 'MarkerFrom'))}",
        f"local MARKER_TO = {lua_point(on_floor(build, 'MarkerTo'))}   -- on the rebuilt shore (on_floor)",
        *[f"local {const(f'ExplosionEffect{k}')} = {lua_point(native(build, f'ExplosionEffect{k}'))}" for k in range(5)],
        f"local SHOOTER, SHOOTER_AIM = {lua_point(native(build, 'Shooter'))}, {lua_point(aim)}",
        f"local SHOOTER0, FORT_WALL0_AT = {lua_point(native(build, 'Shooter0'))}, {lua_point(native(build, 'FortWall0'))}",
        "",
        "-- MM9's 'Wait <slot> <seconds> <routine>': a step after so many story ticks (not saved; the explosions only).",
        "local pending = {}",
        "local function after(secondsLater, step)",
        "    table.insert(pending, {at = ticks() + math.max(1, math.floor(secondsLater / TICK_SECONDS + 0.5)), step = step})",
        "end",
        "",
        f"-- TM_HARDROCK.scr:29-54 (KillControl, ScriptParams \"{pieces} {kill_key} {kill_xp}\"): each OneDown counts; at "
        f"the {pieces}th key {kill_key},",
        f"-- the quest sound and {kill_xp} experience. The senders: the flyers whose DeathTriggerTarget is KillControl.",
        f"local KILL_CONTROL = {kill['index']}",
        "local KILL_CONTROL_SENDERS = {" + ", ".join(f"[{a}] = true" for a in sender_actors) + "}",
        "local function killControlOneDown()",
        "    local count = MM9.scrValue(KILL_CONTROL, \"count\", 0) + 1",
        "    MM9.setScrValue(KILL_CONTROL, \"count\", count)",
        f"    if count == {pieces} then reward({kill_key}, {balanced_experience(kill_xp, kill_key)}, 0) end",
        "end",
        "",
        "-- AUTORESURRECT.scr:66-87 Main: the Bone Thrashers wait hidden under the ground (map load, below); :34-46",
        "-- OnResurrect: one rises (shown) on RESURRECT. A dead or removed one takes no message (MM9.receives).",
        "local function resurrect(name, a)",
        "    if MM9.receives(MAP, name, \"RESURRECT\", a) then show(a, true) end",
        "end",
        "",
        "-- ISLE_SUMMONER.scr:47-69 (LichSummoner): each 'spawn' summons a Skeletoid at SpawnLocation with",
        "-- Isle_SpawnCreature.scr; after the fifth the trigger is removed (the sixth still spawns: it counts before).",
        "-- Isle.Skeletoid.<n> holds the n-th summon's actor index + 1, Isle.SkeletoidState.<n> 1 while it runs to",
        "-- MarkerFrom, 2 once it fights, 3 dead. A dead Lich takes no 'spawn' (MM9.receives), and once he is gone",
        "-- (his death, the islet's fall: Isle.LichGone) nothing more comes.",
        f"local SKELETOID_ROW = {skeletoid_row}            -- the {creature}s placed on the isle",
        f"local SKELETOID_RUN_SECONDS = {SKELETOID_RUN_SECONDS}",
        "local function lichSpawn()",
        "    if not MM9.receives(MAP, \"LichSummoner\", \"spawn\", LICH) or var(\"Isle.LichGone\") == 1 then return end",
        "    local counter = var(\"Isle.SummonCount\")",
        "    if counter > 5 then return end",
        "    set(\"Isle.SummonCount\", counter + 1)",
        "    evt.PlayActorClip(LICH, \"attack_melee\", false)   -- PlayAnim hattack1 (the Lich King's AttackMelee)",
        "    local _, spawned = evt.SummonMonstersById({monster = SKELETOID_ROW, x = SPAWN_LOCATION[1],",
        "        y = SPAWN_LOCATION[2], z = SPAWN_LOCATION[3], radius = 128, count = 1})",
        "    local a = spawned ~= nil and spawned[1] or nil",
        "    if a == nil then return end",
        "    local slot = counter + 1",
        "    set(\"Isle.Skeletoid.\" .. slot, a + 1)",
        "    set(\"Isle.SkeletoidState.\" .. slot, 1)",
        "    set(\"Isle.SkeletoidSince.\" .. slot, ticks())",
        "    -- Isle_SpawnCreature.scr:30-47 InitSpawnCreature: elemental blast and column of fire on it, RunTo MarkerFrom",
        "    local x, y, z = evt.GetMapActorPosition(a)",
        "    if x == nil then x, y, z = SPAWN_LOCATION[1], SPAWN_LOCATION[2], SPAWN_LOCATION[3] end",
        "    evt.SpawnWorldEffect(\"mm9:elemental_blast\", x, y, z, EFFECT_SCALE)",
        "    evt.SpawnWorldEffect(\"mm9:column_of_fire\", x, y, z, EFFECT_SCALE)",
        "    evt.MoveActorTo(a, MARKER_FROM[1], MARKER_FROM[2], MARKER_FROM[3], 0, true)",
        "end",
        "-- Isle_SpawnCreature.scr:60-75 Teleport: at MarkerTo (the mainland's shore) with a column of fire, then BaseInit",
        "-- and BaseWanderStartup (the shared AI). Each tick a running Skeletoid that has arrived (or whose run a reload",
        "-- lost, or that takes too long) teleports; it counts as fighting only once the game has moved it. Saves from",
        "-- before 2026-11-09 hold Skeletoids marked fighting that never left MarkerFrom (MarkerTo over the floor): they",
        "-- teleport too.",
        "local function strandedAtMarkerFrom(a)",
        "    local x, y = evt.GetMapActorPosition(a)",
        "    return x ~= nil and math.abs(x - MARKER_FROM[1]) < 300 and math.abs(y - MARKER_FROM[2]) < 300",
        "end",
        "local function updateSkeletoids()",
        "    for slot = 1, var(\"Isle.SummonCount\") do",
        "        local a = var(\"Isle.Skeletoid.\" .. slot) - 1",
        "        local state = var(\"Isle.SkeletoidState.\" .. slot)",
        "        local elapsed = (ticks() - var(\"Isle.SkeletoidSince.\" .. slot)) * TICK_SECONDS",
        "        if a >= 0 and ((state == 1 and (not evt.IsActorMoving(a) or elapsed >= SKELETOID_RUN_SECONDS))",
        "                or (state == 2 and strandedAtMarkerFrom(a))) then",
        "            evt.StopActorMove(a)",
        "            if evt.SetMapActorPosition(a, MARKER_TO[1], MARKER_TO[2], MARKER_TO[3]) then",
        "                evt.SpawnWorldEffect(\"mm9:column_of_fire\", MARKER_TO[1], MARKER_TO[2], MARKER_TO[3], EFFECT_SCALE)",
        "                set(\"Isle.SkeletoidState.\" .. slot, 2)",
        "            end",
        "        end",
        "    end",
        "end",
        "-- Isle_SpawnCreature.scr:49-58 OnDeath: a dead Skeletoid tells LichSummoner to spawn the next.",
        "local function skeletoidKilled(a)",
        "    for slot = 1, var(\"Isle.SummonCount\") do",
        "        if var(\"Isle.Skeletoid.\" .. slot) == a + 1 and var(\"Isle.SkeletoidState.\" .. slot) ~= 3 then",
        "            set(\"Isle.SkeletoidState.\" .. slot, 3)",
        "            lichSpawn()",
        "            return",
        "        end",
        "    end",
        "end",
        "-- TriggerEffects' last message: the Lich is destroyed with the islet.",
        "local function lichDestroyed()",
        "    if not MM9.receives(MAP, \"LichSummoner\", \"destroy\", LICH) then return end",
        "    set(\"Isle.LichGone\", 1)",
        "    show(LICH, false)",
        "end",
        "",
        "-- ISLE_ISLANDEXPLOSION.scr:28-52 CreateExplosion: five bursts of elemental blast and black smoke 1-2 s apart,",
        "-- then mist (CreateSteam).",
        "local function explode(p, burst)",
        "    burst = burst or 0",
        "    if burst < 5 then",
        "        evt.SpawnWorldEffect(\"mm9:elemental_blast\", p[1], p[2], p[3], EFFECT_SCALE)",
        "        evt.SpawnWorldEffect(\"mm9:blacksmoke\", p[1], p[2], p[3], EFFECT_SCALE)",
        "        after(evt.RandomBetween(4, 8) * TICK_SECONDS, function() explode(p, burst + 1) end)",
        "    else",
        "        evt.SpawnWorldEffect(\"mm9:mist\", p[1], p[2], p[3], EFFECT_SCALE)",
        "    end",
        "end",
        f"-- TriggerEffects (DAT {index('TriggerEffects')}, FortWall0's DeathTriggerTarget): its messages in order.",
        "local function triggerEffects()",
        *trigger_calls("TriggerEffects"),
        "end",
        "",
        "-- DestructableBrush 'destroy' (TriggerDestroyOnly): the brush's faces go. FortWall0's death triggers",
        "-- TriggerEffects, once (ShouldMiniSave: Isle.FortWall0Destroyed).",
        "local function removeFaces(cog)",
        "    evt.SetFacetBit(cog, FacetBits.Invisible, 1)",
        "    evt.SetFacetBit(cog, FacetBits.Untouchable, 1)",
        "end",
        "local function fortWallDestroy() removeFaces(FORT_WALL) end",
        "local function fortWall0Destroy()",
        "    if var(\"Isle.FortWall0Destroyed\") == 1 then return end",
        "    set(\"Isle.FortWall0Destroyed\", 1)",
        "    removeFaces(FORT_WALL0)",
        "    triggerEffects()",
        "end",
        "",
        "-- Shooter objects (ShootInterval 0: one FireBolt per 'on'): Shooter fires out of the bunker through the broken",
        "-- FortWall along its own aim (5 damage), Shooter0 at the islet's FortWall0 (500).",
        "local function shooterOn()",
        "    evt.FireMissile(\"Fire\", SHOOTER[1], SHOOTER[2], SHOOTER[3], SHOOTER_AIM[1], SHOOTER_AIM[2], SHOOTER_AIM[3], 5,",
        "        \"Fire\", 0)",
        "    MM9.launchSound(\"FireBolt\", SHOOTER[1], SHOOTER[2], SHOOTER[3])",
        "end",
        "local function shooter0On()",
        "    evt.FireMissile(\"Fire\", SHOOTER0[1], SHOOTER0[2], SHOOTER0[3], FORT_WALL0_AT[1], FORT_WALL0_AT[2],",
        "        FORT_WALL0_AT[3], 500, \"Fire\", 0)",
        "    MM9.launchSound(\"FireBolt\", SHOOTER0[1], SHOOTER0[2], SHOOTER0[3])",
        "end",
        "",
        "-- IS_BOAT.scr:33-44 OnMove: the boat shows and sails to BoatMarker's x at 100 (MoveToPos x, its own height,",
        "-- BoatMarker's z): a glide of its decoration.",
        "local function boatMove()",
        "    evt.SetSprite(BOAT, 1)",
        f"    evt.MoveDecoration(BOAT, {glide[0]}, {glide[1]}, 0, {glide_seconds:.4f})",
        "end",
        "",
        "-- IA_ISLAND.scr / Door Terrain3 'open': the islet sinks 1000 LT (its mover: overrides.yml motion dat, 20 s).",
        "local function isletOpen() evt.SetDoorState(ISLET, DoorAction.Open) end",
        "",
        f"-- ExitTrigger1 'trigger' (DAT {index('ExitTrigger1')}): it lies 43 000 west at sea, outside this map, so its row of",
        "-- map_transitions.txt runs without the volume: the travel days pass, then the arrival.",
        "local function exitTrigger1()",
        *([f"    evt.AdvanceGameMinutes({int(leave['TravelDays'])} * 24 * 60)"] if int(leave["TravelDays"]) > 0 else []),
        f"    evt.MoveToMap({int(leave['ArrivalX'])}, {int(leave['ArrivalY'])}, {int(leave['ArrivalZ'])}, "
        f"{int(leave['FacingYawUnits'])}, 0, 0, 0, 0, \"{leave['DestinationMapFile']}\")",
        "end",
        "",
        "-- ISLEASHESBOOK.scr: the cinema. The cinematic book_sinking shows it and runs these steps as its map events at",
        "-- the script's waits; a skip runs the ones still to come at once. Each step runs once (Isle.CinemaStep.<step>),",
        "-- and the done event runs any that has not (a cinematic that could not play), in order.",
        "-- :OnUse 44-50 Gosub DestroyMonsters (81-103): the AIBase within 500 of the book are removed (the story actors;",
        "-- hidden here).",
        "local function destroyMonsters()",
        f"    local radius = {AIBASE_RADIUS_LT * SCALE:g}",
        "    for _, a in ipairs(STORY_ACTORS) do",
        "        local x, y, z = evt.GetMapActorPosition(a)",
        "        if x ~= nil and (x - BOOK[1]) ^ 2 + (y - BOOK[2]) ^ 2 + (z - BOOK[3]) ^ 2 <= radius ^ 2 then",
        "            show(a, false)",
        "        end",
        "    end",
        "end",
        "-- :OnSink 160-186: FortWall0 destroy (its death triggers TriggerEffects), Terrain3 open, Boat move, key 28, 5200",
        "-- experience and the quest sound (eblast03, drown01 and the fire loop are the cinematic's).",
        "local function sink()",
        "    fortWall0Destroy()",
        "    isletOpen()",
        "    boatMove()",
        f"    reward(28, {balanced_experience(5200, 28)}, 0)",
        "end",
        "local CINEMA_STEPS = {",
        "    {\"monsters\", destroyMonsters},       -- :OnUse 44-50",
        "    {\"fortWall\", fortWallDestroy},       -- :StartDestroy 106-115 (SpawnMgr off: the isle has none)",
        "    {\"shooter\", shooterOn},              -- :Shoot 119-125",
        "    {\"shooter0\", shooter0On},            -- :Shoot2 139-146 (ebolt01 is the cinematic's)",
        "    {\"sink\", sink},                      -- :OnSink 160-186",
        "    {\"exit\", exitTrigger1},              -- :FadeOut2 218-226 (letterbox and camera3 off: the cinematic's)",
        "}",
        "local function cinemaStep(step)",
        "    local done = \"Isle.CinemaStep.\" .. step[1]",
        "    if var(done) == 0 then",
        "        set(done, 1)",
        "        step[2]()",
        "    end",
        "end",
    ]
    names = [step for step in cinema]
    if names != ["monsters", "fortWall", "shooter", "shooter0", "sink", "exit"]:
        raise SystemExit(f"{MAP}: story.py CINEMA_EVENTS {names} differ from regionlua.py's CINEMA_STEPS")
    registrations = []
    for k, step in enumerate(names):
        lines.append(f"handlers[{cinema[step]}] = function() cinemaStep(CINEMA_STEPS[{k + 1}]) end   -- {step}")
        registrations.append((cinema[step], f"Isle cinema: {step}", None))
    done = isle_story.CINEMA_DONE_EVENT
    lines += [
        f"handlers[{done}] = function()   -- the cinematic ended (played or skipped)",
        "    for _, step in ipairs(CINEMA_STEPS) do cinemaStep(step) end",
        "end",
        "-- ISLEASHESBOOK.scr:29-54 OnUse: ContainerCheck (58-77: the party stands on the bunker's AI rails; any party at",
        "-- the book does here), then the cinema once Forad has joined (key 29) and before it ran (key 28). A cinematic is",
        "-- never saved half played, so the steps' map vars only guard against a second use while it plays.",
        "local function bookUse()",
        "    if has(29) and not has(28) and var(\"Isle.CinemaStep.monsters\") == 0 then",
        f"        evt.PlayCinematic(\"{isle_story.CINEMA_ID}\", {done})",
        "    end",
        "end",
        f"handlers[{OBJECT_EVENT_BASE + index('Book')}] = bookUse   -- Book",
        "-- PROPTRIGGER.scr:24-36 (Prop159, \"Book Use\"): using the lectern uses the book.",
        f"handlers[{OBJECT_EVENT_BASE + index('Prop159')}] = bookUse   -- Prop159",
        "",
    ]
    registrations += [(done, "Isle cinema: done", None), (OBJECT_EVENT_BASE + index("Book"), "Book", "Read"),
                      (OBJECT_EVENT_BASE + index("Prop159"), "Lectern", "Read")]

    # --- the doors -------------------------------------------------------------------------------------------------
    bunker_event, hut_event = (hooks.mover_events[group][0] for group in ("BunkerDoor", "RotatingDoor8"))
    lock = str(obj(build, "BunkerDoor1")["properties"]["ScriptParams"]).split()
    key_item, take_key = int(lock[0]), len(lock) > 1 and lock[1] == "1"
    if not take_key:
        raise SystemExit(f"{MAP}: BunkerDoor1's DoorLock.scr no longer takes its key ({lock})")
    lines += [
        f"-- DOORLOCK.scr:22-48 (BunkerDoor1/2, ScriptParams \"{' '.join(lock)}\"): with the Turret Key (item {key_item}) "
        "the doors",
        "-- unlock and the key is taken; they are Sticky (they stay open) and DoubleDoorName opens the pair together.",
        "-- Without the key they stay Locked.",
        f"handlers[{bunker_event}] = function()",
        "    if var(\"Isle.BunkerOpen\") == 1 then return end",
        f"    if MM9.hasItem({key_item}, \"DOORLOCK.scr:25\") ~= 1 then",
        "        evt.StatusText(\"Locked\")",
        "        return",
        "    end",
        f"    MM9.takeItem({key_item}, \"DOORLOCK.scr:34\")",
        "    set(\"Isle.BunkerOpen\", 1)",
        "    evt.SetDoorState(BUNKER_DOOR1, DoorAction.Open)",
        "    evt.SetDoorState(BUNKER_DOOR2, DoorAction.Open)",
        "end",
        "-- RotatingDoor8 (Yrsa's hut door, no script, not locked): a click opens or closes it (MM9 closes it again after",
        "-- CloseWaitTime 5 s; here it stays as the party leaves it).",
        f"handlers[{hut_event}] = function() evt.SetDoorState(HUT_DOOR, DoorAction.Trigger) end",
        "",
    ]
    registrations += [(bunker_event, "BunkerDoor1", "Open"), (hut_event, "RotatingDoor8", "Open")]
    script.hooks += [
        f"SetMapContextAction({bunker_event}, {{kind = \"open_door\", source = \"mm9_mechanism\", "
        "targetName = \"BunkerDoor1\"})",
        f"SetMapContextAction({hut_event}, {{kind = \"open_door\", source = \"mm9_mechanism\", "
        "targetName = \"RotatingDoor8\"})",
    ]

    # --- Yrsa and Forad: their scripts' OnUse (their click, before the dialogue) and OnRude (the dialogue's exit) --
    y, f, a = index("Yrsa"), index("ForadDarre"), index("ShopkeeperHuman2MaleA0")
    annud_rude = next(int(actor_record["mm9_rude_id"]) for actor_record in hooks.story.actors
                      if actor_record["actor_index"] == annud)

    def greeting(name: str) -> str:
        """The DAT's GreetingSound as the world's audio name (MM9_AMBIENT_ANIMATION.md 2.4: NPC use plays it)."""
        sound = voices._sound_name(str(obj(build, name)["properties"].get("GreetingSound") or ""))
        if sound is None:
            raise SystemExit(f"{MAP}: {name} has no installed GreetingSound")
        return sound

    lines += [
        "-- YRSA.scr:74-102 OnUse: key 480; the first time key 365, 800 experience and the quest sound; her voice; then",
        f"-- her dialogue (DoRude 1, NPCNbr {rude['Yrsa']}).",
        f"handlers[{RUDE_USE + y}] = function()",
        "    MM9.giveKey(480)",
        f"    if not has(365) then reward(365, {balanced_experience(800, 365)}, 0) end",
        "    MM9.playSound(\"voices\\\\NPC\\\\NPC_001.wav\")",
        f"    MM9.openRude({rude['Yrsa']})",
        "end",
        "-- YRSA.scr:14-70 OnRude: :Key (the Turret Key, item 568, once key 469 is held and the party has none),",
        "-- :dragonfly (key 27: 2000 experience and key 366, once), :Mainline (key 1: 2000 experience and key 367, once).",
        f"handlers[{RUDE_EXIT + y}] = function()",
        "    if MM9.hasItem(568, \"YRSA.scr:26\") ~= 1 and has(469) then MM9.giveItem(568, \"YRSA.scr:33\") end",
        f"    if not has(366) and has(27) then reward(366, {balanced_experience(2000, 366)}, 0) end",
        f"    if not has(367) and has(1) then reward(367, {balanced_experience(2000, 367)}, 0) end",
        "end",
        "-- FORAD.scr:22-41 OnUse: the first time (no key 480) key 480, 800 experience and the quest sound; then his",
        f"-- greeting (the DAT's GreetingSound, which MM9's NPC use plays: the script's own Playsound is commented out)",
        f"-- and his dialogue (DoRude 2, NPCNbr {rude['ForadDarre']}). MM9 has no approach talk here: FORAD.scr's",
        "-- OnFoundPlayer / OnTargetWithinDist 16 Talk is armed only by an Appear message, which only Frosgard City's",
        "-- BattleMan.scr sends.",
        f"handlers[{RUDE_USE + f}] = function()",
        f"    if not has(480) then reward(480, {balanced_experience(800, 480)}, 0) end",
        f"    MM9.playSound(\"{greeting('ForadDarre')}\")",
        f"    MM9.openRude({rude['ForadDarre']})",
        "end",
        "-- Annud Redeye (HideModel.scr has no OnUse): MM9's NPC use plays his GreetingSound, then his dialogue.",
        f"handlers[{RUDE_USE + a}] = function()",
        f"    MM9.playSound(\"{greeting('ShopkeeperHuman2MaleA0')}\")",
        f"    MM9.openRude({annud_rude})",
        "end",
        "-- FORAD.scr:45-86 OnRude: with key 104 (a later chapter's betrayal) he turns hostile instead (OnFoundPlayer off;",
        "-- BaseInit, his fight, is not ported); else :Forad: key 368 and 4000 experience once, and once his hire row",
        "-- gave key 29 he is gone with the party (RemoveObject).",
        f"handlers[{RUDE_EXIT + f}] = function()",
        f"    if has(104) then MM9.disableFoundPlayer({f}) return end",
        f"    if not has(368) then reward(368, {balanced_experience(4000, 368)}, 0) end",
        "    if has(29) then MM9.removeActor(FORAD) end",
        "end",
        "",
    ]
    registrations += [(RUDE_USE + y, "Yrsa", None), (RUDE_EXIT + y, "Yrsa: dialogue exit", None),
                      (RUDE_USE + f, "Forad Darre", None), (RUDE_EXIT + f, "Forad Darre: dialogue exit", None),
                      (RUDE_USE + a, "Annud Redeye", None)]

    # --- the triggers the party walks into ----------------------------------------------------------------------
    rows = []
    for name in PLAYER_TRIGGERS:
        p = obj(build, name)["properties"]
        if not float(p.get("PlayerTriggerable", 0) or 0):
            raise SystemExit(f"{MAP}: {name} is not PlayerTriggerable")
        centre = native(build, name)
        dims = p.get("Dims") or [0, 0, 0]
        half = (dims[0] * SCALE, dims[2] * SCALE, dims[1] * SCALE + TRIGGER_Z_SLACK)
        activations = int(number(p.get("ActivationCount", 0)))
        if activations != 1:
            raise SystemExit(f"{MAP}: {name} fires {activations} times; the poll below fires each once")
        fn = name[0].lower() + name[1:]
        lines += [f"-- {name} (DAT {index(name)}): " + ", ".join(f"{t} {m}" for t, m in messages(build, name)) + ".",
                  f"local function {fn}()", *trigger_calls(name), "end"]
        low = [c - h for c, h in zip(centre, half)]
        high = [c + h for c, h in zip(centre, half)]
        rows.append(f"    {{name = \"{name}\", fire = {fn}, box = {{{lua_point(low)}, {lua_point(high)}}}}},")
    lines += [
        "-- DAT Trigger objects the party walks into (PlayerTriggerable; Dims are half extents, reaching "
        f"{TRIGGER_Z_SLACK} over and under), each",
        "-- once (ActivationCount 1: Isle.TriggerCount.<name>).",
        "local PLAYER_TRIGGERS = {", *rows, "}",
        "local function playerTriggers()",
        "    local x, y, z = evt.GetPartyPosition()",
        "    for _, t in ipairs(PLAYER_TRIGGERS) do",
        "        local count, b = \"Isle.TriggerCount.\" .. t.name, t.box",
        "        if var(count) == 0 and x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]",
        "                and z >= b[1][3] and z <= b[2][3] then",
        "            set(count, 1)",
        "            t.fire()",
        "        end",
        "    end",
        "end",
        "",
        f"handlers[{EV_TICK}] = function()   -- the story tick: delayed steps, the triggers, the running Skeletoids",
        "    set(\"Isle.Ticks\", ticks() + 1)",
        "    local now, due = ticks(), {}",
        "    for k = #pending, 1, -1 do",
        "        if pending[k].at <= now then",
        "            table.insert(due, 1, pending[k].step)",
        "            table.remove(pending, k)",
        "        end",
        "    end",
        "    for _, step in ipairs(due) do step() end",
        "    playerTriggers()",
        "    updateSkeletoids()",
        "end",
        "",
        "-- Deaths: KillControl's flyers send OneDown (their DeathTriggerTarget); Isle_Summoner.scr OnDeath ends the",
        "-- summons (\"give player an incentive to kill the summoner soon\"); a summoned Skeletoid's brings the next.",
        f"handlers[{EV_KILLED}] = function(context)",
        "    local a = context.actorIndex",
        "    if KILL_CONTROL_SENDERS[a] then killControlOneDown() end",
        "    if a == LICH then set(\"Isle.LichGone\", 1) end",
        "    skeletoidKilled(a)",
        "end",
        "",
        "-- FORADWORLD.scr:23-36, 135 OnWorldSwitch TakeKey: the location keys go as the party leaves.",
        f"handlers[{EV_LEAVE}] = function()",
        "    for k = 1024, 1033 do MM9.takeKey(k) end",
        "end",
        "",
        "-- The map load (after ForadWorld.scr's Init, outdoor_blv.py).",
        "handlers.regionLoad = function()",
        "    -- game.cpp (cshell.dll 0x100a6e40) entering worlds\\isleofashes: before the cinema (key 28) and the first",
        "    -- time (key 481) it gives key 481 and plays movies\\Shipwreck.bik (MM9Shipwreck).",
        "    if not has(28) and not has(481) then",
        "        MM9.giveKey(481)",
        "        evt.ShowMovie(\"MM9Shipwreck\", true)",
        "    end",
        "    -- IS_BOAT.scr:46-51, 64 placed2: the boat stays hidden until it leaves.",
        "    evt.SetSprite(BOAT, 0)",
        "    -- FORAD.scr:96-108, 178-183 DeleteCheck: Forad has joined the party (key 29).",
        "    if has(29) then show(FORAD, false) end",
        "    -- YRSA.scr:106-118, 138-139 Init: Yrsa is gone once Forad has joined (key 29) when the party comes back. MM9",
        "    -- has no saves on the isle, so it never reloads the map between Forad joining and Yrsa giving the Turret Key;",
        "    -- here a reload in that window would hide her and lock the bunker for good. She leaves after the cinema",
        "    -- (key 28) instead.",
        "    if has(29) and has(28) then show(YRSA, false) end",
        "    -- HIDEMODEL.scr:26-34, 55-70 (\"28 unhide\"): Annud Redeye is there after the cinema.",
        "    show(ANNUD, has(28))",
        "    -- AUTORESURRECT.scr:66-80: the Bone Thrashers wait under the ground until their trigger has fired.",
    ]
    for name in PLAYER_TRIGGERS:
        if risers[name]:
            hidden = "; ".join(f"show({const(n)}, false)" for n in risers[name])
            lines.append(f"    if var(\"Isle.TriggerCount.{name}\") == 0 then {hidden} end")
    lines += [
        "    -- Saves from before the cinematic (2026-11-06) could hold the old timed cinema half played: it starts over.",
        "    if evt.GetMapVar(\"Isle.CinemaStart\", -1) >= 0 and not has(28) then",
        "        set(\"Isle.CinemaStart\", -1)",
        "        for _, step in ipairs(CINEMA_STEPS) do set(\"Isle.CinemaStep.\" .. step[1], 0) end",
        "    end",
        "    -- ISLEASHESBOOK.scr:230-243 Init: after the cinema (key 28) FortWall0 is gone and the islet sunk (Terrain3",
        "    -- sinkspeed, open); the Lich went with it (FortWall0 is ShouldMiniSave: its death trigger does not fire again).",
        "    if has(28) then",
        "        removeFaces(FORT_WALL0)",
        "        isletOpen()",
        "        set(\"Isle.FortWall0Destroyed\", 1)",
        "        set(\"Isle.LichGone\", 1)",
        "        show(LICH, false)",
        "    end",
        "end",
        "",
    ]
    script.add(lines, *registrations)
    script.hooks += [
        f"RegisterMapTimerEvent({EV_TICK}, seconds(TICK_SECONDS), handlers[{EV_TICK}], \"Isle of Ashes story\")",
        f"RegisterMonsterKilledHook({EV_KILLED}, \"Isle of Ashes deaths\", handlers[{EV_KILLED}])",
        f"RegisterMapOnLeaveEvent({EV_LEAVE}, \"Isle of Ashes location keys\", handlers[{EV_LEAVE}])",
    ]
