"""
Boot Camp (MM9's tutorial island, Ravensford) map Lua: its scripted objects as native handlers, each citing its .scr
(mm9/extracted/SCRIPTS/SCRIPTS; behaviour spec: work/scr_spec.md). Loaded by ../mm9r_common/outdoor_blv.py `map_script`
after the shared doors, chests and ForadWorld.scr (devdocs/mm9_rework/REGIONS_FINISH.md step 2). RUDE exits are event
50000 + the DAT object index, found-player events 56000 + index (game/mm9/Mm9RudeDialogue.h).

- The tutorial scrolls (Givetake.scr "<item> 1" on Prop4-7 and Prop35-38: Spells, Skills, Classes, Notes, Shopkeepers,
  Movement I and II, Combat) and the museum's spell scrolls (BootGive.scr "<item>" on Prop3 and Prop39-43): world
  items (../mm9r_common/dungeon/pickups.py), picked up as any ground item.
- Grandpa (NPC436.scr, CommonerHuman2MaleA0, RUDE 436): the dialogue's exit gives Interface I and II (items 579, 580)
  while the party has no Interface I, and once the training is done (key 475) Strategy Tips, Disarm Trap Skill and
  Identify Item Skill (589, 298, 302; key 496). He greets the party once when he first sees it (:Init OnFoundPlayer
  DoRude, bSpokeTo): the found-player event, which only outdoor maps raise for now (work/scr_spec.md). Leaving the
  island (Trigger0 at the dock sends him "Leave") gives key 473, Ravensford training completed: the map's leave event
  (the boat is Boot Camp's only exit).

- The museum's demonstrations (BC_Manager.scr, "SpawnLoc0 SpawnLoc1 SpawnLoc2"; `museum_lines`): Switch0 ("fight")
  brings an Evil Grand Sorcerer and an Oculus (BC_MonsterFight.scr) out of a mist at SpawnLoc0/1, the party's friends
  and each other's enemies, for 120 s or until one dies, when the other vanishes in a mist 2 s later; Switch1 ("open")
  brings a Reverend Monk (BC_MonsterOpen.scr) out of a mist at SpawnLoc2, who walks to TreasureChest4, 3 and 0 in turn
  (evt.MoveActorTo), opening each to the crowd's cheer; the black chest (BC_TreasureChest.scr "1") springs its trap,
  a column of fire, and he dies and is gone 2 s later. Each switch works again once its show is over. Not carried:
  the chests' lid animations and the monk's castspell3 clip (static decoration models).

- MM9's intro movie (MM9Intro, from movies\\intro.bik) on the party's first arrival (`WORLD_INTRO_VAR`): MM9 itself
  plays it at start-up; OpenYAMM plays each world's intro at its start map.

The dock's Trigger0 -> ExitTrigger0 link is the transitions table's (work/scr_spec.md).
"""

from __future__ import annotations

EV_LEAVE = 600          # the map's leave event: NPC436.scr :OnLeave
EV_MUSEUM_POLL, EV_MONK_AT_CHEST, EV_MUSEUM_KILLED = 610, 611, 612    # BC_Manager.scr's clock, the monk's arrivals, deaths
# BC_Manager.scr's spawns: the CacheOnly templates (overrides.yml monster_classes) by class
FIGHTERS = ("EvilGrandSorcererCACHEONLY", "OrbusCACHEONLY")             # BC_MonsterFight.scr: at SpawnLoc0, SpawnLoc1
MONK = "ReverendMonkCACHEONLY"                                          # BC_MonsterOpen.scr: at SpawnLoc2
MONK_CHESTS = ("TreasureChest4", "TreasureChest3", "TreasureChest0")    # its walk; the last is the trapped black chest
# BC_MonsterOpen.scr's PlaySound after each chest (the next walk starts when it ends)
MONK_SOUNDS = ("ambient/people/crowdnoise-cheer01.wav", "ambient/people/crowdnoise-cheer02.wav",
               "ambient/people/crowdnoise-ohhh 02.wav")
MONK_STAND_OFF_LT = 70  # where the monk stops: this far before a chest's centre, on his way from SpawnLoc2
FIGHT_SECONDS = 120     # BC_Manager.scr :StartFight Wait 0, 120, ForceEndFight
POLL_SECONDS = 0.25
GRANDPA = "CommonerHuman2MaleA0"
WORLD_INTRO_VAR = "OpenYAMM.WorldIntro.MM9"     # the intro has played (MM6's and MM8's are OpenYAMM.WorldIntro.MM6/8)


