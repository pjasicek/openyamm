"""
Wizard's Lab's map Lua: the doors (MM9's locked pair says so), the chests, the DAT's own object wiring and the scripted
objects as native handlers, each citing its .scr (README.md, "Scripted objects"; the behaviour spec of every script
is work/scr_spec.md).

- TeleporterSwitch.scr / TeleporterMulti.scr: six teleporter stations; a click on one of a station's five crystals
  sets where its teleporter sends the party next (one trip), lights the crystal's colour 4 s;
- the closet teleporters (Teleporter1/2, plain Teleporter objects): always on, one closet to the other;
- WizardLabCamera.scr, WizardSummoner.scr, WizardMaster.scr, WizardEffect.scr, WizardDemon.scr: the summoning in the
  tower top, started by the party's arrival at DestinationPurple: MM9's camera cinema is the cinematic `summoning`
  (cinematic_scenes: wizardslab.cinematics.yml), whose steps are the ritual's ticks;
- the super eye (DAT wiring, no .scr): EvilGrandSorcerer1's death lowers the force field, puts out GlowingLight0 and
  shuts and locks DoubleDoor18/25; the Oculus's death unlocks them;
- the cell levers (DAT wiring): Switch<n> opens Cell<n>;
- NPC55.scr (Robinssen, RUDE 55), BookLetter.scr (letters 498, 499), Book.scr, Relic.scr.

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h). Positions are native (work/transform.json: no offset).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

import cutscenes
from dungeon import lua
from dungeon.lights import PULSING_LIGHT_KEY_BASE
from dungeon.source import ROOT, facing_degrees

PROJECT = Path(__file__).resolve().parent
PROPS = PROJECT / "props.json"
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"

# --- Events, timers, cogs, groups ------------------------------------------------------------------------------------
EV_LOAD = 1
EV_LOCKED = 200                     # DoubleDoor10 (Locked 1, no key or unlock trigger)
EV_EYE_DOORS = {"DoubleDoor18": 201, "DoubleDoor25": 202}      # locked while the super eye lives
EV_LEVER = 210                      # 210 + k: the cell levers Switch15..28 (sorted)
EV_CRYSTAL = 230                    # 230 + k: the 30 TeleporterSwitch.scr crystals (CRYSTALS order)
T_POLL = 262
T_CRYSTAL = 263                     # 263 + station - 1 (six stations): the crystal's light goes out after 4 s
T_RITUAL, T_BANISH = 270, 271
EV_KILLED, EV_DAMAGED = 280, 281    # monster killed / damage hooks
EV_SCRIPTED_PROP = 330              # books, letters, the relic: EV_SCRIPTED_PROP + k (props.json order)
COG_PROP = 400                      # SetSprite keys of the props a script removes
NPC_ROBINSSEN = "ReverendMonk0"
# The summoning's cinematic (cinematic_scenes): its done event and its steps, EV_CINEMA + 1.. (cutscenes.Scene)
CINEMA_ID, EV_CINEMA = "summoning", 36000
RUDE_ROBINSSEN = 55

# Actor groups (convert.py places them). Each summoner has a group of its own so the ritual can tell which are dead.
GROUP_SUMMONER = 21                 # 21..26: the six apprentices in WizardSummoner.scr chain order
GROUP_MASTER = 27                   # SummoningGuy3 (WizardMaster.scr)
GROUP_DEMON = 28                    # the summoned Greater Demon
GROUP_NPC = 29                      # Robinssen

# MM9 monster rows (assets_dev/worlds/mm9/data_tables/monster_data.txt)
ROW_APPRENTICE, ROW_GRAND_SORCERER, ROW_DEMON = 9156, 9158, 9242

# WizardSummoner.scr's chain: each apprentice's third parameter is the next one to start; SummoningGuy3 is the master.
CHAIN = ("SummoningGuy0", "SummoningGuy6", "SummoningGuy1", "SummoningGuy5", "SummoningGuy2", "SummoningGuy4")
MASTER = "SummoningGuy3"
RITUAL_FADE_SECONDS = 2.0           # WizardLabCamera.scr :SoftExit (fade out 2 s before the first shot)
CAST_SECONDS = 1.5                  # :ConjureSpell Wait 1.5 -> :CastSpell (both scripts)
CONJURE_SECONDS = 2.5               # :ConjureSpell 1.5 s -> :CastSpell 1 s -> :FinishSpell (both scripts)
LIGHTNING_SECONDS = 1.0             # a shooter's Lightning arc (PROJECTILE.txt Lightning: lifetime 2 s; assumed)
LIGHTNING_LAUNCH, LIGHTNING_HIT = "weapons/chainlight01.wav", "weapons/chainlight03.wav"   # PROJECTILE.txt Lightning
BANISH_SECONDS = 6.0                # WizardMaster.scr :BanishDemon 4 s up, :PerformBanish 2 s down, :RemoveDemon
FINISHES_TO_BANISH = 6              # WizardMaster.scr :BanishDemon (nCounter < 6: wait)
PARTY_RADIUS = 37                   # IndoorWorldRuntime PartyCollisionRadius (native units)
CRYSTAL_LIGHT_SECONDS = 4           # TeleporterSwitch.scr EFFECTS_WAIT_TIME

LEVERS = tuple(f"Switch{k}" for k in range(15, 29))
LOCKED_GROUPS = ("DoubleDoor10",)
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr", "relic.scr")
PROP_COG_SCRIPTS = ()   # props the script hides (none: Relic.scr's relic is a world item, dungeon/pickups.py)
# The TeleporterSwitch.scr crystals (WorldObject models, overrides.yml `models`: nudge movers); map_script checks the
# list against the DAT.
CRYSTALS = tuple(f"{colour}{station}" for station in range(6)
                 for colour in ("yellow", "white", "red", "purple", "green", "blue")
                 if (colour, station) not in (("blue", 0), ("green", 1), ("purple", 2), ("red", 3), ("white", 4),
                                              ("yellow", 5)))
# The closet teleporters: plain Teleporter objects (no script, StartOn 1, UseRotation 0) and their destinations.
CLOSETS = {"Teleporter1": "Teleporter1Dest", "Teleporter2": "Teleporter2Dest"}

MOVER_EVENTS = {
    **{group: (EV_LOCKED, "click") for group in LOCKED_GROUPS},
    **{group: (event, "click") for group, event in EV_EYE_DOORS.items()},
    **{lever: (EV_LEVER + k, "click") for k, lever in enumerate(LEVERS)},
    **{crystal: (EV_CRYSTAL + k, "click") for k, crystal in enumerate(CRYSTALS)},
}


def rude_exit_event(index: int) -> int:
    return 50000 + index


def rude_use_event(index: int) -> int:
    return 53000 + index


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


def script_name(entry: dict) -> str:
    return str(entry.get("script") or "").replace("\\", "/").split("/")[-1].lower()


def scripted_props() -> list:
    """props.json's scripted props (books, letters, the relic), in file order: [(name, entry)]."""
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    return [(e["source_name"], e) for e in entries if script_name(e) in SCRIPTED_PROP_SCRIPTS]


