"""
Arslegard City's map Lua: the doors (MM9's locked doors say so; Njam's house opens with Njam's Key), the Great Gate
scenes (FateMan.scr, WritMan.scr: the cinematics gate_fate and gate_writ, gate_cinematics.py), Njam's chase, Sven,
Hanndl and the letters as native handlers, each citing its .scr (README.md, "Scripted objects", "Cinematics").

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h).
"""

from __future__ import annotations

import csv
import json

import numpy as np

import cutscenes
import gate_cinematics
from dungeon import lua
from dungeon.source import ROOT
from quest_xp import balanced_experience, experience_lua, experience_note

LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
REVIEW_TRANSITIONS = ROOT / "output/mm9_rework/assets_dev/worlds/mm9/data_tables/map_transitions.txt"
DARK_PASSAGEWAY_ROW = "mm9:transition/arslegardcity/147"     # ExitTrigger2: FateMan.scr's `trigger ExitTrigger2`
EV_LOAD, EV_LOCKED, EV_NJAM_HOUSE, EV_NJAM_CELL, EV_GATE = 1, 230, 231, 232, 233
EV_NJAM_TRIGGER = 240               # Trigger0 (the pad in Njam's house): NjamChase.scr's Chase
EV_NJAM_DAMAGE = 241                # the monster damage hook (an id outside the map's events)
T_POLL = 260
EV_SCRIPTED_PROP = 330              # letters, books, the scroll: EV_SCRIPTED_PROP + k
# (GiveTake.scr's scroll Prop8, Njam's Struggle, is a world item: ../mm9r_common/dungeon/pickups.py)
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr")
ITEM_NJAM_KEY = 576                 # Doorlock.scr 576 on NjamDoor0/1: Njam's Key
KEY_FATE = 98                       # FateMan.scr: the Writ of Fate cinema has played
KEY_WRIT, KEY_WRIT_DONE = 100, 9515  # WritMan.scr: the Writ shown (100), Hanndl gone and the gate open (9515)
KEY_NJAM_CHASE, KEY_NJAM_DONE = 108, 470   # NjamChase.scr

# MM9 doors with Locked 1 that nothing unlocks here: the Thousand Terrors' double door (its exit volume stands in front
# of it) and Njam's back door. A click says the door is locked (MM9 jiggles it, doorlock01.wav).
LOCKED_GROUPS = ["ClankDoor1", "NjamBackDoor0"]
MOVER_EVENTS = {**{group: (EV_LOCKED, "click") for group in LOCKED_GROUPS},
                "NjamDoor0": (EV_NJAM_HOUSE, "click"), "Njamdoor": (EV_NJAM_CELL, "click"),
                "RotatingDoor0": (EV_GATE, "click")}



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