def index_of(build, name: str) -> int:
    return build.source.by_name[name.lower()]["index"]


def extend(hooks, build, script) -> None:
    tag = "bootcamp"
    lines = [
        "handlers.regionLoad = function()",
        "    -- MM9's opening movie (movies\\intro.bik, which cshell.dll menus.cpp plays at start-up after the logos):",
        "    -- OpenYAMM plays a world's intro on the party's first arrival at its start map, as for MM6 and MM8.",
        f"    if evt.GetGlobalVar(\"{WORLD_INTRO_VAR}\", 0) == 0 then",
        f"        evt.SetGlobalVar(\"{WORLD_INTRO_VAR}\", 1)",
        "        evt.ShowMovie(\"MM9Intro\", true)",
        "    end",
    ]
    lines += ["end", ""]
    grandpa = index_of(build, GRANDPA)
    lines += [
        "",
        "-- NPC436.scr :OnRude (Grandpa, RUDE 436): with the training done (key 475) Strategy Tips, Disarm Trap Skill and",
        "-- Identify Item Skill once (key 496); otherwise Interface I and II while the party has no Interface I.",
        f"handlers[{50000 + grandpa}] = function()   -- {GRANDPA}",
        "    if has(475) and not has(496) then",
        f"        MM9.giveItem(589, \"{tag}:NPC436\"); MM9.giveItem(298, \"{tag}:NPC436\"); "
        f"MM9.giveItem(302, \"{tag}:NPC436\")",
        "        MM9.giveKey(496)",
        "        return",
        "    end",
        f"    if MM9.hasItem(579, \"{tag}:NPC436\") == 1 then return end",
        f"    MM9.giveItem(579, \"{tag}:NPC436\"); MM9.giveItem(580, \"{tag}:NPC436\")",
        "end",
        "-- NPC436.scr :Init -> OnFoundPlayer :DoRude: the first time he sees the party (bSpokeTo) his dialogue and voice.",
        f"handlers[{56000 + grandpa}] = function()   -- {GRANDPA}",
        f"    if not MM9.foundPlayerEnabled({grandpa}) then return end",
        f"    MM9.disableFoundPlayer({grandpa})",
        "    MM9.openRude(436)",
        "    MM9.playSound(\"voices/npc/npc_249.wav\")",
        "end",
        "-- NPC436.scr :OnLeave (Trigger0 at the dock sends \"Leave\" as the party boards): key 473, training completed.",
        "-- A slain Grandpa takes no Leave (MM9.receives, scr_audit README \"Implicit engine semantics\"): no key.",
        f"handlers[{EV_LEAVE}] = function()",
        f"    if not MM9.receives(\"bootcamp\", \"{GRANDPA}\", \"Leave\", "
        f"{getattr(hooks, 'npc_actor', {}).get(GRANDPA, 'nil')}) then return end",
        "    if not has(473) then MM9.giveKey(473) end",
        "end",
        "",
    ]
    registrations = [(50000 + grandpa, "Grandpa", None), (56000 + grandpa, "Grandpa", None)]
    script.add(lines, *registrations)
    script.hooks.append(f'RegisterMapOnLeaveEvent({EV_LEAVE}, "Leaving Boot Camp", handlers[{EV_LEAVE}])')
    museum, museum_registrations, museum_load = museum_lines(build)
    script.add(museum, *museum_registrations)
    script.hooks.append(f'RegisterMonsterKilledHook({EV_MUSEUM_KILLED}, "Museum shows", handlers[{EV_MUSEUM_KILLED}])')
    # (the museum's functions are declared after regionLoad: it calls them through the handlers table)
    regionLoad = next(k for k, line in enumerate(script.lines) if line == "handlers.regionLoad = function()")
    script.lines.insert(regionLoad + 1, "    if handlers.museumLoad then handlers.museumLoad() end")
    script.add(["handlers.museumLoad = function()", *museum_load, "end", ""])


def native_on_floor(build, lt) -> list:
    """A DAT position as a native point on the floor under it (the position itself where there is none)."""
    floor = build.content.floor_at(lt[0], lt[2], lt[1] + 16)
    point = build.project.native([lt[0], lt[1] if floor is None else floor, lt[2]])
    return [int(round(v)) for v in point]