def prop_events(build=None) -> dict:
    """DAT prop name -> click event."""
    return {name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted_props())}


def prop_cogs(build=None) -> dict:
    """The props the script hides (SetSprite cogs), by their script: their props.json names."""
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    names = [e["source_name"] for e in entries if script_name(e) in PROP_COG_SCRIPTS]
    return {name: COG_PROP + k for k, name in enumerate(names)}


# --- Points and volumes -----------------------------------------------------------------------------------------------
def native_point(build, lt) -> list:
    return build.project.native(np.asarray(lt, float)).round().astype(int).tolist()


def on_floor(build, lt) -> list:
    """The native point on the floor under an LT point (the point itself when no floor is found)."""
    floor = build.content.floor_at(lt[0], lt[2], lt[1] + 20)
    point = native_point(build, [lt[0], lt[1] if floor is None else floor, lt[2]])
    point[2] += 2
    return point


def volume(build, name: str) -> list:
    """An MM9 Trigger or Teleporter box (Pos +- Dims, LT) as a native box, reaching down to the floor under it (MM9's
    MoveToFloor puts DestinationPurple's box on the floor; the party's position is its feet)."""
    p = build.source.properties(name)
    centre, dims = np.asarray(p["Pos"], float), np.asarray(p["Dims"], float)
    low, high = centre - dims, centre + dims
    floor = build.content.floor_at(centre[0], centre[2], centre[1] + dims[1])
    if floor is not None:
        low[1] = min(low[1], floor - 4)
    a, b = build.project.native(low), build.project.native(high)
    return [np.minimum(a, b).round().astype(int).tolist(), np.maximum(a, b).round().astype(int).tolist()]


def yaw_units(rotation) -> int:
    return int(round(facing_degrees(rotation) / 360 * 2048)) % 2048


def box(b) -> str:
    return "{" + lua.point(b[0]) + ", " + lua.point(b[1]) + "}"


def touch_box(b) -> str:
    """A TouchNotify volume as the Lua tests it (the party's position, its feet): grown horizontally by the party's
    collision radius, since MM9 fires when the player's body touches the volume. Teleporter2's box lies 31 units
    behind its closet's doors and the party's centre stops 25 units short of the back panel: the plain box was never
    reached (2026-11-05)."""
    low, high = list(b[0]), list(b[1])
    low[0], low[1], high[0], high[1] = low[0] - PARTY_RADIUS, low[1] - PARTY_RADIUS, high[0] + PARTY_RADIUS, \
        high[1] + PARTY_RADIUS
    return box([low, high])


def stations(build) -> tuple[list, list, dict]:
    """The teleporter stations, the destinations and the crystals from the DAT's TeleporterSwitch.scr parameters
    ("<teleporter> <destination> <light>"): stations [TeleporterAt*], destinations [Destination*], crystal -> (station
    number, destination number, pulsing light key)."""
    crystals, station_names, destination_names = {}, [], []
    for o in build.source.objects:
        script = str(o["properties"].get("ScriptName") or "").lower()
        if not script.endswith("teleporterswitch.scr"):
            continue
        teleporter, destination, light = str(o["properties"]["ScriptParams"]).split()
        if teleporter not in station_names:
            station_names.append(teleporter)
        if destination not in destination_names:
            destination_names.append(destination)
        key = PULSING_LIGHT_KEY_BASE + build.source.by_name[light.lower()]["index"]
        crystals[o["name"]] = (teleporter, destination, key)
    if set(crystals) != set(CRYSTALS):
        differ = sorted(set(crystals) ^ set(CRYSTALS))
        raise SystemExit(f"TeleporterSwitch crystals differ from citylua.CRYSTALS: {differ}")
    station_names.sort()
    destination_names.sort()
    numbered = {name: (station_names.index(t) + 1, destination_names.index(d) + 1, key)
                for name, (t, d, key) in crystals.items()}
    return station_names, destination_names, numbered


