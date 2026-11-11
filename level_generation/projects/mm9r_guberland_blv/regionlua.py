"""
Guberland (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests and ForadWorld.scr
(devdocs/mm9_rework/REGIONS_FINISH.md step 2). RUDE exits are event 50000 + the DAT object index, a click before the
dialogue 53000 + index (game/mm9/Mm9RudeDialogue.h). The behaviour spec of every script is work/scr_spec.md.

- Thorir Mouth (NPC133.scr): the six Gathering prizes for the Capstone of Order, Nicolai's circus job.
- Ivan the Smart (NPC130.scr): the trivia contest's letter of victory.
- The hag's hair (givetake.scr on the hairbrush): a world item (../mm9r_common/dungeon/pickups.py).
- The Mercenary promotion (NPC186.scr, NPC187.scr, atlipromo.scr, Atliwagon.scr): the late guard's relief at the dock
  from 2:45 to 3:15 (he walks off), the bandits at 3:30, Atli at 6:00 once they are dead (he, his daughter and the
  guard walk to the dock), his reward and promotion; raiders alive at 5:30 fail the night (they vanish, the guard is
  back on duty for the next night); by the dock a rest stops at those times (evt.SetRestAlarm); Atli, his daughter, the guard and
  his ship gone once it is done.
- The Gathering's games (THJORGARDGAMESCOMMON.inc): tickets (HucksterMod.scr), ring the bell (DingTheBell.scr,
  BellWeight.scr), the runes (Mastermind*.scr and the Switch), arm wrestling (ArmWrestle.scr), the stones game
  (StonesGame.scr, StonesSquare.scr, StonesPiece.scr: Piece0-35 clicked, the bot answers; key 7110) and whack-a-honky
  (Whack-a-Honky.scr on Honky0-3, Switch0 its start lever; key 7113); every win gives a random prize. The stones game
  and whack-a-honky are Thjorgard's (mm9r_thjorgard_blv/regionlua.py, its scenario_games.yml) with Guberland's win
  keys; as there, placed stones show the 2x coloured stones and the idle geese all stand.
- Nicolai Ironfist (NPC414.scr) here only with key 121; Alvar the Clumsy (Retainer.scr) hidden while hired.
- Scandlan's and Broccan's new-game talk (NPC150.scr, NPC151.scr): Scandlan's FoundPlayer starts the cinematic
  newgame_talk (no cameras: their voices and conv clips; key 5020; Broccan walks off to Mata), README "Cinematics".

The late guard (AtliGuard, WealthyTownGuard1: overrides.yml `outdoor.people` with the Guard row 9111 of his guard.abc
model) stands at his post until relieved (key 197). Not here (work/scr_spec.md): the hag and TronPlayer's dialogue (not placed / no RUDE id: shared npcs()),
Broccan's wander after the talk, PropAnim banners and the stat stone, NPC voices.
"""

from __future__ import annotations

import json
import math
import wave
from pathlib import Path

import cutscenes
from dungeon import lua
from quest_xp import balanced_experience, experience_note

EV_PROP = 330           # a scripted prop's click: EV_PROP + k
COG_PROP = 400          # a prop's SetSprite key: COG_PROP + k
T_POLL, T_BELL, T_SWITCH = 600, 601, 602
T_HONK, T_HONK_END = 603, 604   # timers: whack-a-honky's countdown and geese, its ten seconds of play
T_COWER = 605           # timer: the end of Mata's cower (ArmWrestle.scr :FinishCower)
EV_GAME_PROP = 700      # the stones game's pieces and the geese: a click EV_GAME_PROP + k
COG_GAME_PROP = 700     # and their SetSprite key COG_GAME_PROP + k
PIECES = [f"Piece{k}" for k in range(36)]           # StonesPiece.scr, on Square0-35 (StonesSquare.scr "Piece<k> <k>")
HONKIES = [f"Honky{k}" for k in range(4)]          # Whack-a-Honky.scr "<k> Honky 0 3"
GAME_PROPS = PIECES + HONKIES
# The stones' colours (StonesPiece.scr: yellow.dtx white, blue.dtx black), as in Thjorgard: only the 2x coloured
# stones exist as decorations (the runes game's)
STONE_EMPTY, STONE_WHITE, STONE_BLACK = "mm9_stone", "mm9_stoneyellow_x200", "mm9_stoneblue_x200"
KEY_STONES_WIN, KEY_HONKY_WIN = 7110, 7113         # THJORGARDGAMESCOMMON.inc :RecordStonesWin, :RecordHonkyWin
HONK_WIN = 8                                       # Whack-a-Honky.scr WIN_CONDITION
TEXT = {                        # MMIXSCRIPTTEXT.csv (RollOverText numbers), as Thjorgard's
    230: "White wins!!!", 231: "Black wins!!!", 233: "Stone must be placed adjacent to another of your stones.",
    235: "Five...", 236: "Four...", 237: "Three...", 238: "Two...", 239: "One...", 244: "Your move.",
}
TAG = "guberland"

# DAT name -> script, for the props with a click
# (givetake.scr's hairbrush Prop1 is a world item, ../mm9r_common/dungeon/pickups.py: the hag's hair, item 240; the
# stool Prop0, whose Proptrigger.scr used the brush, needs no click of its own)
CLICK_PROPS = {
    **{f"ColorButton{k}": "mastermindcolor.scr" for k in range(5)},
    **{f"ColorSpace{k}": "mastermindspace.scr" for k in range(4)},
}
# DAT name -> script, for the props shown or hidden (or recoloured) by Lua
COG_PROPS = {
    "Cart": "atliwagon.scr",
    **{f"ColorSpace{k}": "mastermindspace.scr" for k in range(4)},
}
COLOUR_NAMES = ("red", "blue", "yellow", "orange", "green")    # MastermindColor.scr p0 0..4
RELIEF_RADIUS_LT = 768          # atlipromo.scr OnFoundPlayer: the party at the late guard's post (scr_spec.md)
PRIZES = range(362, 368)        # THJORGARDGAMESCOMMON.inc PRIZE_GUBER_MIN..MAX
KEYED_DOORS: dict = {}
# NPC150.scr / NPC151.scr's talk as the cinematic newgame_talk (no cameras): its done event, steps 36001..
NEWGAME_TALK = "newgame_talk"
EV_NEWGAME_TALK = 36000
TALK_KEY = 5020                 # NPC150.scr :OnStart givekey: the talk has been heard
TALK_BROKEN = "NewgameTalkBroken"   # map var: a slain speaker ended the talk (newgame_talk_scene)
BROCCAN_STOP = 100              # native units short of Mata where Broccan's walk (WalkTo Mata) ends


def placed_props() -> dict:
    """props.json by DAT name (source_name)."""
    entries = json.loads((Path(__file__).parent / "props.json").read_text())
    return {e["source_name"]: e for e in entries}