def scripted_props(build=None) -> list:
    """props.json's scripted props (letters, books), in file order: [(name, entry)]."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    return [(e["source_name"], e) for e in entries
            if str(e.get("script") or "").lower().replace("scripts\\", "").strip() in SCRIPTED_PROP_SCRIPTS]


def prop_events(build) -> dict:
    return {name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted_props(build))}


def pads(hooks, build) -> dict:
    """Trigger0 (in Njam's house: Njam Chase, its own Off) as an invisible pressure pad."""
    o = build.source.by_name["trigger0"]
    p = o["properties"]
    entry = build.content.pad("Trigger0", p["Pos"], p["Dims"], EV_NJAM_TRIGGER)
    return {"Trigger0": entry}


def dark_passageway_arrival() -> tuple:
    """ExitTrigger2's row in the review root's transitions table: the Dark Passageway's StartPoint0 arrival."""
    with open(REVIEW_TRANSITIONS, newline="", encoding="latin-1") as stream:
        lines = stream.read().split("\n")
    column = {name: i for i, name in enumerate(lines[0].split("\t"))}
    for line in lines[1:]:
        cells = line.split("\t")
        if cells[0] == DARK_PASSAGEWAY_ROW:
            return (int(float(cells[column["ArrivalX"]])), int(float(cells[column["ArrivalY"]])),
                    int(float(cells[column["ArrivalZ"]])), int(float(cells[column["FacingYawUnits"]])),
                    cells[column["DestinationMapFile"]])
    raise SystemExit(f"{DARK_PASSAGEWAY_ROW}: no transition row")


def map_script(hooks, build) -> str:
    script = lua.Script(build, "Arslegard City")
    script.doors()
    a, o = hooks.actor, hooks.objects
    scripted = scripted_props(build)
    dmap = dark_passageway_arrival()[4]
    njam_house = [m["node"][5:] for m in build.movers if m["group"] == "NjamDoor0"]
    njam_cell = [m["node"][5:] for m in build.movers if m["group"] == "Njamdoor"]
    gate = [m["node"][5:] for m in build.movers if m["group"] == "RotatingDoor0"]

    def toggle(leaves):
        return " ".join(f"evt.SetDoorState(DOORS[\"{leaf}\"], DoorAction.Trigger)" for leaf in leaves)

    def opened(leaves):
        return " ".join(f"evt.SetDoorState(DOORS[\"{leaf}\"], DoorAction.Open)" for leaf in leaves)

    lines = [
        "local function has(k) return MM9.hasKey(k) == 1 end",
        "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function locked()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        "",
        "-- MM9's locked doors that nothing here unlocks (Locked 1): the Thousand Terrors' double door, Njam's back door.",
        f"handlers[{EV_LOCKED}] = locked",
        f"-- NjamDoor0/1 (Doorlock.scr 576): Njam's Key ({ITEM_NJAM_KEY}, Krohn's reward in the Hall of the Gods) opens",
        "-- them; without it they are locked.",
        f"handlers[{EV_NJAM_HOUSE}] = function()",
        f"    if var(\"NjamHouseOpen\") == 1 or MM9.hasItem({ITEM_NJAM_KEY}, \"arslegardcity:NjamDoor0\") == 1 then",
        f"        set(\"NjamHouseOpen\", 1); {toggle(njam_house)}",
        "    else locked() end",
        "end",
        f"-- Njamdoor (Locked, Sticky): Njam's own door, unlocked by his chase (NjamChase.scr, key {KEY_NJAM_DONE}).",
        f"handlers[{EV_NJAM_CELL}] = function()",
        f"    if has({KEY_NJAM_DONE}) then {toggle(njam_cell)} else locked() end",
        "end",
        f"-- RotatingDoor0/1, the Great Gate (Locked): WritMan.scr unlocks and opens it (key {KEY_WRIT_DONE}).",
        f"handlers[{EV_GATE}] = function()",
        f"    if has({KEY_WRIT_DONE}) then {toggle(gate)} else locked() end",
        "end",
        "",
    ]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"), (EV_NJAM_HOUSE, "Njam's door", "Door"),
               (EV_NJAM_CELL, "Door", "Door"), (EV_GATE, "The Great Gate", "Door"))

    lines = [
        f"-- NjamChase.scr (Njam the Meddler, Trigger0 'Chase' in his house): with the chase on (key {KEY_NJAM_CHASE}) and",
        f"-- not yet run ({KEY_NJAM_DONE}): his door unlocked, key {KEY_NJAM_DONE}, 226 000 experience, the quest sound,",
        "-- and Njam attacks the party (Addenemy player; :Chase: Target the player, so his behaviour, njam.lua's",
        "-- njamchase.scr mode, gets the \"Chase\" trigger). A hit on him starts it too (OnDamage Chase). Gone once it",
        f"-- ran (:Init: removed with {KEY_NJAM_DONE}).",
        "local function njamChase()",
        f"    if has({KEY_NJAM_DONE}) or not has({KEY_NJAM_CHASE}) then return end",
        f"    MM9.giveKey({KEY_NJAM_DONE}); MM9.giveExperience({balanced_experience(226000, KEY_NJAM_DONE)}); quest()"
        f"{experience_note(226000, KEY_NJAM_DONE)}",
        "    set(\"NjamChase\", 1)",
        f"    evt.SetMonGroupBit({hooks_group('njam')}, MonsterBits.Hostile, true)",
        f"    evt.TriggerActor({a['NjamtheMeddler0']}, \"Chase\")",
        "    -- the converter placed him still (MM9 gives him no wander); the chase is MM9's monster AI: he walks",
        f"    evt.SetActorImmobile({a['NjamtheMeddler0']}, false)",
        "    -- MM9 unlocks Njamdoor \"and him to go through it\" (BaseDoor); a Locked door gets no ai_open here,",
        "    -- so the chase opens it",
        f"    {opened(njam_cell)}",
        "end",
        "-- Trigger0's Chase is a message to Njam: a dead (or removed) Njam takes none (MM9.receives), so no key, no",
        "-- experience and his door stays locked.",
        f"handlers[{EV_NJAM_TRIGGER}] = function()",
        f"    local njam = {a['NjamtheMeddler0']}",
        "    if MM9.receives(\"arslegardcity\", \"NjamtheMeddler0\", \"Chase\", njam) then njamChase() end",
        "end",
        "",
        "-- NPC334.scr (Hanndl the Gatekeeper, RUDE 334, by the gate): with Gungnir's errand (key 353) and Gungnir (item",
        "-- 189) a click unlocks its row (354); the exit after the errand (356 without 357) takes Gungnir and pays 40 000",
        "-- gold and 5 000 experience (357).",
        f"handlers[{rude_use_event(o['Hanndl1'])}] = function()",
        "    if has(353) and MM9.hasItem(189, \"arslegardcity:Hanndl\") == 1 then MM9.giveKey(354) end",
        "    MM9.openRude(334)",
        "end",
        f"handlers[{rude_exit_event(o['Hanndl1'])}] = function()",
        "    if not has(357) and has(356) then",
        "        MM9.takeItem(189, \"arslegardcity:Hanndl\"); MM9.giveKey(357); MM9.giveGold(40000); "
        f"{experience_lua(5000, 357)}",
        "        quest()",
        "    end",
        "end",
        "",
        "-- NPC339.scr (Jokull the Ugly, RUDE 339, the Stumbling Hero): the exit after the bathhouse is cleaned (351",
        "-- without 352) pays 80 000 experience and 5 000 gold (352).",
        f"handlers[{rude_exit_event(o['ShopkeeperHuman2MaleA0'])}] = function()",
        "    if not has(352) and has(351) then",
        f"        MM9.giveKey(352); {experience_lua(80000, 352)}",
        "        MM9.giveGold(5000); quest()",
        "    end",
        "end",
        "",
        "-- NPC3.scr (Sven Forkbeard, RUDE 3, \"Arslegard\"): here with key 102, gone with 104. The click (United.inc",
        "-- :OnCheck, Sven's keys 82, 38, 51, 63, 74): the five clans united gives key 178. The exit: GoGetEm (104 -> 486),",
        "-- Thjorad (32 -> 163, 12 000 experience, 6 000 gold, item 197 taken), Refinery (33 -> 177, 68 004, 3 000),",
        "-- United (83 -> 179, 26 500, 6 000), Lifesaver (234 -> 235, 5 000 experience, 10 000 gold).",
        f"handlers[{rude_use_event(o['SvenSvenssen0'])}] = function()",
        "    if not has(178) and has(82) and has(38) and has(51) and has(63) and has(74) then MM9.giveKey(178) end",
        "    MM9.openRude(3)",
        "end",
        f"handlers[{rude_exit_event(o['SvenSvenssen0'])}] = function()",
        "    if has(104) and not has(486) then MM9.giveKey(486); quest() end",
        "    if not has(163) and has(32) then",
        f"        MM9.giveKey(163); MM9.giveExperience({balanced_experience(12000, 163)}); MM9.giveGold(6000); quest()",
        "        MM9.takeItem(197, \"arslegardcity:Sven\")",
        "    end",
        f"    if not has(177) and has(33) then MM9.giveKey(177); "
        f"MM9.giveExperience({balanced_experience(68004, 177)}); "
        f"MM9.giveGold(3000); quest() end{experience_note(68004, 177)}",
        f"    if not has(179) and has(83) then MM9.giveKey(179); "
        f"MM9.giveExperience({balanced_experience(26500, 179)}); MM9.giveGold(6000) end{experience_note(26500, 179)}",
        f"    if not has(235) and has(234) then MM9.giveExperience({balanced_experience(5000, 235)}); "
        "MM9.giveGold(10000); quest(); MM9.giveKey(235) end",
        f"    show({a['SvenSvenssen0']}, has(102) and not has(104))",
        "end",
        "",
    ]
    script.add(lines, (EV_NJAM_TRIGGER, "Njam's house", None),
               (rude_use_event(o["Hanndl1"]), "Hanndl", None), (rude_exit_event(o["Hanndl1"]), "Hanndl", None),
               (rude_exit_event(o["ShopkeeperHuman2MaleA0"]), "Jokull the Ugly", None),
               (rude_use_event(o["SvenSvenssen0"]), "Sven", None),
               (rude_exit_event(o["SvenSvenssen0"]), "Sven", None))

    script.add(gate_lines(dmap) + [""])

    lines = ["-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9)."]
    for k, (name, entry) in enumerate(scripted):
        event = EV_SCRIPTED_PROP + k
        kind = str(entry.get("script")).lower()
        params = str(entry.get("script_params") or "")
        if "bookletter" in kind:
            number = int("".join(ch for ch in params.split()[0] if ch.isdigit())[:3])
            title, text = letter(number)
            lines.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0); "
                         f"evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end   -- {name} ({number})")
            script.registrations.append((event, name, "Read", "event"))
        else:
            lines.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0) end"
                         f"   -- {name} (Book.scr: pages turn, no text)")
            script.registrations.append((event, name, "Book", "event"))
    script.add(lines + [""])

    load = [f"    show({a['SvenSvenssen0']}, has(102) and not has(104))   -- NPC3.scr :Init (Arslegard)",
            f"    if has({KEY_NJAM_DONE}) and var(\"NjamChase\") == 0 then MM9.removeActor({a['NjamtheMeddler0']}) end"
            "   -- NjamChase.scr :Init",
            f"    if var(\"NjamChase\") == 1 then evt.SetActorImmobile({a['NjamtheMeddler0']}, false) end"
            "   -- a chase saved before the release (njamChase)",
            f"    if has({KEY_NJAM_DONE}) then {opened(njam_cell)} end"]
    load.append(f"    if has({KEY_WRIT_DONE}) then MM9.removeActor({a['Hanndl']}) end   -- WritMan.scr :DeleteHanndl")
    lines = [
        *poll_lines(),
        f"handlers[{T_POLL}] = poll",
        f"handlers[{EV_LOAD}] = function()   -- map load",
        *load,
        "    poll()",
        "end",
    ]
    script.add(lines, (T_POLL, "Poll", None, "timer"), (EV_LOAD, "Map load", None))
    # NjamChase.scr :Main `OnDamage Chase`: a hit on Njam starts the chase.
    script.lines += [f"handlers[{EV_NJAM_DAMAGE}] = function(context) "
                     f"if context.actorIndex == {a['NjamtheMeddler0']} then njamChase() end end"]
    script.hooks.append(f'RegisterMonsterDamageHook({EV_NJAM_DAMAGE}, "Njam hurt", handlers[{EV_NJAM_DAMAGE}])')
    hooks.scenes = cinematic_scenes(hooks, build)
    return script.finish(on_load=[EV_LOAD]) + cutscenes.lua_block(hooks.scenes)