# --- The script -------------------------------------------------------------------------------------------------------
def map_script(hooks, build) -> str:
    script = lua.Script(build, "Wizard's Lab", writer="citylua.py")
    script.lines.insert(next(i for i, line in enumerate(script.lines) if line.startswith("local function seconds")) + 1,
                        "local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end")
    script.doors()
    script.chests()
    a, o = hooks.actor, hooks.objects
    source = build.source
    groups = {group: ids for group, ids in script.groups.items()}
    group_table = ", ".join(f"{lua.lua_key(g)} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(groups.items()))
    lines = [
        f"local GROUPS = {{{group_table}}}",
        "local function trigger(group) for _, d in ipairs(GROUPS[group]) do "
        "evt.SetDoorState(d, DoorAction.Trigger) end end",
        "local function openGroup(group) for _, d in ipairs(GROUPS[group]) do "
        "evt.SetDoorState(d, DoorAction.Open) end end",
        "local function closeGroup(group) for _, d in ipairs(GROUPS[group]) do "
        "evt.SetDoorState(d, DoorAction.Close) end end",
        "local function has(k) return MM9.hasKey(k) == 1 end",
        "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
        "local function fx(id, p) evt.SpawnWorldEffect(id, p[1], p[2], p[3]) end",
        "local function sprite(cog, on) if cog then evt.SetSprite(cog, on and 1 or 0, \"0\") end end",
        "local function inBox(b, x, y, z)",
        "    return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]",
        "end",
        "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
        "local function fired(timer)",
        "    evt.StopTimer(timer)",
        "    if var(\"Armed\" .. timer) ~= 1 then return false end",
        "    set(\"Armed\" .. timer, 0)",
        "    return true",
        "end",
        "local function locked()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        "local COG = {" + ", ".join(f"{lua.lua_key(n)} = {c}" for n, c in prop_cogs(build).items()) + "}",
        "",
        "-- MM9's locked pair (DoubleDoorL10/R10: Locked 1, no key, nothing unlocks it).",
        f"handlers[{EV_LOCKED}] = function() locked() end",
        "",
    ]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"))

    # --- the super eye ------------------------------------------------------------------------------------------------
    glow = PULSING_LIGHT_KEY_BASE + source.by_name["glowinglight0"]["index"]
    sorcerer, oculus = a["EvilGrandSorcerer1"], a["Oculus0"]
    lines = [
        "-- The super eye (DAT wiring, no .scr). EvilGrandSorcerer1's DeathTriggerTarget 'super eye trigger':",
        "-- GlowingLight0 off, 'super eye door' (the force field) open (256 down), DoubleDoorL25 and R18 closed (MM9",
        "-- names one leaf of each; here both pairs shut, as their CloseWaitTime 4 shuts the other leaves anyway) and",
        "-- both pairs locked. Oculus0's DeathTriggerTarget 'super eye trigger0' unlocks them (the targets",
        "-- 'super eye lock' and 'super eye unlock' name no object). Not in MM9: an Oculus killed first leaves the",
        "-- pairs unlocked (MM9 would lock them for good).",
        "local function superEye()",
        "    if var(\"SuperEye\") == 1 then return end",
        "    set(\"SuperEye\", 1)",
        f"    evt.SetLight({glow}, false)",
        "    openGroup(\"super eye door\")",
        "    if var(\"OculusDead\") == 1 then return end",
        "    closeGroup(\"DoubleDoor18\"); closeGroup(\"DoubleDoor25\")",
        "    set(\"EyeLock\", 1)",
        "end",
    ]
    for group, event in EV_EYE_DOORS.items():
        lines += [f"handlers[{event}] = function()   -- {group}: a plain double door unless the super eye locked it",
                  "    if var(\"EyeLock\") == 1 then locked() return end",
                  f"    trigger(\"{group}\")",
                  "end"]
    script.add(lines + [""], *[(event, "Door", "Door") for event in EV_EYE_DOORS.values()])

    # --- the cell levers ----------------------------------------------------------------------------------------------
    lines = ["-- The cell levers (DAT wiring: RotatingDoor Switch<n>, OpenTriggerTarget0 Cell<n> 'open',",
             "-- CloseTriggerTarget0 Cell<n> 'toggle'; the AITrack 'on'/'off' messages, MM9's AI rails, are not",
             "-- carried)."]
    for k, lever in enumerate(LEVERS):
        cell = "Cell" + lever[len("Switch"):]
        lines += [f"handlers[{EV_LEVER + k}] = function()   -- {lever} -> {cell}",
                  f"    local on = var(\"{lever}\") == 0",
                  f"    set(\"{lever}\", on and 1 or 0)",
                  f"    trigger(\"{lever}\")",
                  f"    if on then openGroup(\"{cell}\") else trigger(\"{cell}\") end",
                  "end"]
        script.registrations.append((EV_LEVER + k, "Lever", "Lever", "event"))
    script.add(lines + [""])

    # --- the teleporters ----------------------------------------------------------------------------------------------
    station_names, destination_names, crystals = stations(build)
    station_rows = []
    for name in station_names:
        p = source.properties(name)
        station_rows.append(f"    {{name = \"{name}\", box = {touch_box(volume(build, name))}, "
                            f"at = {lua.point(native_point(build, p['Pos']))}}},")
    destination_rows = []
    for name in destination_names:
        p = source.properties(name)
        destination_rows.append(f"    {{name = \"{name}\", at = {lua.point(on_floor(build, p['Pos']))}, "
                                f"yaw = {yaw_units(p.get('Rotation'))}}},")
    crystal_rows = [f"    [{EV_CRYSTAL + k}] = {{name = \"{name}\", station = {crystals[name][0]}, "
                    f"dest = {crystals[name][1]}, light = {crystals[name][2]}}},"
                    for k, name in enumerate(CRYSTALS)]
    closet_rows = []
    for teleporter, destination in CLOSETS.items():
        closet_rows.append(f"    {{name = \"{teleporter}\", box = {touch_box(volume(build, teleporter))}, "
                           f"at = {lua.point(on_floor(build, source.properties(destination)['Pos']))}}},")
    purple = destination_names.index("DestinationPurple") + 1
    lines = [
        "-- The teleporters. TeleporterSwitch.scr (the crystals, \"<teleporter> <destination> <light>\"): a click sets",
        "-- the station's destination (MM9's console TELEPORTER_DESTINATION, then 'on' + 'update' to that teleporter",
        "-- only), plays wizardeyeloop.wav and the spell reaver at the teleporter and lights the crystal's colour for",
        "-- 4 s, its 'use' removed meanwhile. TeleporterMulti.scr (TeleporterAt*, Dims 50): the party walking in goes",
        "-- to the destination (UseRotation: facing it), and 0.5 s later the teleporter turns off (:ResetDestination):",
        "-- one trip per click. With no destination set it does nothing (StartOn 1, TeleportDestination \"\").",
        "local STATIONS = {",
        *station_rows,
        "}",
        "local DESTINATIONS = {",
        *destination_rows,
        "}",
        "local CRYSTALS = {",
        *crystal_rows,
        "}",
        "-- The closet teleporters (Teleporter1/2: no script, StartOn 1, UseRotation 0): always on, the party keeps",
        "-- its facing.",
        "local CLOSETS = {",
        *closet_rows,
        "}",
        "local function teleport(at, yaw)",
        "    sound(\"magic/teleport.wav\")",
        "    evt.MoveToMap(at[1], at[2], at[3], yaw, 0, 0, 0, 0)",
        "end",
        "local function pressCrystal(event)",
        "    local c = CRYSTALS[event]",
        "    if var(\"CrystalBusy\" .. c.station) == 1 then return end",
        "    set(\"Dest\" .. c.station, c.dest)",
        "    set(\"CrystalBusy\" .. c.station, 1); set(\"CrystalEvent\" .. c.station, event)",
        "    evt.SetLight(c.light, true)",
        "    sound(\"magic/wizardeyeloop.wav\")",
        "    fx(\"mm9:spell_reaver\", STATIONS[c.station].at)",
        "    openGroup(c.name)",
        f"    arm({T_CRYSTAL} + c.station - 1, {CRYSTAL_LIGHT_SECONDS})",
        "end",
        "local function crystalOff(station)",
        "    local event = var(\"CrystalEvent\" .. station)",
        "    set(\"CrystalBusy\" .. station, 0)",
        "    if CRYSTALS[event] == nil then return end",
        "    evt.SetLight(CRYSTALS[event].light, false)",
        "    closeGroup(CRYSTALS[event].name)",
        "end",
        "for event, _ in pairs(CRYSTALS) do handlers[event] = function() pressCrystal(event) end end",
        "for station = 1, #STATIONS do",
        f"    handlers[{T_CRYSTAL} + station - 1] = function()",
        f"        if fired({T_CRYSTAL} + station - 1) then crystalOff(station) end",
        "    end",
        "end",
        "",
    ]
    script.add(lines, *[(EV_CRYSTAL + k, "Crystal", "Crystal") for k in range(len(CRYSTALS))],
               *[(T_CRYSTAL + k, "Crystal light", None, "timer") for k in range(len(station_names))])

    # --- the summoning ------------------------------------------------------------------------------------------------
    summoners = [a[name] for name in CHAIN]
    # WizardSummoner.scr's first parameter: the apprentice's shooter (ShooterSummon<k>, ProjectileName Lightning)
    shooter_at = [native_point(build, source.properties(str(source.properties(name).get("ScriptParams")).split()[0])
                               ["Pos"]) for name in CHAIN]
    summon_at = on_floor(build, source.properties("SummonLocation")["Pos"])
    master = a[MASTER]
    summoner_set = ", ".join(f"[{index}] = {k + 1}" for k, index in enumerate(summoners))
    lines = [
        "-- The summoning in the tower top. WizardLabCamera.scr (CameraSummon) runs a camera cinema when the party",
        "-- first arrives at DestinationPurple (a touch Trigger, ActivationCount 1, 'next' to the camera): fade out 2",
        "-- s, then shots at MarkerLocation0-3; its first shot's notify (TriggerNotify0) starts SummoningGuy0. The",
        "-- cinema is the cinematic summoning (cinematic_scenes), whose steps run the ritual's ticks below (each once,",
        "-- in order; a skip runs them at once). WizardSummoner.scr (six apprentices, friends of the party):",
        "-- :ConjureSpell (thunder, its shooter's sparklies and green dots, WizardEffect.scr), 2.5 s later",
        "-- :FinishSpell (the shooter's lightning and bugs at SummonLocation: shoot) starts the next in the chain",
        "-- 0 -> 6 -> 1 -> 5 -> 2 -> 4 -> the master.",
        "-- WizardMaster.scr (SummoningGuy3): :ConjureSpell (meteor, town portal, sparklies, column",
        "-- of fire at SummonLocation), 2.5 s later :Summon spawns a Greater Demon (WizardDemon.scr: enemy of the",
        "-- sorcerers and the party), elemental blast and paralyze. The apprentices then fight it (AddEnemy",
        "-- GreaterDemon); one hurt by anything but the party dies at once (:OnDamage -> Die) and sends the master",
        "-- 'finish'; at six the master banishes the demon (:BanishDemon: dark grasp, lifted 4 s, dropped 2 s,",
        "-- :RemoveDemon). When the demon is gone (:OnTargetDead) the master passes out (dies) while the party is his",
        "-- friend, else turns on the party (EvilSorcerer.scr). Hurting an apprentice makes it the party's enemy and",
        "-- the party no friend (PLAYER_FRIEND FALSE); hurting the master only the latter. Here: a dying apprentice is",
        "-- killed by a lethal hit (the damage hook); the master passing out is hidden (no script call kills an",
        "-- actor); after the demon is up any hit on an apprentice counts as the demon's (README).",
        f"local SUMMONERS = {{{', '.join(map(str, summoners))}}}",
        f"local SUMMONER_OF = {{{summoner_set}}}",
        f"local SUMMON_AT = {lua.point(summon_at)}",
        f"local SHOOTER_AT = {{{', '.join(lua.point(p) for p in shooter_at)}}}   -- their lightning's start",
        f"local MASTER = {master}",
        "local function summonerAlive(k)",
        f"    return not evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_SUMMONER} + k - 1, 0, false)",
        "end",
        "-- Apprentice k's :FinishSpell (Trigger hShooter, shoot), run by the next tick (2.5 s after its :ConjureSpell,",
        "-- as the next caster starts): its shooter (ShooterSummon<k>, ProjectileName Lightning) fires at SummonLocation",
        "-- (PROJECTILE.txt Lightning: launch chainlight01, explosion Sparks with chainlight03; here an arc and MM9's",
        "-- Sparks explosion) and WizardEffect.scr :PlayShootEffect plays SPELL_BUGS at SummonLocation. A dead",
        "-- apprentice's :FinishSpell never comes.",
        "local function shoot(k, timed)",
        "    if not summonerAlive(k) then return end",
        "    local from = SHOOTER_AT[k]",
        f"    evt.Beam(\"SummonBeam\" .. k, \"openyamm:fx/arc_beam\", from[1], from[2], from[3], SUMMON_AT[1], "
        f"SUMMON_AT[2], SUMMON_AT[3], {LIGHTNING_SECONDS})",
        "    fx(\"mm9:explosion_sparks\", SUMMON_AT)",
        "    fx(\"mm9:bugs\", SUMMON_AT)",
        f"    if timed then sound(\"{LIGHTNING_LAUNCH}\"); sound(\"{LIGHTNING_HIT}\") end",
        "end",
        "-- timed: timer 270 runs a summoning an old save left half-way (it plays the sounds the cinematic's cues play",
        "-- and arms the next tick)",
        "local function ritualStep(timed)",
        "    local step = var(\"RitualStep\")",
        f"    if step >= 2 and step <= {len(CHAIN) + 1} then shoot(step - 1, timed) end",
        "    if step >= 1 and step <= 6 then",
        "        if not summonerAlive(step) then return end   -- MM9: a dead apprentice never starts the next",
        "        if timed then sound(\"ambient/thunder/thunderlong.wav\") end",
        "        -- WizardEffect.scr :PlayConjureEffect: DoClientFX hCaster (the apprentice), SPELL_SPARKLIES, on its",
        "        -- body; DoClientFX hMe (the shooter above it), SPELL_GREENDOTS. Its hands' dots are its clips' own DoFX",
        "        -- keys (fidget2 redyeldots, rattack1 greenyeldots: actors.yml events, played by the cinematic's cues).",
        "        MM9.actorFx(SUMMONERS[step], \"mm9:sparklies\")",
        "        fx(\"mm9:greenyeldots\", SHOOTER_AT[step])",
        "        set(\"RitualStep\", step + 1)",
        f"        if timed then arm({T_RITUAL}, {CONJURE_SECONDS}) end",
        "    elseif step == 7 then",
        f"        if evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_MASTER}, 0, false) then return end",
        "        fx(\"mm9:meteor_shower\", SUMMON_AT); fx(\"mm9:town_portal\", SUMMON_AT)",
        "        fx(\"mm9:sparklies\", SUMMON_AT); fx(\"mm9:column_of_fire\", SUMMON_AT)",
        "        if timed then sound(\"magic/cast03.wav\") end",
        "        set(\"RitualStep\", 8)",
        f"        if timed then arm({T_RITUAL}, {CONJURE_SECONDS}) end",
        "    elseif step == 8 then",
        "        if timed then sound(\"animsounds/dragon/fidget2.wav\") end",
        f"        evt.SummonMonstersById({{monster = {ROW_DEMON}, x = SUMMON_AT[1], y = SUMMON_AT[2], "
        f"z = SUMMON_AT[3], radius = 32, group = {GROUP_DEMON}, count = 1}})",
        "        fx(\"mm9:elemental_blast\", SUMMON_AT); fx(\"mm9:paralyze\", SUMMON_AT)",
        "        -- :Backup then :BeginBanish (the master steps back): DoClientFX hMe, SPELL_SPARKLIES and SPELL_BLUEFIRE",
        "        MM9.actorFx(MASTER, \"mm9:sparklies\"); MM9.actorFx(MASTER, \"mm9:fireblue\")",
        f"        for _, row in ipairs({{{ROW_APPRENTICE}, {ROW_GRAND_SORCERER}}}) do",
        f"            evt.SetMonsterRelation({ROW_DEMON}, row, 2); evt.SetMonsterRelation(row, {ROW_DEMON}, 2)",
        "        end",
        "        set(\"RitualStep\", 9); set(\"DemonUp\", 1)",
        "    end",
        "end",
        "local function ritualAdvance(step)   -- a step of the cinematic summoning: the ritual's tick `step`",
        "    if var(\"RitualStep\") == step then ritualStep(false) end",
        "end",
        "local function startRitual()   -- DestinationPurple -> CameraSummon 'next' (once): the cinematic",
        "    if var(\"RitualStep\") ~= 0 then return end",
        "    set(\"RitualStep\", 1)",
        f"    MM9Cinematic.start(\"{CINEMA_ID}\")",
        "end",
        f"handlers[{T_RITUAL}] = function() if fired({T_RITUAL}) then ritualStep(true) end end",
        "local function demonGone()   -- WizardMaster.scr :OnTargetDead",
        "    if var(\"DemonGone\") == 1 then return end",
        "    set(\"DemonGone\", 1)",
        f"    if evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_MASTER}, 0, false) then return end",
        "    if var(\"Betrayed\") == 1 then",
        f"        evt.SetMonGroupBit({GROUP_MASTER}, MonsterBits.Hostile, true)   -- RunScript EvilSorcerer.scr",
        "    else",
        "        sound(\"animsounds/evilsorcerer/wince2.wav\")   -- :PassOut",
        "        MM9.removeActor(MASTER)",
        "    end",
        "end",
        "local function banish()   -- :BanishDemon at the sixth 'finish'",
        "    if var(\"Banishing\") == 1 or var(\"DemonGone\") == 1 then return end",
        "    set(\"Banishing\", 1)",
        "    sound(\"magic/wizardeyeloop.wav\")",
        "    fx(\"mm9:dark_grasp\", SUMMON_AT)",
        f"    arm({T_BANISH}, {BANISH_SECONDS})",
        "end",
        f"handlers[{T_BANISH}] = function()   -- :RemoveDemon",
        f"    if not fired({T_BANISH}) then return end",
        "    sound(\"magic/cast01.wav\")",
        "    fx(\"mm9:spell_reaver\", SUMMON_AT); fx(\"mm9:elemental_blast\", SUMMON_AT)",
        "    -- Trigger hLocation, destroy: a demon already slain stays a corpse (DESTROY on a dead AI does nothing)",
        f"    if not evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_DEMON}, 0, false) then",
        f"        evt.SetMonGroupBit({GROUP_DEMON}, MonsterBits.Invisible, true)",
        "    end",
        "    demonGone()",
        "end",
        "local function betray(index)   -- WizardSummoner.scr / WizardMaster.scr :OnDamage by the party",
        "    set(\"Betrayed\", 1)",
        "    local k = SUMMONER_OF[index]",
        f"    if k ~= nil then evt.SetMonGroupBit({GROUP_SUMMONER} + k - 1, MonsterBits.Hostile, true) end",
        "end",
        f"handlers[{EV_DAMAGED}] = function(context)",
        "    local index = context.actorIndex",
        "    if SUMMONER_OF[index] == nil and index ~= MASTER then return end",
        "    if var(\"DemonUp\") == 0 or var(\"DemonGone\") == 1 then betray(index) return end",
        "    if SUMMONER_OF[index] ~= nil then   -- :OnDamage, not the party: DoClientFX hShooter (itself), SPELL_BLUEDOTS; Die",
        "        MM9.actorFx(index, \"mm9:bluedots\", \"palm_left,palm_right\")   -- its emitters on LHand1 and RHand1",
        "        evt.SetHookDamage(100000)",
        "    end",
        "end",
        f"handlers[{EV_KILLED}] = function(context)",
        "    local index = context.actorIndex",
        f"    if index == {sorcerer} then superEye() end   -- EvilGrandSorcerer1",
        f"    if index == {oculus} then set(\"OculusDead\", 1); set(\"EyeLock\", 0) end   -- Oculus0",
        "    -- 'finish' to the master: a dead master takes none (MM9.receives), so no banishing",
        "    if SUMMONER_OF[index] ~= nil and var(\"DemonUp\") == 1",
        f"            and MM9.receives(\"wizardslab\", \"{MASTER}\", \"finish\", MASTER) then",
        "        set(\"Finished\", var(\"Finished\") + 1)",
        f"        if var(\"Finished\") >= {FINISHES_TO_BANISH} then banish() end",
        "    end",
        "    if var(\"DemonUp\") == 1 and var(\"DemonGone\") == 0",
        f"            and evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_DEMON}, 0, false) then",
        "        demonGone()",
        "    end",
        "end",
        "",
    ]
    script.add(lines, (T_RITUAL, "Summoning", None, "timer"), (T_BANISH, "Banishing", None, "timer"))
    script.hooks += [f'RegisterMonsterKilledHook({EV_KILLED}, "Wizard\'s Lab deaths", handlers[{EV_KILLED}])',
                     f'RegisterMonsterDamageHook({EV_DAMAGED}, "The summoners", handlers[{EV_DAMAGED}])']

    # --- Robinssen ----------------------------------------------------------------------------------------------------
    robinssen = o[NPC_ROBINSSEN]
    lines = [
        f"-- NPC55.scr (Mad Wizard Robinssen, {NPC_ROBINSSEN}, RUDE {RUDE_ROBINSSEN}): a click plays his voice and",
        f"-- opens the dialogue (:OnUse); its exit (:OnRude -> :BlackOrb) sells the Black Orb of Knowledge: with the",
        f"-- deal agreed (key 312, RUDE row 8.1) and no orb yet (313): 2 000 gold taken, key 313, item 250, quest.wav;",
        f"-- without the gold the deal is off (312 taken) and a party voice complains (nogold.inc :NoGold, not",
        f"-- carried).",
        f"handlers[{rude_use_event(robinssen)}] = function()",
        "    MM9.playSound(\"voices/npc/npc_055.wav\")",
        f"    MM9.openRude({RUDE_ROBINSSEN})",
        "end",
        f"handlers[{rude_exit_event(robinssen)}] = function()",
        "    if has(313) or not has(312) then return end",
        "    if MM9.hasGold(2000) == 1 then",
        "        MM9.takeGold(2000); MM9.giveKey(313); MM9.giveItem(250, \"wizardslab:Robinssen\"); quest()",
        "    else",
        "        MM9.takeKey(312)",
        "        evt.StatusText(\"You don't have enough gold.\")",
        "    end",
        "end",
        "",
    ]
    script.add(lines, (rude_use_event(robinssen), "Robinssen", None), (rude_exit_event(robinssen), "Robinssen", None))

    # --- scripted props -----------------------------------------------------------------------------------------------
    lines = ["-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (pages turn, no text),",
             "-- Relic.scr."]
    for k, (name, entry) in enumerate(scripted_props()):
        event = EV_SCRIPTED_PROP + k
        kind = script_name(entry)
        if kind == "bookletter.scr":
            number = int(str(entry["script_params"]).split()[0])
            title, text = letter(number)
            message = lua_string(title + chr(10) + chr(10) + text)
            lines.append(f"handlers[{event}] = function() sound(\"events/bookopen.wav\"); "
                         f"evt.SimpleMessage({message}) end   -- {name} ({number})")
            script.registrations.append((event, name, "Read", "event"))
        elif kind == "relic.scr":
            lines += [
                f"-- {name}: Relic.scr, the Saint's Relic (item 368), a world item (dungeon/pickups.py). Its pickup: with",
                f"-- key 338 and no 340 key 340, else without 339 key 339; quest.wav plays.",
                f"handlers[{event}] = function()",
                "    local key = has(338) and 340 or 339",
                "    if has(key) then return end",
                "    MM9.giveKey(key); quest()",
                "end",
            ]
            script.registrations.append((event, name, None, "event"))
        else:
            lines.append(f"handlers[{event}] = function() sound(\"events/bookopen.wav\") end   -- {name} (Book.scr)")
            script.registrations.append((event, name, "Book", "event"))
    script.add(lines + [""])

    # --- the poll and map load ----------------------------------------------------------------------------------------
    purple_box = volume(build, "DestinationPurple")
    lines = [
        "-- MM9's Teleporter and Trigger volumes, polled four times a second (the party's feet in the box; one shot",
        "-- per entry).",
        f"local PURPLE = {touch_box(purple_box)}   -- DestinationPurple (Trigger, TouchNotify, ActivationCount 1)",
        "local function volumes()",
        "    local x, y, z = evt.GetPartyPosition()",
        "    for k, s in ipairs(STATIONS) do",
        "        local inside = inBox(s.box, x, y, z)",
        "        local entered = inside and var(\"In\" .. s.name) == 0",
        "        set(\"In\" .. s.name, inside and 1 or 0)",
        "        if entered and var(\"Dest\" .. k) > 0 then",
        "            local dest = var(\"Dest\" .. k)",
        "            local d = DESTINATIONS[dest]",
        "            set(\"Dest\" .. k, 0)   -- TeleporterMulti.scr :ResetDestination",
        "            teleport(d.at, d.yaw)",
        # The arrival on DestinationPurple is its touch: the ritual starts with the teleport, not on a later poll
        # (a party still walking crosses the plate between two polls; the user, 2026-11-10).
        f"            if dest == {purple} then startRitual() end",
        "            return",
        "        end",
        "    end",
        "    for _, c in ipairs(CLOSETS) do",
        "        local inside = inBox(c.box, x, y, z)",
        "        local entered = inside and var(\"In\" .. c.name) == 0",
        "        set(\"In\" .. c.name, inside and 1 or 0)",
        "        if entered then teleport(c.at, nil) return end",
        "    end",
        f"    if inBox(PURPLE, x, y, z) then startRitual() end   -- destination {purple}",
        "end",
        "local function poll()",
        "    volumes()",
        f"    evt.StartTimer({T_POLL}, seconds(0.25))",
        "end",
        f"handlers[{T_POLL}] = poll",
        f"handlers[{EV_LOAD}] = function()   -- map load",
        "    for station = 1, #STATIONS do if var(\"CrystalBusy\" .. station) == 1 then crystalOff(station) end end",
        "    local step = var(\"RitualStep\")   -- a summoning saved half-way goes on",
        f"    if step >= 1 and step <= 8 then arm({T_RITUAL}, {CONJURE_SECONDS}) end",
        f"    if var(\"Banishing\") == 1 and var(\"DemonGone\") == 0 then arm({T_BANISH}, 1) end",
        "    poll()",
        "end",
    ]
    script.add(lines, (T_POLL, "Teleporters", None, "timer"), (EV_LOAD, "Map load", None))
    hooks.scenes = cinematic_scenes(a)
    return script.finish(on_load=[EV_LOAD]) + cutscenes.lua_block(hooks.scenes)


# --- the summoning's cinematic ----------------------------------------------------------------------------------------
# mm9_evilsorcerer.glb's clips for MM9's fidget2, rattack1 and taunt (actors.yml fidget, attack_ranged, script_clips):
# MM9's fidget2 is the GLB's Fidget (EVILSORCERER.abc has no fidget1: its fidget2-4 are Fidget, Fidget2, Fidget3)
CLIP_CONJURE, CLIP_CAST, CLIP_TAUNT = "Fidget", "AttackRanged", "Taunt"
THUNDER, MASTER_CAST = "ambient/thunder/thunderlong.wav", "magic/cast03.wav"
DEMON_ROAR = "animsounds/dragon/fidget2.wav"


def cinematic_scenes(actors: dict) -> list:
    """WizardLabCamera.scr + CutScene.inc (CameraSummon) as the cinematic `summoning` (devdocs/mm9_rework/
    MM9_CUTSCENES.md). DestinationPurple's 'next' runs :SoftExit: ScreenFadeOut 0, 2 s, :SoftEntrance: the first scene
    and ScreenFadeIn 2. Each scene snaps the camera to MarkerLocation<k> facing MarkerTarget<k> (AlignCamera:
    FaceObject at rate 0; here a look_at, pitch too: level, the targets 40 degrees down would be out of the picture)
    and triggers TriggerNotify<k>: the first starts SummoningGuy0 and each sends 'next' back through
    TriggerSwitchTo<k+1> after its SendDelay (8, 5, 0 s: MarkerLocation2's scene lasts no frame and is left out).
    The last scene ends at the master's :EndScene (taunt, then 1 s) with CameraOff (the list's next, MarkerLocation4,
    does not exist). The ritual (WizardSummoner.scr chain 2.5 s each, WizardMaster.scr :ConjureSpell, :Summon) is the
    steps, each a tick of ritualStep (the beams, effects, the demon); its sounds, the casters' clips and turns are cues.
    actors: DAT name -> map actor index (WizardsLab.actor)."""
    objects = cutscenes.Objects.load("wizardslab")
    frame = cutscenes.Frame(PROJECT)
    scene = cutscenes.Scene(CINEMA_ID, EV_CINEMA, source="WizardLabCamera.scr, CutScene.inc (CameraSummon); "
                                                         "WizardSummoner.scr, WizardMaster.scr")
    cinema = scene.cinema
    first = RITUAL_FADE_SECONDS
    master_at = first + len(CHAIN) * CONJURE_SECONDS
    summon_at = master_at + CONJURE_SECONDS
    taunt, _ = cutscenes.abc_animation("EVILSORCERER", "taunt")
    end = summon_at + taunt + 1.0                       # :Summon PlayAnim taunt -> :Backup Wait 1 -> :EndScene
    starts = [first]
    for k in range(1, 4):
        starts.append(starts[-1] + float(objects.named(f"TriggerSwitchTo{k}")["values"]["SendDelay"]))
    starts[0] = 0.0                                     # the first camera behind the black from the start
    bounds = starts + [end]
    for k in range(4):
        duration = bounds[k + 1] - bounds[k]
        if duration <= 0:
            continue
        eye = frame.point(objects.named(f"MarkerLocation{k}")["values"]["Pos"])
        target = frame.point(objects.named(f"MarkerTarget{k}")["values"]["Pos"])
        cinema.fixed(duration, eye, look_at=target, fov=cutscenes.MM9_CAMERA_FOV,
                     note=f"MarkerLocation{k} facing MarkerTarget{k}")
    cinema.fade(0.0, "out", 0.0, note=":SoftExit ScreenFadeOut 0")
    cinema.fade(first, "in", 2.0, note=":SoftEntrance ScreenFadeIn 2")
    centre = frame.point(objects.named("SummonLocation")["values"]["Pos"])
    for name in CHAIN:
        cinema._cue(0.0, f"{name} FaceObject SummonLocation", actor=actors[name], action="face",
                    look_at=[round(v, 1) for v in centre], seconds=0)
    for k, name in enumerate(CHAIN):
        at = first + k * CONJURE_SECONDS
        previous = f"; {CHAIN[k - 1]} :FinishSpell (lightning, bugs)" if k > 0 else ""
        scene.step(at, f"apprentice{k + 1}", f"ritualAdvance({k + 1})",
                   note=f"{name} :ConjureSpell (sparklies, green dots){previous}")
        cinema.sound(at, THUNDER, note=f"{name} :ConjureSpell")
        cinema._cue(at, f"{name} fidget2", actor=actors[name], action="clip", clip=CLIP_CONJURE, loop=False)
        cinema._cue(at + CAST_SECONDS, f"{name} :CastSpell rattack1", actor=actors[name], action="clip",
                    clip=CLIP_CAST, loop=False)
        cinema.sound(at + CONJURE_SECONDS, LIGHTNING_LAUNCH, note=f"{name} :FinishSpell: the shooter's Lightning")
        cinema.sound(at + CONJURE_SECONDS, LIGHTNING_HIT, note=f"{name} :FinishSpell: the Lightning's explosion")
    master = actors[MASTER]
    scene.step(master_at, "master", f"ritualAdvance({len(CHAIN) + 1})",
               note=f"{MASTER} :ConjureSpell (meteor, town portal, sparklies, column of fire); "
                    f"{CHAIN[-1]} :FinishSpell (lightning, bugs)")
    cinema._cue(master_at, f"{MASTER} LoopAnim fidget2", actor=master, action="clip", clip=CLIP_CONJURE, loop=True)
    cinema.sound(master_at + CAST_SECONDS, MASTER_CAST, note=f"{MASTER} :CastSpell")
    cinema._cue(master_at + CAST_SECONDS, f"{MASTER} :CastSpell rattack1", actor=master, action="clip",
                clip=CLIP_CAST, loop=False)
    scene.step(summon_at, "demon", f"ritualAdvance({len(CHAIN) + 2})", note=f"{MASTER} :Summon: the Greater Demon")
    cinema.sound(summon_at, DEMON_ROAR, note=":Summon")
    cinema._cue(summon_at, f"{MASTER} :Summon taunt", actor=master, action="clip", clip=CLIP_TAUNT, loop=False)
    return [scene]