def prop_events(build) -> tuple[dict, dict]:
    present = placed_props()
    events = {name: EV_PROP + k for k, name in enumerate(CLICK_PROPS) if name in present}
    cogs = {name: COG_PROP + k for k, name in enumerate(COG_PROPS) if name in present}
    events.update({name: EV_GAME_PROP + k for k, name in enumerate(GAME_PROPS) if name in present})
    cogs.update({name: COG_GAME_PROP + k for k, name in enumerate(GAME_PROPS) if name in present})
    return events, cogs


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def index(build, name: str) -> int:
    return build.source.by_name[name.lower()]["index"]


def rude_exit(build, name: str) -> int:
    return 50000 + index(build, name)


def rude_use(build, name: str) -> int:
    return 53000 + index(build, name)


def found_player(build, name: str) -> int:
    return 56000 + index(build, name)


def native(build, name: str, on_floor: bool = True) -> list[int]:
    """A DAT object's position in the native frame (on the floor under it)."""
    pos = build.source.by_name[name.lower()]["properties"]["Pos"]
    y = pos[1]
    if on_floor:
        floor = build.content.floor_at(pos[0], pos[2], pos[1] + 50)
        y = floor if floor is not None else y
    return [int(round(v)) for v in build.project.native([pos[0], y, pos[2]])]


def door_group(build, group: str) -> tuple[int, list[int], dict | None]:
    """A mover group's click event (0 if none), its door ids and its first mover."""
    movers = [m for m in build.movers if m["group"] == group]
    event = next((m["event"] for m in movers if m["event"]), 0)
    return event, [m["door_id"] for m in movers], (movers[0] if movers else None)


def doors_call(ids: list[int], action: str) -> str:
    return " ".join(f"evt.SetDoorState({d}, DoorAction.{action})" for d in ids)


