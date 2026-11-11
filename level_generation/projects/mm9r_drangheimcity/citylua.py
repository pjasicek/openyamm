"""
Drangheim City's map Lua: the doors (MM9's locked doors say so), and the scripted objects as native handlers, each citing
its .scr (README.md, "Scripted objects"; the behaviour spec of every script is work/scr_spec.md).

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h; such a handler ends with MM9.openRude).
"""

from __future__ import annotations

import csv
import json
import math
import wave

import cutscenes
from dungeon import lua
from dungeon import town_portal
from dungeon.source import ROOT
from quest_xp import balanced_experience, experience_note

LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
EV_LOAD, EV_LOCKED = 1, 230
T_POLL = 260
EV_SCRIPTED_PROP = 330              # letters, the book, the town portal altar: EV_SCRIPTED_PROP + k
KILL_HOOK = 97                      # Guaire A'Velsi's death (NPC95.scr :OnDeath)
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr", "townportal.scr")
LOCATION_KEY = 1027                 # ForadWorld.scr "Drangheim" (keys 1024-1033 are the towns')
TOWN_PORTAL_KEY = 5013              # TownPortal.scr "Drangheim"
BANK_KEY, BANK_ORB_KEY = 334, 325   # BankOrb.scr, RUDE 100: the orb placed in Drangheim (nKey 334, nKey2 325)
HROLF_SEEN_KEY = 5010               # NPC110.scr: Hrolf and Alfrigg's quarrel has been seen
# NPC110.scr / NPC109.scr's quarrel as the cinematic dwarves_and_humans (no cameras): its done event, steps 36001..
QUARREL = "dwarves_and_humans"
EV_QUARREL = 36000
EV_FIGHT_OVER = 36020               # the kill hook that ends their fight (:OnTargetDead)
FIGHT_RELATION = 1                  # evt.SetMonsterRelation: close range (they stand 92 units apart)

# MM9 doors with Locked 1 and no key, script or trigger that unlocks them: a click says the door is locked (MM9
# jiggles it). Klusos House's door (AlchemistDoor*) is one of them: its exit volume in front of it takes the party in.
LOCKED_GROUPS = ["SmithShackDoor", "StairDoor", "RotatingDoor1", "AlchemistDoorLeft", "HouseDoor1"]
# Movers that are no doorway of the converter's but open on a click: the town hall's double door (its portal is a
# rect portal, overrides.yml).
TOGGLE_GROUPS = {"TownHallDoorLeft": 240}
MOVER_EVENTS = {**{group: (EV_LOCKED, "click") for group in LOCKED_GROUPS},
                **{group: (event, "click") for group, event in TOGGLE_GROUPS.items()}}
MARKERS = ("HrolfMarker",)


def rude_exit_event(index: int) -> int:
    return 50000 + index


def rude_use_event(index: int) -> int:
    return 53000 + index


def found_player_event(index: int) -> int:
    return 56000 + index


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