def wav_seconds(name: str) -> float:
    import wave
    from dungeon.source import ROOT
    with wave.open(str(ROOT / "assets_dev/worlds/mm9/audio" / name)) as stream:
        return stream.getnframes() / stream.getframerate()


def museum_lines(build) -> tuple[list, list, list]:
    """BC_Manager.scr's two shows (module docstring): the Lua, its registrations and its map-load lines. The clock is
    a poll every POLL_SECONDS while a show runs; a load ends a show under way (MM9 keeps its spawns in the mini save;
    walks are not saved here) and re-arms the switches."""
    from dungeon.lua import point
    import numpy as np
    bases = build.content.monster_bases(cache_only=True)
    sorcerer, oculus = (bases[name]["monster_id"] for name in FIGHTERS)
    monk = bases[MONK]["monster_id"]
    by_name = build.source.by_name
    manager = next(o for o in build.source.objects
                   if str(o["properties"].get("ScriptName") or "").lower().endswith("bc_manager.scr"))
    spawn_names = str(manager["properties"]["ScriptParams"]).split()
    spawns = [native_on_floor(build, by_name[name.lower()]["properties"]["Pos"]) for name in spawn_names]
    monk_from = np.array(by_name[spawn_names[2].lower()]["properties"]["Pos"], float)
    stops = []
    for name in MONK_CHESTS:
        chest = np.array(by_name[name.lower()]["properties"]["Pos"], float)
        away = monk_from - chest
        away[1] = 0.0
        stop = chest + away / max(np.linalg.norm(away), 1.0) * MONK_STAND_OFF_LT
        stops.append(native_on_floor(build, stop))
        monk_from = stop
    chests = [native_on_floor(build, by_name[name.lower()]["properties"]["Pos"]) for name in MONK_CHESTS]
    waits = [int(np.ceil(wav_seconds(sound) / POLL_SECONDS)) for sound in MONK_SOUNDS]
    switch_events = {}
    for m in build.movers:
        if m["group"] in ("Switch0", "Switch1") and m["event"]:
            switch_events[m["group"]] = (m["event"], m["door_id"])
    ticks = lambda seconds: int(round(seconds / POLL_SECONDS))       # noqa: E731
    lines = [
        "-- BC_Manager.scr (ScriptObject BC_Manager, \"" + " ".join(spawn_names) + "\"): the museum's shows. Switch0's",
        "-- OpenTrigger sends it \"fight\", Switch1's \"open\" (each switch then springs back: its OpenTrigger1 \"close\").",
        f"local BC = {{sorcerer = {sorcerer}, oculus = {oculus}, monk = {monk}, spawns = {{"
        + ", ".join(point(p) for p in spawns) + "},",
        "    stops = {" + ", ".join(point(p) for p in stops) + "}, chests = {"
        + ", ".join(point(p) for p in chests) + "},",
        "    sounds = {" + ", ".join(f'"{name}"' for name in MONK_SOUNDS) + "}, waits = {"
        + ", ".join(map(str, waits)) + "}}",
        "local function bcIndex(name) local v = var(name) return v > 0 and v - 1 or nil end",
        "local function bcMist(index)",
        "    local x, y, z = evt.GetMapActorPosition(index)",
        "    if x ~= nil then evt.SpawnWorldEffect(\"mm9:mist\", x, y, z + 64, 1) end",
        "end",
        "local function bcSpawn(monster, at, yaw)",
        "    local _, made = evt.SummonMonstersById({monster = monster, x = at[1], y = at[2], z = at[3], radius = 0, "
        "count = 1, hostile = false, loot = false, yawDegrees = yaw})",
        "    local index = made ~= nil and made[1] or nil",
        "    if index ~= nil then bcMist(index) end   -- DoClientFX hSpawn, SPELL_MIST",
        "    return index",
        "end",
        "local function bcRemove(name)",
        "    local index = bcIndex(name)",
        "    if index ~= nil then evt.StopActorMove(index); MM9.removeActor(index) end",
        "    set(name, 0)",
        "end",
        "local function bcClock() evt.StartTimer(" + str(EV_MUSEUM_POLL) + f", seconds({POLL_SECONDS})) end",
        "-- The party's friends (AddFriend Player; BC_MonsterOpen.scr: AddFriend AIBase), and the fighters each other's",
        "-- enemies (AddEnemy AIBase): MM9's rows are the party's enemies by the table, so the map sets these.",
        "local function bcRelations()",
        "    evt.SetMonsterRelation(BC.sorcerer, 0, 0); evt.SetMonsterRelation(BC.oculus, 0, 0); "
        "evt.SetMonsterRelation(BC.monk, 0, 0)",
        "    evt.SetMonsterRelation(BC.sorcerer, BC.oculus, 4); evt.SetMonsterRelation(BC.oculus, BC.sorcerer, 4)",
        "end",
        "local function bcFight()   -- :StartFight",
        "    if var(\"BCFight\") ~= 0 then return end",
        "    bcRelations()",
        "    -- :SetupFighting: the sorcerer faces +x (FaceDir 1, 0, 0), the Oculus -x: each other",
        "    local a, b = bcSpawn(BC.sorcerer, BC.spawns[1], 0), bcSpawn(BC.oculus, BC.spawns[2], 180)",
        "    set(\"BCSorcerer\", a ~= nil and a + 1 or 0); set(\"BCOculus\", b ~= nil and b + 1 or 0)",
        f"    set(\"BCFight\", 1); set(\"BCFightLeft\", {ticks(FIGHT_SECONDS)}); set(\"BCSurvivorLeft\", 0)",
        "    bcClock()",
        "end",
        "local function bcFightOver()   -- :ForceEndFight, :RemoveCreature",
        "    bcRemove(\"BCSorcerer\"); bcRemove(\"BCOculus\")",
        "    set(\"BCFight\", 0); set(\"BCSurvivorLeft\", 0)",
        "end",
        "local function bcOpen()   -- :StartOpen; BC_MonsterOpen.scr waits 0.1 s, then 1 s, then walks",
        "    if var(\"BCMonkStage\") ~= 0 then return end",
        "    bcRelations()",
        "    local m = bcSpawn(BC.monk, BC.spawns[3])",
        "    if m == nil then return end",
        f"    set(\"BCMonk\", m + 1); set(\"BCMonkStage\", 1); set(\"BCMonkChest\", 0); set(\"BCMonkLeft\", {ticks(1.1)})",
        "    bcClock()",
        "end",
        "local function bcMonkWalk()   -- :WalkToFirst, :WalkToSecond, :WalkToThird",
        "    local m, k = bcIndex(\"BCMonk\"), var(\"BCMonkChest\") + 1",
        "    local stop = BC.stops[k]",
        "    set(\"BCMonkChest\", k); set(\"BCMonkStage\", 2)",
        f"    if m == nil or not evt.MoveActorTo(m, stop[1], stop[2], stop[3], {EV_MONK_AT_CHEST}) then "
        "set(\"BCMonkStage\", 0) end",
        "end",
        "local function bcMonkGone()   -- the link broken: \"open\" works again",
        "    bcRemove(\"BCMonk\"); set(\"BCMonkStage\", 0)",
        "end",
        f"handlers[{EV_MONK_AT_CHEST}] = function()   -- :OpenFirst, :OpenSecond, :OpenThird",
        "    if var(\"BCMonkStage\") ~= 2 then return end",
        "    local k, c = var(\"BCMonkChest\"), BC.chests[var(\"BCMonkChest\")]",
        "    evt.PlaySoundName(BC.sounds[k], c[1], c[2], c[3])",
        "    if k < #BC.stops then",
        "        set(\"BCMonkStage\", 1); set(\"BCMonkLeft\", BC.waits[k])",
        "    else",
        "        -- BC_TreasureChest.scr \"1\" :SpringTrap: a column of fire on the opener and the latch; :KillTheGuy 1 s",
        "        -- later, :RemoveTheGuy 2 s after that",
        "        local m = bcIndex(\"BCMonk\")",
        "        local x, y, z = nil, nil, nil",
        "        if m ~= nil then x, y, z = evt.GetMapActorPosition(m) end",
        "        if x ~= nil then evt.SpawnWorldEffect(\"mm9:column_of_fire\", x, y, z, 1) end",
        "        evt.PlaySoundName(\"door/doorlatch01.wav\", c[1], c[2], c[3])",
        f"        set(\"BCMonkStage\", 3); set(\"BCMonkLeft\", {ticks(1)})",
        "    end",
        "    bcClock()",
        "end",
        f"handlers[{EV_MUSEUM_POLL}] = function()",
        "    local running = false",
        "    if var(\"BCSpring\") > 0 then   -- the pushed switches spring back",
        "        running = true",
        "        set(\"BCSpring\", var(\"BCSpring\") - 1)",
        "        if var(\"BCSpring\") == 0 then "
        + " ".join(f"evt.SetDoorState({door}, DoorAction.Close)" for _, door in switch_events.values()) + " end",
        "    end",
        "    if var(\"BCFight\") == 1 then",
        "        running = true",
        "        set(\"BCFightLeft\", var(\"BCFightLeft\") - 1)",
        "        local survivor = var(\"BCSurvivorLeft\")",
        "        if survivor > 0 then set(\"BCSurvivorLeft\", survivor - 1) end",
        "        if var(\"BCFightLeft\") <= 0 or survivor == 1 then bcFightOver(); running = false end",
        "    end",
        "    local stage = var(\"BCMonkStage\")",
        "    if stage == 1 or stage == 3 or stage == 4 then",
        "        running = true",
        "        set(\"BCMonkLeft\", var(\"BCMonkLeft\") - 1)",
        "        if var(\"BCMonkLeft\") <= 0 then",
        "            if stage == 1 then bcMonkWalk()",
        "            elseif stage == 3 then   -- :KillTheGuy",
        "                local m = bcIndex(\"BCMonk\")",
        "                if m ~= nil then evt.KillMapActor(m) end",
        f"                set(\"BCMonkStage\", 4); set(\"BCMonkLeft\", {ticks(2)})",
        "            else bcMonkGone() end",
        "        end",
        "    elseif stage == 2 then",
        "        running = true",
        "    end",
        "    if running then bcClock() end",
        "end",
        "-- :OnObjectLinkBroken: one fighter dead, the other vanishes in a mist 2 s later; the monk dead (by the trap or",
        "-- the party), \"open\" works again once his body is gone.",
        f"handlers[{EV_MUSEUM_KILLED}] = function(context)",
        "    local i = context.actorIndex",
        "    if i == nil then return end",
        "    if var(\"BCFight\") == 1 and var(\"BCSurvivorLeft\") == 0 and (i == bcIndex(\"BCSorcerer\") "
        "or i == bcIndex(\"BCOculus\")) then",
        "        local other = i == bcIndex(\"BCSorcerer\") and bcIndex(\"BCOculus\") or bcIndex(\"BCSorcerer\")",
        "        if other ~= nil then bcMist(other) end",
        f"        set(\"BCSurvivorLeft\", {ticks(2) + 1})",
        "    elseif i == bcIndex(\"BCMonk\") and var(\"BCMonkStage\") ~= 4 then",
        "        evt.StopActorMove(i)",
        f"        set(\"BCMonkStage\", 4); set(\"BCMonkLeft\", {ticks(2)})",
        "        bcClock()",
        "    end",
        "end",
    ]
    registrations = [(EV_MONK_AT_CHEST, "Museum monk", None), (EV_MUSEUM_POLL, "Museum shows", None, "timer")]
    for group, show in (("Switch0", "bcFight"), ("Switch1", "bcOpen")):
        if group not in switch_events:
            continue
        event, door = switch_events[group]
        lines += [f"-- {group}: pushed in, it springs back (OpenTrigger1 \"close\") and starts its show.",
                  f"handlers[{event}] = function()",
                  f"    evt.SetDoorState({door}, DoorAction.Open)",
                  f"    set(\"BCSpring\", {ticks(1)}); bcClock()",
                  f"    {show}()",
                  "end"]
    lines.append("")
    load = ["    -- BC_Manager.scr: a show under way when the map was left or saved ends; both switches work again",
            "    bcRelations()",
            "    bcFightOver(); bcMonkGone(); set(\"BCSpring\", 0)",
            f"    evt.SetDoorState({switch_events['Switch0'][1]}, DoorAction.Close)" if "Switch0" in switch_events
            else "",
            f"    evt.SetDoorState({switch_events['Switch1'][1]}, DoorAction.Close)" if "Switch1" in switch_events
            else ""]
    return lines, registrations, [line for line in load if line]