# --- the Great Gate scenes (FateMan.scr, WritMan.scr) as the cinematics gate_fate and gate_writ -----------------------
def gate_lines(dmap: str) -> list[str]:
    """FateMan.scr and WritMan.scr's :OnLose: the guards that start the cinematics (their steps: gate_cinematics.py)."""
    return [
        "-- The Great Gate scenes (FateMan.scr, WritMan.scr: both run their :OnLose on every arrival, `wait 1 .1 OnLose`)",
        "-- as the camera cinemas gate_fate and gate_writ (arslegardcity.cinematics.yml, gate_cinematics.py; their",
        "-- gameplay steps are the MM9Cinematic events at the end of this file, which also run on a skip).",
        f"-- FateMan.scr, once (without key {KEY_FATE}): Hanndl at the peephole sends the party for a Writ of Fate; key",
        f"-- {KEY_FATE}, 46 000 experience and `trigger ExitTrigger2`: the move to the Dark Passageway ({dmap}).",
        "local function fateMan()",
        f"    if has({KEY_FATE}) then return false end",
        f"    MM9Cinematic.start(\"{gate_cinematics.FATE_ID}\")",
        "    return true",
        "end",
        f"-- WritMan.scr: with the Writ shown (key {KEY_WRIT}) and not yet done ({KEY_WRIT_DONE}): key {KEY_WRIT_DONE},",
        "-- Hanndl reads it, 170 000 experience, Hanndl (the gate's actor) removed, the Great Gate unlocked and opened",
        "-- (it closes again after MM9's CloseWaitTime; a click opens it from then on). Done: Hanndl removed (map load).",
        "local function writMan()",
        f"    if not has({KEY_WRIT}) or has({KEY_WRIT_DONE}) then return end",
        f"    MM9Cinematic.start(\"{gate_cinematics.WRIT_ID}\")",
        "end",
    ]


def poll_lines() -> list[str]:
    return [
        "-- The gate scene starts as MM9's does, about 3 s after the arrival (`wait 1 .1 OnLose`, ScreenFadeOut 1, `wait 1",
        "-- 2 OnStart`): three polls. The cinematics begin at MM9's :OnStart.",
        "local arrivalPolls = 0",
        "local function poll()",
        "    arrivalPolls = arrivalPolls + 1",
        "    if arrivalPolls == 3 and not fateMan() then writMan() end",
        f"    evt.StartTimer({T_POLL}, seconds(1))",
        "end",
    ]


def cinematic_scenes(hooks, build) -> list:
    """gate_fate and gate_writ from the build (gate_cinematics.scenes; convert.py installs them)."""
    return gate_cinematics.scenes(build.movers, hooks.actor["Hanndl"], dark_passageway_arrival(),
                                  gate_cinematics.experience())


def hooks_group(name: str) -> int:
    from convert import GROUP_NJAM
    return {"njam": GROUP_NJAM}[name]