def extend(hooks, build, script) -> None:
    events, cogs = prop_events(build)
    actor = getattr(hooks, "npc_actor", {})
    props = placed_props()
    # ArmWrestle.scr :StartCower: Mata's clips and their length (cowerstart, cower five times, cowerstop)
    mata = actor["CommonerHalfOrcMaleA0"]
    clips = lua.model_clip_seconds(next(a["monster_id"] for a in build.content.report["actors"]
                                        if a["actor_index"] == mata))
    cower_seconds = round(clips["cowerstart"] + 5 * clips["cower"] + clips["cowerstop"], 1)
    lines = [
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "",
    ]
    registrations = []
    load = []

    def item(verb: str, number, who: str) -> str:
        return f"MM9.{verb}Item({number}, \"{TAG}:{who}\")"

    # --- Thorir Mouth and Ivan the Smart -------------------------------------------------------------------------
    take_prizes = "; ".join(item("take", k, "Thorir") for k in PRIZES)
    lines += [
        "-- NPC133.scr (Thorir Mouth, RUDE 133). :OnUse :ItemCheck: all six Gathering prizes (362-367) in the",
        "-- packs give key 487 (his row 'We've got your set of prizes' gives 488).",
        f"handlers[{rude_use(build, 'RUDEProp10')}] = function()",
        "    local n = 0",
        f"    for k = {PRIZES.start}, {PRIZES.stop - 1} do",
        f"        if MM9.hasItem(k, \"{TAG}:Thorir\") == 1 then n = n + 1 end",
        "    end",
        "    if n == 6 then MM9.giveKey(487) end",
        "    MM9.openRude(133)",
        "end",
        "-- NPC133.scr :OnRude: the prizes taken (488, not 490: key 490); Nicolai's job (121, not 122: 5 000 gold,",
        "-- 20 000 experience, key 122); the Capstone of Order (488, not 188: item 396, 146 000 experience, key 188).",
        f"handlers[{rude_exit(build, 'RUDEProp10')}] = function()",
        f"    if has(488) and not has(490) then {take_prizes}; MM9.giveKey(490) end",
        f"    if has(121) and not has(122) then reward(122, {balanced_experience(20000, 122)}, 5000) end"
        f"{experience_note(20000, 122)}",
        f"    if has(488) and not has(188) then {item('give', 396, 'Thorir')}; "
        f"reward(188, {balanced_experience(146000, 188)}, 0) end{experience_note(146000, 188)}",
        "end",
        "-- NPC130.scr (Ivan the Smart, RUDE 130) :Trivia: beaten (60, not 164): key 164, 5 000 experience, item 400.",
        f"handlers[{rude_exit(build, 'RUDEProp9')}] = function()",
        f"    if has(60) and not has(164) then reward(164, {balanced_experience(5000, 164)}, 0); "
        f"{item('give', 400, 'Ivan')} end",
        "end",
        "",
    ]
    registrations += [(rude_use(build, "RUDEProp10"), "Thorir Mouth", None),
                      (rude_exit(build, "RUDEProp10"), "Thorir Mouth", None),
                      (rude_exit(build, "RUDEProp9"), "Ivan the Smart", None)]

    # --- the Mercenary promotion ----------------------------------------------------------------------------------
    post = native(build, "AtliGuard")
    spawn = native(build, "SpawnMarker")
    radius = int(round(RELIEF_RADIUS_LT * 2.56))
    rows = {}
    for a in build.content.report["actors"]:
        rows.setdefault(a["class"], a["monster_id"])
    marker = native(build, "Atlimarker0")
    away = native(build, "AtliMarker")
    walkers = [actor[n] for n in ("Atli", "AtliDaughter", "AtliGuard") if n in actor]
    summons = [f"banditsRun(evt.SummonMonstersById({{monster = {rows[c]}, x = {spawn[0]}, y = {spawn[1]}, "
               f"z = {spawn[2]}, radius = 128, count = 3}}))" for c in ("Bandit", "Cutpurse") if c in rows]
    lines += [
        "-- The Mercenary promotion. atlipromo.scr (the late guard at the dock, AtliGuard): @m 2:45 key 376,",
        "-- @m 3:15 taken; :OnLeave (OnFoundPlayer): with 376 and Atli's job (125) he gives 197 and walks off to",
        f"-- AtliMarker. Here the party standing within {RELIEF_RADIUS_LT} LT of his post stands for his sighting.",
        "-- Atliwagon.scr: @M 3:30 three Bandits and three Cutpurses at SpawnMarker (once, with 197); @M 6:00",
        "-- :summonatli: key 126 and Atli's :OnSummon: he, his daughter (NPC187.scr :OnReturn) and the guard",
        "-- (atlipromo.scr :OnReturn) walk to the dock, Atlimarker0.",
        "-- The watch is a night's (the user, 2026-11-08): the relief starts it; the raid comes at 3:30 of that night",
        "-- (the party on the map); Atli comes at 6:00 once every raider is dead (a party that left after the fight",
        "-- finds him come when it is back). Raiders still alive at 5:30, or a raid the party was away for, fail the",
        "-- night: the raiders are gone, key 197 is taken and the guard walks back to his post, to be relieved again",
        "-- the next night. MM9's clock triggers fire during a wait: by the dock, the rest alarm (evt.SetRestAlarm)",
        "-- stops a rest at 2:45 (at the post), 3:30, 5:30 and 6:00. The walks run on after a load (GuardLeaving 1 to",
        "-- AtliMarker, 2 back to the post; AtliComing); the guard stays until Atli is gone (127).",
        "-- BanditAttack.scr (their spawn string's script): :OnAttack runs each to Atlimarker0 (TerrainMode, Runto 256)",
        "-- until OnFoundPlayer, then stops and fights (:OnExit, BaseInit); arriving does the same. Here the watch's",
        "-- poll stops a runner the party is in sight of (evt.ActorSeesParty) and sets it on the party; a load sends",
        "-- the ones still running again (:Main OnPostSaveLoad OnAttack).",
        f"local ATLI_MARKER = {{{marker[0]}, {marker[1]}, {marker[2]}}}   -- Atlimarker0, the dock",
        f"local GUARD_AWAY = {{{away[0]}, {away[1]}, {away[2]}}}   -- AtliMarker",
        f"local GUARD_POST = {{{post[0]}, {post[1]}, {post[2]}}}   -- AtliGuard",
        f"local ATLI_WALKERS = {{{', '.join(str(i) for i in walkers)}}}   -- Atli, his daughter, the guard",
        "local DOCK_RANGE = 5120   -- the rest alarms stop a rest this near the dock",
        "local function banditsRun(count, made)",
        "    if made == nil then return end",
        "    for _, i in ipairs(made) do",
        "        local n = var(\"Runners\") + 1",
        "        set(\"Runners\", n); set(\"Runner\" .. n, i + 1)",
        "        local b = var(\"Bandits\") + 1",
        "        set(\"Bandits\", b); set(\"Bandit\" .. b, i + 1)",
        "        evt.MoveActorTo(i, ATLI_MARKER[1], ATLI_MARKER[2], ATLI_MARKER[3], 0, true)",
        "    end",
        "end",
        "local function banditsWatch(resend)",
        "    for n = 1, var(\"Runners\") do",
        "        local i = var(\"Runner\" .. n) - 1",
        "        if i >= 0 then",
        "            if evt.GetMapActorPosition(i) == nil or evt.ActorSeesParty(i) then",
        "                evt.StopActorMove(i); evt.SetActorTarget(i, \"party\"); set(\"Runner\" .. n, 0)   -- :OnExit",
        "            elseif resend then",
        "                evt.MoveActorTo(i, ATLI_MARKER[1], ATLI_MARKER[2], ATLI_MARKER[3], 0, true)",
        "            elseif not evt.IsActorMoving(i) then",
        "                set(\"Runner\" .. n, 0)   -- at Atlimarker0: Runto's Onexit, BaseInit",
        "            end",
        "        end",
        "    end",
        "end",
        "local function banditsLeft()   -- this night's raiders still standing",
        "    local left = 0",
        "    for n = 1, var(\"Bandits\") do",
        "        local i = var(\"Bandit\" .. n) - 1",
        "        if i >= 0 and MM9.actorAlive(i) then left = left + 1 end",
        "    end",
        "    return left",
        "end",
        "local function nextClock(at, minute)   -- the first game minute >= at whose time of day is `minute`",
        "    local t = math.floor(at / 1440) * 1440 + minute",
        "    if t < at then t = t + 1440 end",
        "    return t",
        "end",
        "local function near(i, p)   -- a walker at its walk's end (Walkto's 256 LT)",
        "    local x, y = evt.GetMapActorPosition(i)",
        "    return x == nil or (x - p[1]) ^ 2 + (y - p[2]) ^ 2 <= 655 ^ 2",
        "end",
        "local function walkOn(i, p)   -- a walk a load dropped, or one to start: sent again",
        "    if not near(i, p) and not evt.IsActorMoving(i) then evt.MoveActorTo(i, p[1], p[2], p[3]) end",
        "end",
        "local function walkTo(i, p)   -- a new walk, turning from the last one",
        "    evt.MoveActorTo(i, p[1], p[2], p[3])",
        "end",
        "local function watchFailed()   -- the raid not stopped by 5:30: the raiders make off, the guard is back on duty",
        "    for n = 1, var(\"Bandits\") do",
        "        local i = var(\"Bandit\" .. n) - 1",
        "        if i >= 0 and MM9.actorAlive(i) then evt.StopActorMove(i); MM9.removeActor(i) end",
        "    end",
        "    set(\"Bandits\", 0); set(\"Runners\", 0); set(\"BanditsSent\", 0); set(\"RelievedAt\", 0)",
        "    MM9.takeKey(197)",
        *([f"    set(\"GuardLeaving\", 2); walkTo({actor['AtliGuard']}, GUARD_POST)"] if "AtliGuard" in actor else []),
        "    evt.StatusText(\"The raiders got away. Atli's boat needs guarding again tonight.\")",
        "end",
        "local function atliWatch()",
        "    banditsWatch(false)",
        "    local now = math.floor(evt.CurrentGameMinutes())",
        "    local minute = now % 1440",
        "    local window = minute >= 165 and minute < 195",
        "    if window and not has(376) then MM9.giveKey(376) elseif not window and has(376) then MM9.takeKey(376) end",
        "    local x, y = evt.GetPartyPosition()",
        f"    local dx, dy = x - ({post[0]}), y - ({post[1]})",
        f"    local atPost = dx * dx + dy * dy <= {radius} * {radius}",
        "    local byDock = (x - ATLI_MARKER[1]) ^ 2 + (y - ATLI_MARKER[2]) ^ 2 <= DOCK_RANGE ^ 2",
        # :OnLeave is the guard's OnFoundPlayer: a slain guard sees nobody, so key 197 (and the job) never comes
        "    if has(376) and has(125) and not has(197) and not has(126) and atPost"
        + (f" and MM9.actorAlive({actor['AtliGuard']})" if "AtliGuard" in actor else "") + " then",
        "        MM9.giveKey(197); set(\"RelievedAt\", now)",
        *([f"        set(\"GuardLeaving\", 1); walkTo({actor['AtliGuard']}, GUARD_AWAY)   -- :OnLeave: walkto AtliMarker"]
          if "AtliGuard" in actor else []),
        "        evt.StatusText(\"The late guard leaves. Your watch begins.\")",
        "    end",
        *([f"    local g = var(\"GuardLeaving\")",
           "    if g ~= 0 and not has(126) then",
           "        local p = g == 1 and GUARD_AWAY or GUARD_POST",
           f"        if near({actor['AtliGuard']}, p) then set(\"GuardLeaving\", 0) else walkOn({actor['AtliGuard']}, p) end",
           "    end"] if "AtliGuard" in actor else []),
        "    local alarm = nil",
        "    if has(197) and not has(126) and not has(127) then",
        "        local at = var(\"RelievedAt\")",
        "        local raidAt, giveUpAt, atliAt = nextClock(at, 210), nextClock(at, 330), nextClock(at, 360)",
        "        if var(\"BanditsSent\") == 0 then",
        "            if now >= giveUpAt then watchFailed()",
        "            elseif now >= raidAt then",
        "                set(\"BanditsSent\", 1)",
        *[f"                {s}" for s in summons],
        "            else alarm = raidAt end",
        "        elseif banditsLeft() > 0 then",
        "            if now >= giveUpAt then watchFailed() else alarm = giveUpAt end",
        "        elseif now >= atliAt then",
        "            MM9.giveKey(126); set(\"AtliComing\", 1); set(\"GuardLeaving\", 0)   -- :summonatli, :OnSummon",
        "            for _, i in ipairs(ATLI_WALKERS) do walkTo(i, ATLI_MARKER) end",
        "        else alarm = atliAt end",
        "    elseif has(125) and not has(197) and not has(126) and atPost then",
        "        alarm = nextClock(now, 165)   -- to be there when he can be relieved",
        "    end",
        "    evt.SetRestAlarm((byDock or atPost) and alarm or nil)",
        "    if var(\"AtliComing\") == 1 and not has(127) then",
        "        local arrived = true",
        "        for _, i in ipairs(ATLI_WALKERS) do",
        "            if not near(i, ATLI_MARKER) then arrived = false; walkOn(i, ATLI_MARKER) end",
        "        end",
        "        if arrived then set(\"AtliComing\", 0) end",
        "    end",
        "end",
        f"handlers[{T_POLL}] = atliWatch",
        "",
        "-- NPC186.scr (Atli Sigmundssen, RUDE 186) :Mercpromo: Atli has come (126, not 127): key 127, 1 000 gold,",
        "-- 24 000 experience, the characters holding 401-404 promoted to Mercenary (each key taken).",
        f"handlers[{rude_exit(build, 'Atli')}] = function()",
        "    if not has(126) or has(127) then return end",
        f"    reward(127, {balanced_experience(24000, 127)}, 1000){experience_note(24000, 127)}",
        "    MM9.promoteParty(\"Mercenary\")   -- every eligible member (not MM9's per-character keys 401-404)",
        "end",
        "",
    ]
    registrations += [(T_POLL, "Atli's watch", None, "timer"), (rude_exit(build, "Atli"), "Atli Sigmundssen", None)]
    if "AtliGuard" in actor:
        load.append(f"    show({actor['AtliGuard']}, not has(127))   -- gone with Atli (atlipromo.scr :Init: once relieved)")
    load.append("    banditsWatch(true)   -- BanditAttack.scr OnPostSaveLoad OnAttack: the runners run on")
    load.append("    atliWatch()")
    for name, why in (("Atli", "NPC186.scr :Init"), ("AtliDaughter", "NPC187.scr :Init")):
        if name in actor:
            load.append(f"    show({actor[name]}, not has(127))   -- {why}: gone to Thronheim")
    if "Cart" in cogs:
        load.append(f"    evt.SetSprite({cogs['Cart']}, has(127) and 0 or 1, \"0\")"
                    "   -- Atliwagon.scr :Init: the ship is gone")

    # --- the Gathering's games: tickets and prizes ----------------------------------------------------------------
    lines += [
        "-- THJORGARDGAMESCOMMON.inc: a game takes a ticket (item 557) when it starts; a win (Guberland:",
        "-- HucksterMod.scr \"1\") gives the game's key, key 7116 and a random prize (362-367). MM9's rollover",
        "-- strings are not extracted: the status lines are our own words.",
        "local function ticket()   -- :CheckGameTicket, :TakeGameTicket",
        f"    if {item('has', 557, 'Ticket')} ~= 1 then",
        "        evt.StatusText(\"You need a game ticket. The ticket master sells them.\")",
        "        return false",
        "    end",
        f"    {item('take', 557, 'Ticket')}",
        "    evt.StatusText(\"A game ticket is used.\")",
        "    return true",
        "end",
        "local function gameWon(key)   -- :Record<Game>Win, :CheckGuberlandWins, :GiveGuberlandPrize",
        "    MM9.giveKey(key); MM9.giveKey(7116)",
        f"    MM9.giveItem(MM9.random({PRIZES.start}, {PRIZES.stop - 1}), \"{TAG}:Prize\")",
        "    evt.StatusText(\"You win! Here is your prize.\")",
        "end",
        "local function might()   -- GetAttribute 0: the active character's Might",
        "    evt.ForPlayer(Players.Current)",
        "    local low, high = 0, 1024",
        "    while low < high do",
        "        local mid = math.floor((low + high + 1) / 2)",
        "        if evt.Cmp(VarTag.ActualMight, mid) then low = mid else high = mid - 1 end",
        "    end",
        "    return low",
        "end",
        "-- HucksterMod.scr (the ticket master, RUDE 429) :OnRudeExit: key 1001: one ticket for 5 gold; key 1010:",
        "-- ten for 40 gold; the rule book (item 594) with the first. Without the gold, NoGold.inc.",
        "local function sellTickets(cost, count)   -- :SellGameTicket, :SellBatchTickets",
        "    if MM9.hasGold(cost) ~= 1 then evt.StatusText(\"You don't have enough gold.\"); return end",
        "    evt.PlaySoundName(\"events/gold01.wav\", 0, 0, 0)",
        "    MM9.takeGold(cost)",
        f"    for n = 1, count do {item('give', 557, 'Ticket')} end",
        f"    if {item('has', 594, 'Rulebook')} ~= 1 then {item('give', 594, 'Rulebook')} end",
        "    evt.StatusText(count == 1 and \"You bought a game ticket.\" or \"You bought ten game tickets.\")",
        "end",
        f"handlers[{rude_exit(build, 'TicketMaster')}] = function()",
        "    if has(1001) then MM9.takeKey(1001); sellTickets(5, 1)",
        "    elseif has(1010) then MM9.takeKey(1010); sellTickets(40, 10) end",
        "end",
        "",
        "-- ArmWrestle.scr (Mata Abyomi, RUDE 148) :OnUse (his dialogue opens too: DoRude 1): with a ticket, his",
        "-- might (no ScriptParams: 0) + 1..40 against the character's Might + 9..50; a tie is the party's.",
        "-- A beaten Mata :StartCower: PlayAnim cowerstart, LoopAnim cower 5, PlayAnim cowerstop, his use (the game,",
        f"-- not the dialogue) removed until it ends (:RemoveUse, :RestoreUse: {cower_seconds} s; runtime only).",
        f"local MATA = {mata}",
        "local mataCowers = false",
        f"handlers[{rude_use(build, 'CommonerHalfOrcMaleA0')}] = function()",
        "    if not mataCowers and ticket() then",
        "        local his = MM9.random(1, 40)",
        "        if might() + MM9.random(9, 50) >= his then",
        "            evt.PlayActorClip(MATA, {\"cowerstart\", \"cower\", \"cower\", \"cower\", \"cower\", \"cower\", "
        "\"cowerstop\"}, false)",
        f"            mataCowers = true; evt.StartTimer({T_COWER}, seconds({cower_seconds}))",
        "            gameWon(7115)",
        "        else evt.StatusText(\"You lose.\") end",
        "    end",
        "    MM9.openRude(148)",
        "end",
        f"handlers[{T_COWER}] = function()   -- :FinishCower -> :RestoreUse",
        f"    evt.StopTimer({T_COWER})",
        "    mataCowers = false",
        "end",
        "",
    ]
    registrations += [(rude_exit(build, "TicketMaster"), "Ticket master", None),
                      (rude_use(build, "CommonerHalfOrcMaleA0"), "Mata Abyomi", None),
                      (T_COWER, "Mata's cower", None, "timer")]

    # --- ring the bell ---------------------------------------------------------------------------------------------
    plate_event, plate, _ = door_group(build, "Strikeplate1")
    riser_event, riser, riser_mover = door_group(build, "Riser1")
    if plate_event and riser and riser_mover:
        rise = riser_mover["move_length"] / max(1, riser_mover["open_speed"])
        lines += [
            "-- DingTheBell.scr (Strikeplate1) :HitBell, BellWeight.scr (Riser1, \"360\") :AdjustHeight: with a",
            "-- ticket the plate goes down and the weight rises to 360 LT x timing / ding (timing 40..60 + the",
            "-- character's Might, ding 60..80); :CheckWin: timing > ding rings the bell (the bell's win), else a",
            "-- loss; the plate works again 3 s later, when the weight's close lifts it. Here timer 601 stops the",
            "-- weight at its height, then closes both.",
            f"local BELL_RISE = {rise:.3f}   -- seconds for the weight's full rise (move length / open speed)",
            f"handlers[{plate_event}] = function()   -- Strikeplate1 (replaces its door toggle)",
            "    if var(\"BellPhase\") ~= 0 then return end   -- :BlockUse",
            "    if not ticket() then return end",
            "    local ding = MM9.random(60, 80)",
            "    local timing = MM9.random(40, 60) + might()",
            "    set(\"BellWin\", timing > ding and 1 or 0)",
            "    set(\"BellPhase\", 1)",
            f"    {doors_call(plate, 'Open')} {doors_call(riser, 'Open')}",
            f"    evt.StartTimer({T_BELL}, seconds(BELL_RISE * math.min(1, timing / ding)))",
            "end",
            f"handlers[{T_BELL}] = function()",
            "    local phase = var(\"BellPhase\")",
            "    if phase == 1 then",
            f"        {' '.join(f'evt.StopDoor({d})' for d in riser)}",
            "        if var(\"BellWin\") == 1 then evt.PlaySoundName(\"events/dingbell.wav\", 0, 0, 0); gameWon(7114)",
            "        else evt.StatusText(\"You lose.\") end",
            f"        set(\"BellPhase\", 2); evt.StartTimer({T_BELL}, seconds(3))   -- :AllowUse",
            "    else",
            f"        if phase == 2 then {doors_call(riser, 'Close')} {doors_call(plate, 'Close')} end",
            f"        set(\"BellPhase\", 0); evt.StopTimer({T_BELL})",
            "    end",
            "end",
        ]
        if riser_event:
            lines.append(f"handlers[{riser_event}] = function() end   -- Riser1: only the plate drives the weight")
        lines.append("")
        registrations.append((T_BELL, "Bell", None, "timer"))
        load.append(f"    if var(\"BellPhase\") ~= 0 then set(\"BellPhase\", 0); {doors_call(riser, 'Close')} "
                    f"{doors_call(plate, 'Close')} end")

    # --- the runes ----------------------------------------------------------------------------------------------------
    switch_event, switch, _ = door_group(build, "Switch")
    buttons = [f"ColorButton{k}" for k in range(5)]
    spaces = [f"ColorSpace{k}" for k in range(4)]
    if switch_event and all(n in events for n in buttons) and all(n in events and n in cogs for n in spaces):
        plain = props[spaces[0]]["decoration"]
        paint = ["-- MastermindSpace.scr :ChangeColor (skins\\gibs\\<colour>.dtx)",
                 "local function paintRune(cog, colour)"]
        for k, name in enumerate(buttons):
            paint.append(f"    {'if' if k == 0 else 'elseif'} colour == {k} then "
                         f"evt.SetSprite(cog, 1, \"{props[name]['decoration']}\")")
        paint += [f"    else evt.SetSprite(cog, 1, \"{plain}\") end", "end"]
        lines += [
            "-- The runes. MastermindColor.scr (ColorButton0-4): the current colour. MastermindSpace.scr",
            "-- (ColorSpace0-3): Mastermind.scr :ColorChosen (the game's first choice takes a ticket) and the stone",
            "-- takes the colour (here its decoration swaps to the button's). The Switch's open: :CompareColors: right",
            "-- runes (MM9 lights FireCorrect fires; here a status line names them), 4 chances, all four right: the",
            "-- runes' win; :GenerateColors: four random colours 0..4. RuneChosen<i> holds colour + 1 (0 = none).",
            *paint,
            "local function newRunes()   -- :GenerateColors",
            "    for i = 1, 4 do set(\"RuneCode\" .. i, MM9.random(0, 4)) end",
            "    set(\"RuneChances\", 4); set(\"RuneTicket\", 1)",
            "end",
            "local function runeTicket()   -- bNeedsTicket",
            "    if var(\"RuneTicket\") == 0 then return true end",
            "    if not ticket() then return false end",
            "    set(\"RuneTicket\", 0)",
            "    return true",
            "end",
        ]
        for k, name in enumerate(buttons):
            lines += [f"handlers[{events[name]}] = function()   -- {name}",
                      "    evt.PlaySoundName(\"door/trapdooropen.wav\", 0, 0, 0)",
                      f"    set(\"RuneColour\", {k}); evt.StatusText(\"The {COLOUR_NAMES[k]} rune.\")",
                      "end"]
            registrations.append((events[name], "Rune", "Rune"))
        for k, name in enumerate(spaces):
            lines += [
                f"handlers[{events[name]}] = function()   -- {name} (MastermindSpace.scr :UpdateColor)",
                "    local colour = var(\"RuneColour\")",
                f"    if var(\"RuneChances\") > 0 and runeTicket() then set(\"RuneChosen{k + 1}\", colour + 1) end",
                "    evt.PlaySoundName(\"door/doorlatch01.wav\", 0, 0, 0)",
                f"    paintRune({cogs[name]}, colour)",
                "end",
            ]
            registrations.append((events[name], "Rune stone", "Rune"))
        lines += [
            f"handlers[{switch_event}] = function()   -- Switch (OpenTrigger: Mastermind check; not a door toggle)",
            f"    {doors_call(switch, 'Open')}",
            f"    evt.StartTimer({T_SWITCH}, seconds(1))",
            "    if var(\"RuneChances\") <= 0 or not runeTicket() then return end",
            "    local right = {}",
            "    for i = 1, 4 do",
            "        if var(\"RuneChosen\" .. i) == var(\"RuneCode\" .. i) + 1 then",
            "            right[#right + 1] = tostring(i)",
            "        end",
            "    end",
            "    local chances = var(\"RuneChances\") - 1",
            "    set(\"RuneChances\", chances)",
            "    if #right == 4 then newRunes(); gameWon(7112); return end   -- :Correct (bless.wav is not imported)",
            "    local text = tr(\"No rune is right.\")",
            "    if #right > 0 then text = tr(\"Right: rune {runes}.\", {runes = table.concat(right, \", \")}) end",
            "    if chances == 0 then evt.StatusText(text .. \" \" .. tr(\"You lose.\")); newRunes()   -- :Incorrect",
            "    else",
            "        local left = ({tr(\"1 chance left.\"), tr(\"2 chances left.\"), tr(\"3 chances left.\")})[chances]",
            "        evt.StatusText(text .. \" \" .. left)",
            "    end",
            "end",
            f"handlers[{T_SWITCH}] = function() evt.StopTimer({T_SWITCH}); {doors_call(switch, 'Close')} end",
            "",
        ]
        registrations.append((T_SWITCH, "Rune switch", None, "timer"))
        load += ["    newRunes()   -- Mastermind.scr :InitMastermind",
                 "    for i = 1, 4 do set(\"RuneChosen\" .. i, 0) end"]
        load += [f"    paintRune({cogs[name]}, -1)" for name in spaces]

    lines += ["local function rnd(a, b)   -- MM9's GetRandomInt a, b (the high bits of the event generator)",
              "    return a + math.floor(MM9.random(0, 1073741823) / 65536) % (b - a + 1)",
              "end", ""]
    game_lines, game_registrations, game_load = stones_game(build, events, cogs, actor.get("TronPlayer"))
    lines += game_lines
    registrations += game_registrations
    load += game_load
    game_lines, game_registrations, game_load = whack_a_honky(build, events, cogs)
    lines += game_lines
    registrations += game_registrations
    load += game_load

    # --- the stones player ------------------------------------------------------------------------------------------
    lines += [
        "-- StonesPlayer.scr (TronPlayer) :OnRudeEnter: key 7002, DoRude 428; :OnRudeExit: 7002 taken. Live once",
        "-- the actor carries RUDE 428 (it is placed with none: work/scr_spec.md).",
        f"handlers[{rude_use(build, 'TronPlayer')}] = function() MM9.giveKey(7002); MM9.openRude(428) end",
        f"handlers[{rude_exit(build, 'TronPlayer')}] = function() MM9.takeKey(7002) end",
        "",
    ]
    registrations += [(rude_use(build, "TronPlayer"), "Stones player", None),
                      (rude_exit(build, "TronPlayer"), "Stones player", None)]

    # --- Nicolai, Alvar ---------------------------------------------------------------------------------------------
    if "AlvartheClumsy" in actor:
        lines += [
            "-- Retainer.scr (Alvar the Clumsy, RUDE 178, key 458): gone while hired (also once his dialogue hires",
            "-- him).",
            f"handlers[{rude_exit(build, 'AlvartheClumsy')}] = function()",
            f"    show({actor['AlvartheClumsy']}, not has(458))",
            "end",
            "",
        ]
        registrations.append((rude_exit(build, "AlvartheClumsy"), "Alvar the Clumsy", None))
        load.append(f"    show({actor['AlvartheClumsy']}, not has(458))   -- Retainer.scr :Init")
    if "Niclolai" in actor:
        load.append(f"    show({actor['Niclolai']}, has(121))   -- NPC414.scr :Init: here once he has the circus job")

    # --- Scandlan and Broccan's new-game talk ---------------------------------------------------------------------
    if "Scandlan" in actor and "Broccan" in actor:
        lines += talk_start_lua(found_player(build, "Scandlan"))
        registrations.append((found_player(build, "Scandlan"), "Scandlan", None))
        # the scenes' block at the end of the file; convert.py installs hooks.scenes as guberland.cinematics.yml
        hooks.scenes = scenes(actor, native(build, "Broccan"), native(build, "CommonerHalfOrcMaleA0"))
        script.hooks.append(cutscenes.lua_block(hooks.scenes))

    lines += ["-- Visibility and the games on every load (the scripts' :Init).",
              "handlers.regionLoad = function()"] + load + ["end", ""]
    script.add(lines, *registrations)