def scripted_props(build) -> list:
    """props.json's scripted props, in file order: [(name, entry)]."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    return [(e["source_name"], e) for e in entries
            if e["kind"] == "prop" and str(e.get("script") or "").lower().replace("scripts\\", "")
            in SCRIPTED_PROP_SCRIPTS]


def prop_events(build) -> dict:
    """DAT prop name -> click event: the scripted props."""
    return {name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted_props(build))}


def prop_cogs(build) -> dict:
    return {}


def marker_points(build) -> dict:
    """The MM9 markers the scripts move NPCs to, as native points on the floor under them."""
    points = {}
    for name in MARKERS:
        found = build.source.by_name.get(name.lower())
        if found is None:
            continue
        p = found["properties"]["Pos"]
        floor = build.content.floor_at(p[0], p[2], p[1] + 16)
        if floor is None:
            continue
        points[name] = build.project.native([p[0], floor, p[2]]).round().astype(int).tolist()
    return points


def promotion(lines: list, title: str, done: int, needed: int, xp: int, gold: int, promo: str, keys: tuple) -> None:
    # every eligible member at once (MM9.promoteParty: the quest -> class-line table); MM9's per-character keys
    # (`keys`) are not used (devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And Classes")
    lines += [f"    if not has({done}) and has({needed}) then",
              f"        reward({done}, {balanced_experience(xp, done)}, {gold}){experience_note(xp, done)}",
              f"        MM9.promoteParty(\"{promo}\")",
              "    end"]


def map_script(hooks, build) -> str:
    script = lua.Script(build, "Drangheim City")
    script.doors()
    script.chests()
    a, o, points = hooks.actor, hooks.objects, hooks.points
    scripted = scripted_props(build)
    lines = [
        "local function has(k) return MM9.hasKey(k) == 1 end",
        "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; "
        "if gold > 0 then MM9.giveGold(gold) end; quest() end",
        "",
        "-- MM9's locked doors (Locked 1, no key): the smith's shack, the stair door, the tavern's back door, a house and",
        "-- Klusos House's front door (its exit volume in front of the door takes the party in).",
        f"handlers[{EV_LOCKED}] = function()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        "",
        f"-- ForadWorld.scr (ScriptObject0, \"Drangheim\"): key {LOCATION_KEY} is the party's location while here (keys",
        "-- 1024-1033 are the towns'); key 5017 closes the shops from 20:00 to 06:00 (MM9 dialogues forbid or require it).",
        "local function shopHours()",
        "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
        "    local closed = hour >= 20 or hour < 6",
        "    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end",
        "end",
        "",
    ]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"))
    toggles = ["-- The town hall's double door: a click opens or shuts both leaves."]
    for group, event in TOGGLE_GROUPS.items():
        leaves = [m["node"][5:] for m in build.movers if m["group"] == group]
        calls = " ".join(f"evt.SetDoorState(DOORS[\"{leaf}\"], DoorAction.Trigger)" for leaf in leaves)
        toggles.append(f"handlers[{event}] = function() {calls} end   -- {group}")
    script.add(toggles + [""], *[(event, group, "Door") for group, event in TOGGLE_GROUPS.items()])

    banker, sigmund = "ShopkeeperHumanFemaleA4", "SigmundtheStressed0"
    lines = [
        f"-- BankOrb.scr (Ingimar's bank, RUDE 100): the Orb of Linking. A click with the orb (item 252) after the quest",
        f"-- (key 322) unlocks the row that installs it (key 330); the exit places it (key {BANK_KEY} -> {BANK_ORB_KEY}) and",
        "-- the sixth bank's orb pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).",
        f"handlers[{rude_use_event(o[banker])}] = function()",
        f"    if not has({BANK_ORB_KEY}) and has(322) and MM9.hasItem(252, \"drangheimcity:Banker\") == 1 then "
        "MM9.giveKey(330) end",
        "    MM9.openRude(100)",
        "end",
        f"handlers[{rude_exit_event(o[banker])}] = function()",
        "    if not has(330) then return end",
        "    MM9.takeKey(330)",
        f"    if not has({BANK_KEY}) then return end",
        f"    quest(); MM9.takeItem(252, \"drangheimcity:Banker\"); MM9.giveKey({BANK_ORB_KEY})",
        "    if has(337) then return end",
        "    for k = 331, 336 do if not has(k) then return end end",
        f"    reward(337, {balanced_experience(20000, 337)}, 15000){experience_note(20000, 337)}",
        "end",
        "",
        "-- NPC87.scr (Sigmund the Stressed, Jarl of Drangheim, RUDE 87). The click (OnUse -> United.inc OnCheck): the",
        "-- other five clans' keys (82 Kira, 38 Bjarni, 34 Sven, 63 Markel, 74 Tryygva) give key 178. The exit: key 44",
        "-- gives item 596 (key 489); the gossip (55: 300, 5 000 experience, 5 000 gold); Fort Stenig (49: 171, 32 000,",
        "-- 7 000); Crona Kiga (50: 170, 52 000, 10 000, item 390 taken); the clans united (83: 179, 26 500, 6 000).",
        f"handlers[{rude_use_event(o[sigmund])}] = function()",
        "    if not has(178) and has(82) and has(38) and has(34) and has(63) and has(74) then MM9.giveKey(178) end",
        "    MM9.openRude(87)",
        "end",
        "-- Deviation (the user, 2026-11-08): a party that took the Crona Kiga before the task (the pedestal's key 169)",
        "-- and shows it after \"We've already retrieved that.\" (key 46) has done the task: key 50, which MM9's rows never",
        "-- grant on that path, so Drangheim's pledge (49 and 50) stayed out of reach. Before the rewards below.",
        f"handlers[{rude_exit_event(o[sigmund])}] = function()",
        "    if not has(50) and has(169) and has(46) and MM9.hasItem(390, \"drangheimcity:Sigmund\") == 1 then "
        "MM9.giveKey(50) end",
        "    if not has(489) and has(44) then MM9.giveItem(596, \"drangheimcity:Sigmund\"); MM9.giveKey(489) end",
        f"    if not has(300) and has(55) then reward(300, {balanced_experience(5000, 300)}, 5000) end",
        f"    if not has(171) and has(49) then reward(171, {balanced_experience(32000, 171)}, 7000) end"
        f"{experience_note(32000, 171)}",
        f"    if not has(170) and has(50) then reward(170, {balanced_experience(52000, 170)}, 10000); "
        f"MM9.takeItem(390, \"drangheimcity:Sigmund\") end{experience_note(52000, 170)}",
        f"    if not has(179) and has(83) then reward(179, {balanced_experience(26500, 179)}, 6000) end"
        f"{experience_note(26500, 179)}",
        "end",
        "",
        "-- NPC88.scr (Atli the Quick, RUDE 88): the Assassin's trial done (key 226): key 227, 63 000 experience,",
        "-- 5 000 gold, every character holding key 405-408 promoted to Assassin.",
        f"handlers[{rude_exit_event(o['CommonerElfMaleA0'])}] = function()",
    ]
    promotion(lines, "Atli", 227, 226, 63000, 5000, "Assassin", (405, 406, 407, 408))
    lines += [
        "end",
        "",
        "-- NPC89.scr (Keith Bloodaxe, RUDE 89): Atli taken where he goes (key 136): key 137, 24 500 experience,",
        "-- 5 000 gold, every character holding key 413-416 promoted to Crusader.",
        f"handlers[{rude_exit_event(o['CommonerHuman2MaleA0'])}] = function()",
    ]
    promotion(lines, "Keith", 137, 136, 24500, 5000, "Crusader", (413, 414, 415, 416))
    lines += [
        "end",
        "",
        "-- NPC95.scr (Guaire A'Velsi, a Bandit, RUDE 95): Atli's assassination target. Shown (300 hit points) once Atli",
        "-- gave the task (key 222); his death gives key 225 and he is gone for good.",
        f"local BANDIT = {a['CommonerElfMaleA1']}",
        f"handlers[{KILL_HOOK}] = function(context)",
        "    if context.actorIndex == BANDIT and not has(225) then MM9.giveKey(225) end",
        "end",
        "",
        "-- NPC378.scr (Thorolf Ratatoskssen, two copies, RUDE 378): the messenger. Talking to one removes the other; after",
        "-- the message (key 84) or the summons (key 107) he vanishes by town portal; with 83 or 106 alone the dialogue",
        "-- reopens (it cannot be skipped).",
    ]
    for name, twin in (("Thorolf0", "Thorolf1"), ("Thorolf1", "Thorolf0")):
        lines += [f"handlers[{rude_use_event(o[name])}] = function() MM9.removeActor({a[twin]}); MM9.openRude(378) end",
                  f"handlers[{rude_exit_event(o[name])}] = function()",
                  # :Vanish: DoClientFX g_hmyObject, Ceffect ("spell-town portal")
                  f"    if has(107) or has(84) then MM9.clientFx({a[name]}, \"mm9:town_portal\"); "
                  f"MM9.removeActor({a[name]}); MM9.removeActor({a[twin]})",
                  "    elseif has(106) or has(83) then MM9.openRude(378) end",
                  "end"]
    # NPC378.scr :OnFound: he runs to the party and talks (dungeon/lua.py thorolf_approaches)
    lua.thorolf_approaches(script, a, ("Thorolf0", "Thorolf1"))
    hx, hy, hz = points["HrolfMarker"]
    lines += [""] + hrolf_lua(a["Hrolf"], (hx, hy, hz), found_player_event(o["Hrolf"]))
    script.add(lines,
               (rude_use_event(o[banker]), "Ingimar's bank", None), (rude_exit_event(o[banker]), "Bank", None),
               (rude_use_event(o[sigmund]), "Sigmund", None), (rude_exit_event(o[sigmund]), "Sigmund", None),
               (rude_exit_event(o["CommonerElfMaleA0"]), "Atli", None),
               (rude_exit_event(o["CommonerHuman2MaleA0"]), "Keith Bloodaxe", None),
               (found_player_event(o["Hrolf"]), "Hrolf", None),
               *[(f(o[n]), "Thorolf", None) for n in ("Thorolf0", "Thorolf1") for f in (rude_use_event, rude_exit_event)])
    script.hooks.append(f'RegisterMonsterKilledHook({KILL_HOOK}, "Guaire killed", handlers[{KILL_HOOK}])')

    # --- scripted props --------------------------------------------------------------------------------------------
    lines = ["-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr's book (no text in MM9), TownPortal.scr."]
    altar_load = []          # TownPortal.scr :Init (the map load shows the clean altar)
    for k, (name, entry) in enumerate(scripted):
        event = EV_SCRIPTED_PROP + k
        kind = str(entry.get("script")).lower()
        if "bookletter" in kind:
            number = int(str(entry["script_params"]).split()[0])
            title, text = letter(number)
            lines.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0); "
                         f"evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end   -- {name} ({number})")
            script.registrations.append((event, name, "Read", "event"))
        elif "townportal" in kind:
            lines += town_portal.handler(name, entry, event)
            altar_load = [town_portal.on_load()]
            script.registrations.append((event, name, "Altar", "event"))
        else:
            lines.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0) end"
                         f"   -- {name} (Book.scr: pages turn, no text)")
            script.registrations.append((event, name, "Book", "event"))
    script.add(lines + [""])

    # --- map load and the poll -------------------------------------------------------------------------------------
    # NPC87.scr :Vanish with bVanish FALSE (key 108, he is back): LoopAnim Sit, facing as placed (the fire). MM9 places
    # no chair or seat brush there (DAT objects and polygons within 250 LT: the fireplace, a bed, the town portal): he
    # sits on air in MM9 too.
    record = hooks.records[a[sigmund]]
    yaw = math.radians(record["initial_yaw_units"] * 360.0 / 2048.0)
    sx, sy = record["position"]["x"], record["position"]["y"]
    facing = (int(round(sx + 256 * math.cos(yaw))), int(round(sy + 256 * math.sin(yaw))))
    lines = [
        "-- NPC87.scr :Init -> :Vanish: with key 108 Sigmund is back and loops Sit (LoopAnim Sit 0 DoNothing), facing as",
        "-- placed (the fire; MM9 places no chair there); the load and the poll (the key given while here) seat him.",
        "local sigmundSeated = false",
        "local function sigmundSits()",
        "    if sigmundSeated or not has(108) then return end",
        "    sigmundSeated = true",
        f"    evt.PlayActorClip({a[sigmund]}, \"sit\", true); evt.FaceActorTo({a[sigmund]}, {facing[0]}, {facing[1]}, 0)",
        "end",
        "",
    ]
    script.add(lines)
    load = [
        "    -- NPC87.scr :Init: Sigmund is away while key 40 is set, back with 108",
        f"    show({a[sigmund]}, not (has(40) and not has(108)))",
        "    sigmundSits()",
        "    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)",
        f"    show({a['Thorolf0']}, thorolf); show({a['Thorolf1']}, thorolf)",
        f"    show({a['ShopkeeperHumanFemaleA8']}, not has(456))   -- Retainer.scr: Edina A'Mor, hidden while hired",
        f"    show({a['ShopkeeperHumanFemaleA9']}, not has(455))   -- Retainer.scr: Beagan A'Ghrie, hidden while hired",
        f"    show({a['Niclolai']}, not has(121))   -- NPC414.scr: Nicolai Ironfist moves to Guberland on key 121",
        "    -- NPC95.scr :Init: Guaire A'Velsi is here once Atli gave his task (222), gone once he is dead (225)",
        "    if has(225) then MM9.removeActor(BANDIT) else show(BANDIT, has(222)) end",
        f"    if has({HROLF_SEEN_KEY}) then hrolfAway() end   -- NPC110.scr :Init",
    ]
    load += altar_load
    lines = [
        "local function poll()",
        "    shopHours()",
        "    sigmundSits()",
        "    if not has(225) and has(222) and var(\"BanditShown\") == 0 then set(\"BanditShown\", 1); show(BANDIT, true) end",
        f"    evt.StartTimer({T_POLL}, seconds(1))",
        "end",
        f"handlers[{T_POLL}] = poll",
        f"handlers[{EV_LOAD}] = function()   -- map load",
        f"    for k = 1024, 1033 do if k ~= {LOCATION_KEY} and has(k) then MM9.takeKey(k) end end",
        f"    MM9.giveKey({LOCATION_KEY})",
        *load,
        "    poll()",
        "end",
    ]
    script.add(lines, (T_POLL, "Poll", None, "timer"), (EV_LOAD, "Map load", None))
    monsters = {name: hooks.records[a[name]]["monster_id"] for name in ("Hrolf", "Alfrigg")}
    return script.finish(on_load=[EV_LOAD]) + cutscenes.lua_block(scenes(a, monsters)) + fight_over_lua(a, monsters)


# --- the cutscene ---------------------------------------------------------------------------------------------------
def scenes(actors: dict, monsters: dict) -> list:
    """The map's cutscenes (cutscenes.Scene) from the built actors (DAT name -> actor index: hooks.actor, or
    work/build_report.json's scripted actors) and their monster rows: the converter's Lua and install and
    cinematics_pilot.py use these."""
    return [quarrel_scene(actors["Hrolf"], actors["Alfrigg"], monsters["Hrolf"], monsters["Alfrigg"])]


def hrolf_lua(hrolf: int, marker, event: int) -> list[str]:
    """Hrolf at his marker (NPC110.scr :Init with key 5010) and his FoundPlayer handler (event 56000 + his DAT
    index), which starts the quarrel."""
    hx, hy, hz = marker
    return [
        "-- NPC110.scr / NPC109.scr (Hrolf Anfarssen and Alfrigg Hafnarssen): the first time Hrolf sees the party",
        f"-- (OnFoundPlayer :OnStart, without key {HROLF_SEEN_KEY}) they quarrel, the cinematic {QUARREL}, and",
        "-- fight (its steps, at the end of this file). On a later load Hrolf stands at HrolfMarker (:Init).",
        "local function hrolfAway()",
        f"    evt.SetMapActorPosition({hrolf}, {hx}, {hy}, {hz})",
        "end",
        f"handlers[{event}] = function()",
        f"    if not has({HROLF_SEEN_KEY}) then MM9Cinematic.start(\"{QUARREL}\") end",
        "end",
        "",
    ]


def voice_seconds(name: str) -> float:
    """A cinema voice's length (mm9/extracted/VOICES/VOICES/CINEMA/<folder>/<file>.wav; cutscenes.wav_seconds only
    searches SOUNDS)."""
    folder, file = name.split("\\")[-2:]
    path = ROOT / "mm9/extracted/VOICES/VOICES/CINEMA" / folder.upper() / file.upper().replace(".WAV", ".wav")
    with wave.open(str(path)) as stream:
        return stream.getnframes() / float(stream.getframerate())


# NPC110.scr (Hrolf) and NPC109.scr (Alfrigg) from Hrolf's :OnStart: (speaker, Loopanim clip, voice file, the fixed
# wait before :OnStop and the other's Speak<n>)
QUARREL_LINES = (("Hrolf", "conv2", "01", 5.5), ("Alfrigg", "conv1", "02", 7.3), ("Hrolf", "conv2", "03", 13.3),
                 ("Alfrigg", "conv1", "04c", 3.2), ("Hrolf", "conv5", "05", 4.5), ("Alfrigg", "conv1", "06", 1.0),
                 ("Hrolf", "conv4", "07", 3.0))


def quarrel_scene(hrolf: int, alfrigg: int, hrolf_monster: int, alfrigg_monster: int) -> cutscenes.Scene:
    """NPC110.scr :OnStart..:Trigger8 and NPC109.scr: Hrolf targets Alfrigg (who targets him back, :OnTarget), key 5010;
    each line a Loopanim and its wav, then a fixed wait (not the wav's length) before :OnStop (Stop, Loopanim stand)
    and the other's Speak<n>: Hrolf 01 (5.5 s), Alfrigg 02 (7.3), Hrolf 03 (13.3), Alfrigg 04c (3.2), Hrolf 05 (4.5),
    Alfrigg 06 (1), Hrolf 07 (3); then :Trigger8 sends Alfrigg Fight and both AddEnemy the other's class (Hrolf
    commonerdwarfmaleA, Alfrigg commonerhuman2maleB) and go on BaseMelee: here the two monster rows' relations, close
    range (their rows are those classes on this map), the step `fight` at 37.8 s. No camera: an ambient cinematic
    (overheard talk: no shots, letterbox or input lock; the party walks on). The lines have no text in MM9's data, so
    no subtitles. ALFRIGGFIGHT.scr (key 115, the same wavs) is placed nowhere."""
    scene = cutscenes.Scene(QUARREL, EV_QUARREL, source="NPC110.scr :OnStart..:Trigger8, NPC109.scr", ambient=True)
    cinema = scene.cinema
    who = {"Hrolf": hrolf, "Alfrigg": alfrigg}
    scene.step(0.0, "key", f"MM9.giveKey({HROLF_SEEN_KEY})", note=f":OnStart givekey {HROLF_SEEN_KEY}")
    cinema._cue(0.0, "Hrolf targets Alfrigg", actor=hrolf, action="face", look_at_actor=alfrigg, seconds=0.3)
    cinema._cue(0.0, "Alfrigg targets Hrolf (:OnTarget)", actor=alfrigg, action="face", look_at_actor=hrolf,
                seconds=0.3)
    at = 0.0
    for name, clip, number, wait in QUARREL_LINES:
        voice = f"voices\\cinema\\dwarvesandhumans\\{number}.wav"
        cinema._cue(at, f"{name}: Loopanim {clip}", actor=who[name], action="clip", clip=clip, loop=True)
        cinema.sound(at, voice, note=f"{name} {number}.wav ({voice_seconds(voice):.2f} s)")
        at += wait
        cinema._cue(at, f"{name}: :OnStop (Loopanim stand)", actor=who[name], action="clip", clip="stand", loop=True)
    # Each line is a Speak<n> message to the other (a dead AI takes none: MM9.receives) and each speaker checks that
    # its target lives (bTargetDead): the quarrel reaches :Trigger8's Fight only while both live. (The cues above
    # are presentation: a death mid-quarrel does not cut them.)
    relations = "\n".join([
        f"if MM9.actorAlive({hrolf}) and MM9.receives(\"drangheimcity\", \"Alfrigg\", \"Fight\", {alfrigg}) then",
        f"    evt.SetMonsterRelation({hrolf_monster}, {alfrigg_monster}, {FIGHT_RELATION})",
        f"    evt.SetMonsterRelation({alfrigg_monster}, {hrolf_monster}, {FIGHT_RELATION})",
        "end"])
    scene.step(at, "fight", relations, note=":Trigger8 Fight: AddEnemy both ways, BaseMelee")
    return scene


def fight_over_lua(actors: dict, monsters: dict) -> str:
    """NPC110.scr / NPC109.scr :OnTargetDead: the first death ends the fight (the survivor's RemoveEnemy)."""
    hrolf, alfrigg = actors["Hrolf"], actors["Alfrigg"]
    hm, am = monsters["Hrolf"], monsters["Alfrigg"]
    return "\n".join([
        "-- NPC110.scr / NPC109.scr :OnTargetDead: the first of Hrolf and Alfrigg to die ends their fight (the",
        "-- survivor's RemoveEnemy; the quarrel's fight step set the relations).",
        f"handlers[{EV_FIGHT_OVER}] = function(context)",
        f"    if context.actorIndex ~= {hrolf} and context.actorIndex ~= {alfrigg} then return end",
        f"    if evt.GetMapVar(\"Cinema.{QUARREL}.step.fight\", 0) == 0 then return end",
        f"    evt.SetMonsterRelation({hm}, {am}, 0); evt.SetMonsterRelation({am}, {hm}, 0)",
        "end",
        f"RegisterMonsterKilledHook({EV_FIGHT_OVER}, \"Hrolf and Alfrigg's fight\", handlers[{EV_FIGHT_OVER}])",
        "",
    ])