# --- the stones game and whack-a-honky (Thjorgard's, mm9r_thjorgard_blv/regionlua.py) -------------------------------
def stones_game(build, events: dict, cogs: dict, bot=None) -> tuple[list, list, list]:
    """StonesGame.scr \"Square 6\" (TronMgr), StonesSquare.scr, StonesPiece.scr, StonesPlayer.scr's moves: the
    handlers (ticket(), gameWon() and rnd() come first), their registrations and the load's lines. `bot`: TronPlayer's
    map actor (None when not placed: he always answers)."""
    if not all(name in cogs and name in events for name in PIECES):
        return [], [], []
    piece_cogs = ", ".join(str(cogs[name]) for name in PIECES)
    lines = [
        "-- StonesGame.scr \"Square 6\" (TronMgr), StonesSquare.scr (Square0-35), StonesPiece.scr (Piece0-35),",
        "-- StonesPlayer.scr (TronPlayer, the bot). A 6 x 6 board, map vars St0-St35: 0 empty, 1 white (the party),",
        "-- 2 black (the bot). A move goes on an empty square next to (8 ways) a stone of the mover's colour; after",
        "-- each move, the side to move without a legal square loses (MM9's scan skips the last square). The first",
        f"-- move of a game takes a ticket; a win is key {KEY_STONES_WIN}. The board is set again on every load.",
        f"local ST_COGS = {{{piece_cogs}}}",
        "local ST_OFFSETS = {-5, 1, 7, -6, 6, -7, -1, 5}   -- :SetupCheck (BOARDSIZE 6); 1-3 right, 6-8 left",
        "local function stDraw(i, colour)   -- StonesPiece.scr :TurnWhite / :TurnBlack; empty keeps a grey stone",
        "    local key = ST_COGS[i + 1]",
        f"    if colour == 1 then evt.SetSprite(key, 1, \"{STONE_WHITE}\")",
        f"    elseif colour == 2 then evt.SetSprite(key, 1, \"{STONE_BLACK}\")",
        f"    else evt.SetSprite(key, 1, \"{STONE_EMPTY}\") end",
        "end",
        "local function stSet(i, colour) set(\"St\" .. i, colour); stDraw(i, colour) end",
        "local function stLegal(i, colour)   -- :CheckSurrounding",
        "    if var(\"St\" .. i) ~= 0 then return false end",
        "    for n, offset in ipairs(ST_OFFSETS) do",
        "        local j = i + offset",
        "        local edge = ((i + 1) % 6 == 0 and n <= 3) or (i % 6 == 0 and n >= 6) or j < 0 or j > 35",
        "        if not edge and var(\"St\" .. j) == colour then return true end",
        "    end",
        "    return false",
        "end",
        "local function stCanMove(colour)   -- :CheckVictory (while nCurSquare < LISTLAST: squares 0-34)",
        "    for i = 0, 34 do if stLegal(i, colour) then return true end end",
        "    return false",
        "end",
        "local function stReset()   -- :ResetVars, :ResetBoard: one white and the mirrored black at random",
        "    for i = 0, 35 do stSet(i, 0) end",
        "    local r = rnd(0, 35)",
        "    stSet(r, 1); stSet(35 - r, 2); set(\"StTicket\", 0); set(\"StTurn\", 0)",
        "end",
        "-- A slain stones player (TronPlayer) takes no \"play\" (MM9.receives): the board waits on black, and the",
        "-- party's next click places black (:CheckMove alternates the colours whoever clicks). Map var StTurn 2.",
        f"local ST_BOT = {'nil' if bot is None else bot}",
        "local function stMove(i)   -- StonesSquare.scr :RequestMove -> StonesGame.scr :CheckMove",
        "    if var(\"StTicket\") == 0 then",
        "        if not ticket() then return end",
        "        set(\"StTicket\", 1)",
        "    end",
        "    if var(\"StTurn\") == 2 then   -- black's turn (:HandleInvalidMove sends the dead bot \"play\": nothing)",
        "        if not stLegal(i, 2) then return end",
        "        stSet(i, 2); set(\"StTurn\", 0)",
        f"        if not stCanMove(1) then evt.StatusText({lua_string(TEXT[231])}); stReset(); return end",
        f"        evt.StatusText({lua_string(TEXT[244])})",
        "        return",
        "    end",
        f"    if not stLegal(i, 1) then evt.StatusText({lua_string(TEXT[233])}); return end   -- :HandleInvalidMove",
        "    stSet(i, 1)",
        f"    if not stCanMove(2) then evt.StatusText({lua_string(TEXT[230])}); gameWon({KEY_STONES_WIN}); stReset(); "
        "return end",
        "    if not MM9.receives(\"guberland\", \"TronPlayer\", \"play\", ST_BOT) then set(\"StTurn\", 2); return end",
        "    local legal = {}   -- StonesPlayer.scr :PlacePiece: random squares until a legal one",
        "    for j = 0, 35 do if stLegal(j, 2) then legal[#legal + 1] = j end end",
        "    stSet(legal[rnd(1, #legal)], 2)",
        f"    if not stCanMove(1) then evt.StatusText({lua_string(TEXT[231])}); stReset(); return end",
        f"    evt.StatusText({lua_string(TEXT[244])})",
        "end",
    ]
    registrations = []
    for k, name in enumerate(PIECES):
        lines.append(f"handlers[{events[name]}] = function() stMove({k}) end   -- {name} (Square{k})")
        registrations.append((events[name], "Stone", "Stone"))
    lines.append("")
    return lines, registrations, ["    stReset()   -- StonesGame.scr :InitStonesGame"]


def whack_a_honky(build, events: dict, cogs: dict) -> tuple[list, list, list]:
    """Whack-a-Honky.scr \"<k> Honky 0 3\" (Honky0-3) and Switch0 (its start lever, a `rotate` mover): the handlers,
    their registrations and the load's lines."""
    honk_event, lever, _ = door_group(build, "Switch0")
    if not (all(name in events and name in cogs for name in HONKIES) and honk_event):
        return [], [], []
    lines = [
        "-- Whack-a-Honky.scr \"<k> Honky 0 3\" (Honky0-3) and Switch0 (OpenTrigger0 Honky0 \"start\"). A pull with a",
        "-- ticket: Countdown5, then ten seconds (Wait 19, 15 EndGame from the pull) of geese, one up at a time: it",
        "-- rises (0.2 s), waits 0.5-1 s, goes down (0.2 s) and another rises (:OnFinishedLower, never the same one); a",
        "-- click on the raised goose counts (WHACK_COUNTER) and sends it down at once. Eight win (WIN_CONDITION):",
        f"-- key {KEY_HONKY_WIN}. MM9 raises the geese 20 units from their holes; here the idle geese all stand, and while",
        "-- the game runs only the raised one shows. Map vars: HonkState (0 idle, 1 countdown, 2 playing), HonkStep,",
        "-- HonkUp (1-4, 0 none), HonkLast, HonkHits.",
        f"local HONK_COGS = {{{', '.join(str(cogs[name]) for name in HONKIES)}}}",
        f"local HONK_COUNT = {{{', '.join(lua_string(TEXT[n]) for n in range(235, 240))}}}",
        "local function honkShowAll(on) for i = 1, 4 do evt.SetSprite(HONK_COGS[i], on and 1 or 0, \"0\") end end",
        "local function honkRaise()   -- :ReceivePopup",
        "    local k = rnd(1, 4)",
        "    while k == var(\"HonkLast\") do k = rnd(1, 4) end",
        "    set(\"HonkUp\", k); set(\"HonkLast\", k); evt.SetSprite(HONK_COGS[k], 1, \"0\")",
        f"    evt.StartTimer({T_HONK}, seconds((200 + rnd(500, 1000)) / 1000))",
        "end",
        "local function honkLower()   -- :SendPopup",
        "    local k = var(\"HonkUp\")",
        "    if k > 0 then evt.SetSprite(HONK_COGS[k], 0, \"0\") end",
        f"    set(\"HonkUp\", 0); evt.StartTimer({T_HONK}, seconds(0.2))",
        "end",
        "local function honkReset()",
        f"    evt.StopTimer({T_HONK}); evt.StopTimer({T_HONK_END})",
        "    set(\"HonkState\", 0); set(\"HonkUp\", 0); honkShowAll(true)",
        f"    {doors_call(lever, 'Close')}",
        "end",
        f"handlers[{honk_event}] = function()   -- Switch0 -> Honky0 :StartGame (replaces its door toggle)",
        "    if var(\"HonkState\") ~= 0 or not ticket() then return end",
        f"    {doors_call(lever, 'Open')}",
        "    set(\"HonkState\", 1); set(\"HonkStep\", 1); set(\"HonkHits\", 0); set(\"HonkLast\", 0)",
        f"    evt.StatusText(HONK_COUNT[1]); evt.StartTimer({T_HONK}, seconds(1))",
        f"    evt.StartTimer({T_HONK_END}, seconds(15))",
        "end",
        f"handlers[{T_HONK}] = function()",
        "    local state = var(\"HonkState\")",
        "    if state == 1 then",
        "        local step = var(\"HonkStep\")",
        "        if step < 5 then set(\"HonkStep\", step + 1); evt.StatusText(HONK_COUNT[step + 1]); "
        f"evt.StartTimer({T_HONK}, seconds(1))",
        "        else set(\"HonkState\", 2); honkShowAll(false); honkRaise() end",
        "    elseif state == 2 then",
        "        if var(\"HonkUp\") > 0 then honkLower() else honkRaise() end",
        "    end",
        "end",
        f"handlers[{T_HONK_END}] = function()   -- :EndGame",
        "    if var(\"HonkState\") ~= 2 then return end",
        "    local hits = var(\"HonkHits\")",
        "    honkReset()",
        f"    if hits >= {HONK_WIN} then gameWon({KEY_HONKY_WIN}) else evt.StatusText(\"You lose.\") end",
        "end",
    ]
    registrations = []
    for k, name in enumerate(HONKIES):
        lines += [
            f"handlers[{events[name]}] = function()   -- {name} :OnDamage",
            f"    if var(\"HonkState\") ~= 2 or var(\"HonkUp\") ~= {k + 1} then return end",
            "    set(\"HonkHits\", var(\"HonkHits\") + 1)",
            "    evt.PlaySoundName(\"ambient/animals/goose honk.wav\", 0, 0, 0)   -- MM9: animsounds\\hen\\fidget01",
            "    honkLower()",
            "end",
        ]
        registrations.append((events[name], "Goose", "Goose"))
    lines.append("")
    registrations += [(honk_event, "Whack-a-honky lever", "Lever"), (T_HONK, "Whack-a-honky", None, "timer"),
                      (T_HONK_END, "Whack-a-honky end", None, "timer")]
    return lines, registrations, ["    honkReset()   -- Whack-a-Honky.scr :Main, :ResetPOS"]


# --- the cutscene ---------------------------------------------------------------------------------------------------
def scenes(actors: dict, broccan_point, mata_point) -> list:
    """The map's cutscenes (cutscenes.Scene) from the built actors (DAT name -> actor index: hooks.npc_actor, or the
    installed scene's actors by their DAT index) and the native floor points of Broccan and Mata (CommonerHalfOrcMaleA0,
    Broccan's WalkTo target): the converter's Lua and install and cinematics_pilot.py use these."""
    return [newgame_talk_scene(actors["Scandlan"], actors["Broccan"], broccan_point, mata_point)]


def talk_start_lua(event: int) -> list[str]:
    """Scandlan's FoundPlayer handler (event 56000 + his DAT index): it starts the talk."""
    return [
        "-- NPC150.scr :Init OnFoundPlayer :OnStart: the first time Scandlan perceives the party (without key "
        f"{TALK_KEY}) he",
        f"-- and Broccan (NPC151.scr) talk, the cinematic {NEWGAME_TALK} (its steps at the end of this file).",
        f"handlers[{event}] = function()",
        f"    if not has({TALK_KEY}) then MM9Cinematic.start(\"{NEWGAME_TALK}\") end",
        "end",
        "",
    ]


def voice_seconds(name: str) -> float:
    """A cinema voice's length (mm9/extracted/VOICES/VOICES/CINEMA/<folder>/<file>.wav; cutscenes.wav_seconds only
    searches SOUNDS)."""
    folder, file = name.split("\\")[-2:]
    path = cutscenes.ROOT / "mm9/extracted/VOICES/VOICES/CINEMA" / folder.upper() / file.upper().replace(".WAV", ".wav")
    with wave.open(str(path)) as stream:
        return stream.getnframes() / float(stream.getframerate())


# NPC150.scr (Scandlan) and NPC151.scr (Broccan) from Scandlan's :OnStart: (speaker, Loopanim clip, the fixed wait
# before the other's Speak<n>); line n is voices\cinema\NewGame\<n>.wav
TALK_LINES = (("Scandlan", "conv2", 6.5), ("Broccan", "conv1", 0.5), ("Scandlan", "conv2", 13.3),
              ("Broccan", "conv1", 0.5), ("Scandlan", "conv5", 18.5), ("Broccan", "conv1", 1.0),
              ("Scandlan", "conv4", 7.0), ("Broccan", "conv1", 0.5), ("Scandlan", "conv5", 12.5),
              ("Broccan", "conv1", 1.0), ("Scandlan", "conv5", 8.5))


def newgame_talk_scene(scandlan: int, broccan: int, broccan_point, mata_point) -> cutscenes.Scene:
    """NPC150.scr :OnStart..:OnSpeak12 and NPC151.scr: Scandlan targets Broccan (who targets him back, :OnTarget), key
    5020; each line a Loopanim and its wav, then a fixed wait (not the wav's length) before the other's Speak<n>:
    Scandlan 01 (6.5 s), Broccan 02 (0.5), 03 (13.3), 04 (0.5), 05 (18.5), 06 (1), 07 (7), 08 (0.5), 09 (12.5), 10 (1),
    Scandlan 11 (8.5); then :Trigger12 (69.8 s) sends Broccan Speak12 (:OnWalkAway: WalkTo Mata, then BaseWander) and
    a second later Scandlan says 12 (7.9 s). Neither OnStop resets the animation (Stop halts movement only; NPC150's
    Loopanim stand is commented out), so each keeps looping his last conv clip; Broccan's ends with his walk, the
    step `walk_away` (evt.ClearActorPresentation, evt.MoveActorTo). No camera: an ambient cinematic (overheard talk:
    no shots, letterbox or input lock; the party walks on). The lines have no text in MM9's data, so no subtitles."""
    scene = cutscenes.Scene(NEWGAME_TALK, EV_NEWGAME_TALK, source="NPC150.scr :OnStart..:OnSpeak12, NPC151.scr",
                            ambient=True)
    cinema = scene.cinema
    who = {"Scandlan": scandlan, "Broccan": broccan}
    scene.step(0.0, "key", f"MM9.giveKey({TALK_KEY})", note=f":OnStart givekey {TALK_KEY}")
    cinema._cue(0.0, "Scandlan targets Broccan", actor=scandlan, action="face", look_at_actor=broccan, seconds=0.3)
    cinema._cue(0.0, "Broccan targets Scandlan (:OnTarget)", actor=broccan, action="face", look_at_actor=scandlan,
                seconds=0.3)

    def line(at: float, name: str, clip: str, number: int) -> None:
        voice = f"voices\\cinema\\newgame\\{number:02d}.wav"
        cinema._cue(at, f"{name}: Loopanim {clip}", actor=who[name], action="clip", clip=clip, loop=True)
        cinema.sound(at, voice, note=f"{name} {number:02d}.wav ({voice_seconds(voice):.2f} s)")

    # MM9's lifecycle (scr_audit README "Implicit engine semantics"): each line from 2 on is a Speak<n> message to its
    # speaker, and his script sends the next one; a slain speaker takes none, so the talk ends there (the earlier
    # speaker's own wait still sent it). A step just before each such line asks MM9.receives; a dropped one ends the
    # cinematic (evt.SkipCinematic: no more lines) and marks it broken for the steps the skip still runs.
    broken = f'evt.GetMapVar("{TALK_BROKEN}", 0) == 0'
    at = 0.0
    for number, (name, clip, wait) in enumerate(TALK_LINES, 1):
        if number > 1:
            scene.step(at - 0.05, f"hears{number:02d}",
                       f'if {broken} and not MM9.receives("guberland", "{name}", "Speak{number}", {who[name]}) then\n'
                       f'    evt.SetMapVar("{TALK_BROKEN}", 1)\n    evt.SkipCinematic()\nend',
                       note=f"{name} takes Speak{number} only alive")
        line(at, name, clip, number)
        at += wait
    # :Trigger12: Broccan's :OnWalkAway walks him to Mata (the arm wrestler), stopping short of him
    bx, by = broccan_point[0], broccan_point[1]
    mx, my, mz = mata_point
    length = max(1.0, math.hypot(mx - bx, my - by))
    tx = round(mx - (mx - bx) / length * BROCCAN_STOP)
    ty = round(my - (my - by) / length * BROCCAN_STOP)
    # Scandlan's own wait says 12 even if Broccan was slain after 10; a slain Broccan takes no Speak12 (no walk)
    scene.step(at, "walk_away", f'if {broken} and MM9.receives("guberland", "Broccan", "Speak12", {broccan}) then\n'
               f"    evt.ClearActorPresentation({broccan})\n    evt.MoveActorTo({broccan}, {tx}, {ty}, {mz})\nend",
               note=":Trigger12 Speak12: Broccan's :OnWalkAway (WalkTo CommonerHalfOrcMaleA0)")
    line(at + 1.0, "Scandlan", "conv5", 12)
    return scene
