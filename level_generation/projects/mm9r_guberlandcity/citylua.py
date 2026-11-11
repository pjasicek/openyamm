"""
Guberland City's map Lua: the doors (MM9's locked facade doors say so; the quarter gates open as the party walks up
to them), the scripted townsfolk and props as native handlers, each citing its .scr (README.md, "Scripted
objects": what each script does in MM9 and what is carried; the scripts are mm9/extracted/SCRIPTS/SCRIPTS/*.scr).

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h; the handler ends by opening the dialogue itself).
"""

from __future__ import annotations

import csv
import json

from dungeon import town_portal
from dungeon.objects import bonus_call
from dungeon.source import ROOT, SCALE
from quest_xp import balanced_experience, experience_note

LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
EV_LOAD, EV_LOCKED, EV_SICKROOM = 1, 230, 231
T_POLL, T_GATES, T_PLAY = 260, 261, 262
PLAY_SCRIPT = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS/THEPLAY.scr"
PLAY_VOICES = ROOT / "assets_dev/worlds/mm9/audio/voices/cinema/guberlandplay"
PLAY_STARTS = (14 * 60 + 30, 16 * 60 + 30)      # Narrator.scr: @m 14:30 and 16:30 OnStart
PLAY_CURTAIN_SECONDS = 2                       # Narrator.scr :OnStart: the curtain opens, 2 s, the first line
PLAY_BOW_SECONDS = 5                           # Narrator.scr :Bow .. :Exit: the bow, then the curtain closes
T_CUE = 263                                    # the players' cues (play_cues)
EV_ARRIVE = 270                                # + k: PLAYERS[k] arrives where a cue sent him
EV_PRIZE = 250                                 # Markel's awards picked up (Prize0-5, dungeon/pickups.py)
PRIZES = tuple(f"Prize{n}" for n in range(6))
PLAYERS = ("Narrator", "Wilam", "Trislan", "Abriel", "Ralof", "Leffery")
PLAY_MARKS = ("Trislan1", "Trislan2", "Trislan3", "Abriel1", "Abriel2", "Abriel3", "Abriel4", "Ralof1", "Ralof2",
              "Ralof3", "Wilam1", "Wilam2", "Wilam3", "Wilam4", "Leffery1", "Leffery2", "Leffery3", "peasant2")
EV_SCRIPTED_PROP = 330              # letters, the book, the town portal altar, the well: + k
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr", "townportal.scr")
SCRIPTED_PROP_NAMES = ("Well0",)
LOCATION_KEY = 1028                 # ForadWorld.scr "Guberland"
TOWN_PORTAL_KEY = 5014              # TownPortal.scr "Guberland"
MARKEL_CLAN_KEYS = (82, 38, 51, 34, 74)   # United.inc :MarkelInit
BANK_KEY, BANK_KEY2 = 332, 326      # BankOrb.scr :Init, RUDE 140 (Ottar Gizurssen): nKey, nKey2
GATES = ("Gate1", "Gate2", "Gate3", "Gate4", "Gate5", "Gate6", "Gate7", "Gate8")
BARS_TEXTURE = "metalbar.dtx"

# MM9 doors with Locked 1, MoveDist 0 and no key, script or trigger that unlocks them: every linear `Door` of the city
# (the facades; three of them, Door27, Door30 and Door32, have a room behind them). A click says the door is locked.
LOCKED_GROUPS = [f"Door{n}" for n in range(0, 33)] + ["RotatingDoor12", "RotatingDoor13"]
SICKROOM_DOOR = "RotatingDoor3"     # Nurtigan's sickroom (Locked 1): NPC142.scr unlocks it with the potion (key 373)


def locked_groups(build) -> list:
    """The locked groups that exist in this DAT (the list above is a superset)."""
    return sorted({m["group"] for m in build.movers if m["group"] in set(LOCKED_GROUPS)})


# Movers that are no doorway but open on a click: the tavern's bar flap (Sticky) and the stage curtain (MM9's
# Narrator.scr raises it for the Guberland Players' show at 14:30 and 16:30; the show is not carried: README).
TOGGLE_GROUPS = {"Bar": 240, "Curtain": 241}
MOVER_EVENTS = {**{group: (EV_LOCKED, "click") for group in LOCKED_GROUPS}, SICKROOM_DOOR: (EV_SICKROOM, "click"),
                **{group: (event, "click") for group, event in TOGGLE_GROUPS.items()}}


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


def scripted_props(build) -> list:
    """props.json's scripted props in file order: [(name, entry)]."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    return [(e["source_name"], e) for e in entries
            if e["source_name"] in SCRIPTED_PROP_NAMES
            or str(e.get("script") or "").lower().replace("scripts\\", "") in SCRIPTED_PROP_SCRIPTS]


def prop_events(build) -> dict:
    events = {name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted_props(build))}
    return {**events, **{name: EV_PRIZE for name in PRIZES}}


def prop_cogs(build) -> dict:
    return {}


def marker_points(build) -> dict:
    return {}


def gate_boxes(build) -> list:
    """The quarter gates' trigger boxes (Gate<n>trigger: Pos +- Dims, LithTech) in native x/y, grown by the party's
    radius (the native party is a 37-unit cylinder; MM9 tests its box)."""
    boxes = []
    for gate in GATES:
        o = build.source.by_name[f"{gate.lower()}trigger"]
        p, d = o["properties"]["Pos"], o["properties"]["Dims"]
        grow = 40
        boxes.append((gate, round((p[0] - d[0]) * SCALE - grow), round((p[0] + d[0]) * SCALE + grow),
                      round((p[2] - d[2]) * SCALE - grow), round((p[2] + d[2]) * SCALE + grow)))
    return boxes


def bars_cutout(build, blv, scene) -> None:
    """The bank counter's bars (WorldObject1's MetalBar, made untouchable TRIGGER_nonsolid_ faces in convert.py) as a
    two-sided cut-out: found in the compiled BLV by texture (The Arena's route)."""
    alias = next(entry["alias"] for name, entry in build.source.aliases.items() if name.endswith(BARS_TEXTURE))
    bars = sorted(f["index"] for f in blv["faces"] if not f["is_portal"] and f["texture_name"] == alias)
    if bars:
        scene.setdefault("translucent_faces", []).append({"faces": bars, "opacity": 1.0, "tint": [1.0, 1.0, 1.0],
                                                          "two_sided": True})
    build.stats["bar_faces"] = len(bars)


def map_script(hooks, build) -> str:
    from dungeon import lua
    script = lua.Script(build, "Guberland City")
    # The DOORS table keys every leaf as a string (Thjorgard City: MM9 leaf names need not be Lua identifiers).
    assert script.lines[4].startswith("local DOORS = {")
    script.lines[4] = "local DOORS = {" + ", ".join(f'["{k}"] = {v}' for k, v in sorted(script.door.items())) + "}"
    script.doors()
    script.chests()
    a, o = hooks.actor, hooks.objects
    locked = locked_groups(build)

    def item(verb, number, who):
        return f"MM9.{verb}Item({number}, \"guberlandcity:{who}\")"

    lines = [
        "local function has(k) return MM9.hasKey(k) == 1 end",
        "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; "
        "if gold > 0 then MM9.giveGold(gold) end; quest() end",
        "-- GivePromo <class>: every eligible member at once (MM9.promoteParty: the quest -> class-line table; MM9's",
        "-- per-character keys are not used: devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md \"Promotions And Classes\")",
        "local function promote(class, first) MM9.promoteParty(class) end",
        "",
        f"-- MM9's locked doors (Locked 1, no key): the {len(locked)} facade doors and the two locked smithy doors.",
        f"handlers[{EV_LOCKED}] = function()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        f"-- {SICKROOM_DOOR}: Nutty Nurtigan's sickroom (Locked 1, Sticky). NPC142.scr unlocks it when the apothecary",
        "-- hands over the potion (key 373); NPC131.scr opens it once he is cured (key 211).",
        f"handlers[{EV_SICKROOM}] = function()",
        f"    if has(373) or has(211) then evt.SetDoorState(DOORS[\"{SICKROOM_DOOR}\"], DoorAction.Trigger)",
        f"    else handlers[{EV_LOCKED}]() end",
        "end",
        "",
        f"-- ForadWorld.scr (ScriptObject0, \"Guberland\"): key {LOCATION_KEY} is the party's location while here (keys",
        "-- 1024-1033 are the towns'); key 5017 closes the shops from 20:00 to 06:00 (their dialogues forbid or require it).",
        "local function shopHours()",
        "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
        "    local closed = hour >= 20 or hour < 6",
        "    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end",
        "end",
        "",
    ]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"), (EV_SICKROOM, "Sickroom door", "Door"))
    toggles = ["-- The bar's flap and the stage curtain: a click opens or shuts them."]
    for group, event in TOGGLE_GROUPS.items():
        leaves = [m["node"][5:] for m in build.movers if m["group"] == group]
        calls = " ".join(f"evt.SetDoorState(DOORS[\"{leaf}\"], DoorAction.Trigger)" for leaf in leaves)
        toggles.append(f"handlers[{event}] = function() {calls} end   -- {group}")
    script.add(toggles + [""], *[(event, group, "Door") for group, event in TOGGLE_GROUPS.items()])

    # --- the quarter gates ------------------------------------------------------------------------------------------
    boxes = gate_boxes(build)
    lines = [
        "-- The eight quarter gates (Gate<n>L/R, linear Doors sliding 120 LT): MM9's Gate<n>trigger boxes (128 LT each way",
        "-- round the gate) toggle the pair once (and turn themselves off); here a 0.25 s poll opens a shut gate whenever",
        "-- the party stands in its box. A click toggles a gate as any door.",
        "local GATES = {" + ", ".join(f'{{"{g}", {x0}, {x1}, {y0}, {y1}}}' for g, x0, x1, y0, y1 in boxes) + "}",
        "local function gates()",
        "    local x, y = evt.GetPartyPosition()",
        "    for _, g in ipairs(GATES) do",
        "        if x >= g[2] and x <= g[3] and y >= g[4] and y <= g[5] then",
        "            if var(g[1] .. \"Open\") == 0 then",
        "                set(g[1] .. \"Open\", 1)",
        "                open(g[1] .. \"L\"); open(g[1] .. \"R\")",
        "            end",
        "        elseif var(g[1] .. \"Open\") == 1 then",
        "            set(g[1] .. \"Open\", 0)   -- re-armed once the party has left the box",
        "        end",
        "    end",
        "end",
        f"handlers[{T_GATES}] = function() gates(); evt.StartTimer({T_GATES}, seconds(0.25)) end",
        "",
    ]
    script.add(lines, (T_GATES, "Gates", None, "timer"))

    # --- townsfolk -------------------------------------------------------------------------------------------------
    lines = [
        f"-- BankOrb.scr (Ottar Gizurssen, RUDE 140: nKey {BANK_KEY}, nKey2 {BANK_KEY2}): the Orb of Linking. A click with the",
        "-- orb (item 252) after the quest (key 322) unlocks the row that installs it (key 330); the exit places it and the",
        "-- sixth bank's orb pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).",
        f"handlers[{rude_use_event(o['ShopkeeperHuman2MaleA7'])}] = function()",
        f"    if not has({BANK_KEY2}) and has(322) and {item('has', 252, 'Ottar')} == 1 then MM9.giveKey(330) end",
        "    MM9.openRude(140)",
        "end",
        f"handlers[{rude_exit_event(o['ShopkeeperHuman2MaleA7'])}] = function()",
        "    if not has(330) then return end",
        "    MM9.takeKey(330)",
        f"    if not has({BANK_KEY}) then return end",
        f"    quest(); {item('take', 252, 'Ottar')}; MM9.giveKey({BANK_KEY2})",
        "    if has(337) then return end",
        "    for k = 331, 336 do if not has(k) then return end end",
        f"    reward(337, {balanced_experience(20000, 337)}, 15000){experience_note(20000, 337)}",
        "end",
        "",
        "-- NPC127.scr (Markel the Great, the Jarl, RUDE 127; United.inc). The click: the five clans (82, 38, 51, 34, 74",
        "-- -> 178). The exit: the Book of Rules (61 -> 167, 10 000 experience, 3 000 gold, item 391 taken), Ivan the Smart",
        "-- (62 -> 165, 26 000, 3 000, item 400 taken), the Dook (66 -> 168, 40 000, 3 000), the clans united (83 -> 179,",
        "-- 26 500, 6 000). Hidden on 40 unless 108.",
        f"handlers[{rude_use_event(o['MarkeltheGreat0'])}] = function()",
        "    if not has(178) then",
        "        local n = 0",
        "        for _, k in ipairs({" + ", ".join(str(k) for k in MARKEL_CLAN_KEYS) + "}) do if has(k) then n = n + 1 end end",
        "        if n == 5 then MM9.giveKey(178) end",
        "    end",
        "    MM9.openRude(127)",
        "end",
        f"handlers[{rude_exit_event(o['MarkeltheGreat0'])}] = function()",
        f"    if not has(167) and has(61) then reward(167, {balanced_experience(10000, 167)}, 3000); "
        f"{item('take', 391, 'Markel')} end",
        f"    if not has(165) and has(62) then reward(165, {balanced_experience(26000, 165)}, 3000); "
        f"{item('take', 400, 'Markel')} end{experience_note(26000, 165)}",
        f"    if not has(168) and has(66) then reward(168, {balanced_experience(40000, 168)}, 3000) end"
        f"{experience_note(40000, 168)}",
        f"    if not has(179) and has(83) then MM9.giveKey(179); "
        f"MM9.giveExperience({balanced_experience(26500, 179)}); MM9.giveGold(6000) end{experience_note(26500, 179)}",
        "end",
        "",
        "-- NPC128.scr (Tjolnir the Super-neat, RUDE 128): Initiate to Healer. :Promocheck: a character holding 437-440",
        "-- gives 206 (MM9's engine set those keys from the class check of \"We are seeking promotion from Initiate to",
        "-- Healer\", code 2083, kept as key 2083; here: that row asked, whoever is in the party: every promotion quest is",
        "-- offered to any party, the user 2026-11-08, dialogue/promotions.yml). With Nurtigan cured (212) and not 213:",
        "-- 24 500 experience, 1 000 gold, key 213, the promotion of the members eligible.",
        f"handlers[{rude_exit_event(o['ShopkeeperHuman2MaleA1'])}] = function()",
        "    if not has(206) and has(2083) then MM9.giveKey(206) end",
        f"    if not has(213) and has(212) then reward(213, {balanced_experience(24500, 213)}, 1000); "
        f"promote(\"Healer\", 437) end{experience_note(24500, 213)}",
        "end",
        "",
        "-- NPC129.scr (Gray Slemnir, RUDE 129): Healer to Priest. :Givequest: a character holding 441-444 gives the quest",
        "-- keys 250, 251, 252 (the class check of \"We are seeking promotion\", code 2084, kept as key 2084; here: that",
        "-- row asked, whoever is in the party). With 260 and not 261: 63 000 experience, 5 000 gold, key 261, items 241",
        "-- and 430 taken, the promotion of the members eligible.",
        f"handlers[{rude_exit_event(o['ShopkeeperHuman2MaleA2'])}] = function()",
        "    if not has(250) and has(2084) then",
        "        MM9.giveKey(250); MM9.giveKey(251); MM9.giveKey(252)",
        "    end",
        "    if not has(261) and has(260) then",
        f"        reward(261, {balanced_experience(63000, 261, 'npc129.scr', 'priest')}, 5000); "
        f"{item('take', 241, 'Gray')}; {item('take', 430, 'Gray')}"
        f"{experience_note(63000, 261, 'npc129.scr', 'priest')}",
        "        promote(\"Priest\", 441)",
        "    end",
        "end",
        "",
        "-- NPC141.scr (the tavern keeper, RUDE 141): the keg delivered (304, not 306): key 306, item 249 taken, 500 gold,",
        "-- 5 000 experience.",
        f"handlers[{rude_exit_event(o['ShopkeeperHalfOrcFemaleA'])}] = function()",
        f"    if not has(306) and has(304) then reward(306, {balanced_experience(5000, 306)}, 500); "
        f"{item('take', 249, 'Tavern')} end",
        "end",
        "",
        "-- NPC142.scr (Skarphedinn Njalssen, the apothecary, RUDE 142). The click: with item 240 and key 206, key 207.",
        "-- The exit: with 208 item 240 is taken and the potion is ready two game hours later (key 209); with 210 and not",
        f"-- 373 the sickroom door ({SICKROOM_DOOR}) is unlocked, item 558 given, key 373.",
        f"handlers[{rude_use_event(o['ShopkeeperHuman2MaleA8'])}] = function()",
        f"    if {item('has', 240, 'Skarphedinn')} == 1 and has(206) then MM9.giveKey(207) end",
        "    MM9.openRude(142)",
        "end",
        f"handlers[{rude_exit_event(o['ShopkeeperHuman2MaleA8'])}] = function()",
        "    if has(208) and not has(209) and var(\"PotionReadyAt\") == 0 then",
        f"        {item('take', 240, 'Skarphedinn')}",
        "        set(\"PotionReadyAt\", math.floor(evt.CurrentGameMinutes()) + 120)",
        "    end",
        "    if has(210) and not has(373) then",
        f"        {item('give', 558, 'Skarphedinn')}; MM9.giveKey(373); quest()",
        "    end",
        "end",
        "",
        "-- NPC131.scr (Nutty Nurtigan, RUDE 131, in his sickroom): cured (211) with the potion (item 558) on the dialogue's",
        "-- close, the potion is taken and he leaves the sickroom (MM9 walks him to Marker0 and wanders; here the door",
        "-- opens and he stays). On load with 211 the door stands open.",
        f"handlers[{rude_exit_event(o['CommonerHumanMaleA0'])}] = function()",
        f"    if has(211) and {item('has', 558, 'Nurtigan')} == 1 then",
        f"        {item('take', 558, 'Nurtigan')}; open(\"{SICKROOM_DOOR}\")",
        "    end",
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
    lines += [""]
    script.add(lines,
               (rude_use_event(o["ShopkeeperHuman2MaleA7"]), "Ottar Gizurssen", None),
               (rude_exit_event(o["ShopkeeperHuman2MaleA7"]), "Bank", None),
               (rude_use_event(o["MarkeltheGreat0"]), "Markel the Great", None),
               (rude_exit_event(o["MarkeltheGreat0"]), "Markel", None),
               (rude_exit_event(o["ShopkeeperHuman2MaleA1"]), "Tjolnir", None),
               (rude_exit_event(o["ShopkeeperHuman2MaleA2"]), "Gray Slemnir", None),
               (rude_exit_event(o["ShopkeeperHalfOrcFemaleA"]), "Tavern keeper", None),
               (rude_use_event(o["ShopkeeperHuman2MaleA8"]), "Skarphedinn", None),
               (rude_exit_event(o["ShopkeeperHuman2MaleA8"]), "Skarphedinn", None),
               (rude_exit_event(o["CommonerHumanMaleA0"]), "Nurtigan", None),
               *[(f(o[n]), "Thorolf", None) for n in ("Thorolf0", "Thorolf1") for f in (rude_use_event, rude_exit_event)])

    # --- scripted props --------------------------------------------------------------------------------------------
    lines = ["-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr (no text in MM9), TownPortal.scr, the well."]
    altar_load = []          # TownPortal.scr :Init (the map load shows the clean altar)
    for k, (name, entry) in enumerate(scripted_props(build)):
        event = EV_SCRIPTED_PROP + k
        kind = str(entry.get("script") or "").lower()
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
        elif name in SCRIPTED_PROP_NAMES:
            lines += [f"-- {name}: MM9's WellMMIX, its class's use (dungeon/objects.py bonus_call).",
                      f"handlers[{event}] = function() {bonus_call(build, name)} end"]
            script.registrations.append((event, name, "Well", "event"))
        else:
            lines.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0) end"
                         f"   -- {name} (Book.scr: pages turn, no text)")
            script.registrations.append((event, name, "Book", "event"))
    script.add(lines + [""])

    # --- Markel's awards ------------------------------------------------------------------------------------------
    lines = [
        "-- Markel's awards (Prize0-5 on the shelf of his hall; Sign4: \"Awards Won by Markel ... at The Gathering\"): the",
        "-- Thing's Stuffed Dragon (item 395). MM9 has them as set dressing; here they are world items taken once Markel is",
        "-- dead (key 40, dungeon/pickups.py), an OpenYAMM way past the Thing's games on Yrsa's errand: the first taken",
        "-- while the errand runs (93, not 94) counts as the prize won (94: Bikki takes it, the Jarls leave the council).",
        "-- No experience: the Thing's 10 000 is for winning its games.",
        f"handlers[{EV_PRIZE}] = function()",
        "    if has(93) and not has(94) then",
        "        MM9.giveKey(94); quest()",
        "        evt.StatusText(\"Markel the Great will not miss one of his prizes.\")",
        "    end",
        "end",
        "",
    ]
    script.add(lines, (EV_PRIZE, "Markel's awards", None))

    # --- the Guberland Players' show -----------------------------------------------------------------------------
    script.add(play_cues(build, hooks) + [""], (T_CUE, "The players' cues", None, "timer"),
               *[(EV_ARRIVE + k, f"{name} arrives", None) for k, name in enumerate(PLAYERS)])
    script.add(play_lines(build, a) + [""], (T_PLAY, "The play", None, "timer"))

    # --- map load and the poll -------------------------------------------------------------------------------------
    load = [
        f"    show({a['MarkeltheGreat0']}, (not has(40)) or has(108))   -- NPC127.scr :Init (gone on 40 unless 108)",
        f"    show({a['ShopkeeperHuman2MaleA12']}, not has(457))   -- Retainer.scr (457): hidden while hired",
        f"    show({a['ShopkeeperHuman2MaleA13']}, not has(459))   -- Retainer.scr (459): hidden while hired",
        "    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)",
        f"    show({a['Thorolf0']}, thorolf); show({a['Thorolf1']}, thorolf)",
        f"    if has(211) then open(\"{SICKROOM_DOOR}\") end   -- NPC131.scr :Init: Nurtigan cured, the door open",
    ]
    load += altar_load
    lines = [
        "local function poll()",
        "    shopHours()",
        "    playSchedule()",
        "    local ready = var(\"PotionReadyAt\")   -- NPC142.scr :Givekey (@m two hours after the order)",
        "    if ready > 0 and evt.CurrentGameMinutes() >= ready then set(\"PotionReadyAt\", 0); MM9.giveKey(209) end",
        f"    evt.StartTimer({T_POLL}, seconds(1))",
        "end",
        f"handlers[{T_POLL}] = poll",
        f"handlers[{EV_LOAD}] = function()   -- map load",
        f"    for k = 1024, 1033 do if k ~= {LOCATION_KEY} and has(k) then MM9.takeKey(k) end end",
        f"    MM9.giveKey({LOCATION_KEY})",
        *load,
        "    if var(\"PlayLine\") > 0 then set(\"PlayLine\", 0); playCurtain(false); playersHome() end   -- a show left"
        " half-way",
        "    poll()",
        f"    handlers[{T_GATES}]()",
        "end",
    ]
    script.add(lines, (T_POLL, "Poll", None, "timer"), (EV_LOAD, "Map load", None))
    return script.finish(on_load=[EV_LOAD])


def play_timeline() -> list[tuple[str, str, float]]:
    """The play's lines in order: (voice file, speaker, seconds to the next line), from THEPLAY.scr (MM9's linear
    timeline of "The Death of Emperor Trislan": each label plays its line at its speaker's handle and waits the
    sound's duration, adjusted by Add/Subtract, before the next label). The durations are the voice files'."""
    import re
    import wave
    text = PLAY_SCRIPT.read_text(encoding="latin-1").replace("\r", "")
    labels = {m.group(1).lower(): m.group(2) for m in re.finditer(r"^:(\w+)\n(.*?)(?=^:\w|\Z)", text, re.M | re.S)}
    out, label, seen = [], "onblabber", set()
    while label in labels and label not in seen:
        seen.add(label)
        body = labels[label]
        played = re.search(r"playsoundhandle\s+voices\\cinema\\guberlandplay\\(\w+\.wav)\s*,\s*(\w+)handle", body, re.I)
        following = re.search(r"wait\s+1\s+sounddur\s*,\s*(\w+)", body, re.I)
        if not played or not following:
            break
        name, speaker = played.group(1).lower(), played.group(2).lower()
        with wave.open(str(PLAY_VOICES / name)) as sound:
            seconds = sound.getnframes() / sound.getframerate()
        for sign, amount in re.findall(r"^\s*(add|subtract)\s+sounddur\s*,\s*([\d.]+)", body, re.I | re.M):
            seconds += float(amount) if sign.lower() == "add" else -float(amount)
        out.append((name, speaker, round(max(seconds, 0.5), 2)))
        label = following.group(1).lower()
    return out


# MM9 plays the show as a chain of messages between the six players' scripts (Narrator.scr, Trislan.scr, Abriel.scr,
# Wilam.scr, Ralof.scr, Leffery.scr): each line is played by its speaker's handler of a message (or of a walk's arrival
# after one) and that handler's wait sends the next. A dead AI takes no message (devdocs/mm9_rework/scr_audit/README.md
# "Implicit engine semantics"), so a dead player ends the show at his first line: per line, the messages (DAT name,
# message) that must reach a living receiver for it to play. 01, 02 and 28 come from the Narrator's own @m and waits.
# Ralof's :Trigger14 sends Speak14 to Leffery and Abriel at once: Leffery's 14 drives nothing (PLAY_SIDE_LINES),
# Abriel's chain goes on to 15.
PLAY_MESSAGES = {
    "03.wav": (("Trislan", "Walk1"),), "04.wav": (("Abriel", "Speak4"),), "05.wav": (("Trislan", "Speak5"),),
    "06.wav": (("Abriel", "Speak6"),), "07.wav": (("Trislan", "Speak7"),), "08.wav": (("Abriel", "Speak8"),),
    "09.wav": (("Narrator", "Speak9"),), "10.wav": (("Wilam", "Speak9"),), "11.wav": (("Ralof", "Speak11"),),
    "12.wav": (("Leffery", "Speak12"),), "13b.wav": (("Ralof", "Speak13"),), "14.wav": (("Leffery", "Speak14"),),
    "15.wav": (("Abriel", "Speak14"),), "16.wav": (("Ralof", "Speak16"),), "17.wav": (("Abriel", "Speak17"),),
    "18.wav": (("Ralof", "Speak18"),), "19.wav": (("Abriel", "Speak19"),), "20.wav": (("Ralof", "Speak20"),),
    "21.wav": (("Narrator", "Speak21"),),
    "22.wav": (("Abriel", "Exit"), ("Narrator", "Speak22")),        # Abriel's exit walk ends with :FaceStage's Speak22
    "23.wav": (("Ralof", "Walk2"), ("Trislan", "Speak23")),         # Ralof's walk to Trislan ends with :Trigger23
    "24.wav": (("Ralof", "Speak24"),), "25.wav": (("Trislan", "Speak25"),), "26.wav": (("Ralof", "Speak26"),),
    "27a.wav": (("Trislan", "Die"),), "27.wav": (("Narrator", "Speak27"),),
}
PLAY_OWN_LINES = ("01.wav", "02.wav", "28.wav")
PLAY_SIDE_LINES = ("14.wav",)


def play_gate(name: str, actors: dict) -> str:
    """A PLAY row's gate fields: its messages as {DAT name, actor, message} and whether a dropped one ends the show."""
    if name in PLAY_OWN_LINES:
        return ""
    if name not in PLAY_MESSAGES:
        raise SystemExit(f"THEPLAY.scr line {name}: no PLAY_MESSAGES entry")
    to = ", ".join(f"{{\"{who}\", {actors[who]}, \"{message}\"}}" for who, message in PLAY_MESSAGES[name])
    return f", to = {{{to}}}" + (", side = true" if name in PLAY_SIDE_LINES else "")


def play_lines(build, actors: dict) -> list[str]:
    """The Guberland Players' show's voices (README "The Players' show"): at 14:30 and 16:30 (Narrator.scr) the
    curtain opens and the 28 lines of THEPLAY.scr's timeline play at their speakers' places on the stage; the curtain
    closes after the bow. The actors' walks and animations (Narrator.scr and the five actors' scripts, which chain
    the same lines by their animation keys) are play_cues'. A dead player ends the show at his first line, the curtain
    left open (PLAY_MESSAGES). actors: DAT name -> map actor (hooks.actor)."""
    timeline = play_timeline()
    at = {name: ", ".join(str(int(round(v))) for v in build.project.native(build.source.properties(name)["Pos"]))
          for name in {speaker for _, speaker, _ in timeline}}
    rows = [f"    {{\"voices/cinema/guberlandplay/{name}\", {at[speaker]}, {seconds:g}{play_gate(name, actors)}}},"
            f"   -- {speaker}" for name, speaker, seconds in timeline]
    curtain = " ".join(f"evt.SetDoorState(DOORS[\"{m['node'][5:]}\"], open and DoorAction.Open or DoorAction.Close)"
                       for m in build.movers if m["group"] == "Curtain")
    starts = ", ".join(f"[{minute}] = true" for minute in PLAY_STARTS)
    return [
        "-- The Guberland Players' show (Narrator.scr @m 14:30 and 16:30; the lines and their timing from THEPLAY.scr):",
        "-- the curtain opens, each line plays at its speaker's place on the stage, the curtain closes after the bow.",
        "-- PlayLine: the next line (0: no show); PlayDue guards the repeating timer. A row's `to`: the players'",
        "-- messages that must reach a living receiver (MM9.receives) for it to play; else the show stops there, the",
        "-- curtain open (MM9's chain never reaches the Narrator's :Exit), except a `side` line, which stays silent.",
        "local PLAY = {", *rows, "}",
        "local function playReaches(line)",
        "    for _, m in ipairs(line.to or {}) do",
        "        if not MM9.receives(\"guberlandcity\", m[1], m[3], m[2]) then return false end",
        "    end",
        "    return true",
        "end",
        f"local PLAY_STARTS = {{{starts}}}",
        f"local function playCurtain(open) {curtain} end",
        "local function playNext(delay)",
        "    set(\"PlayDue\", 1)",
        f"    evt.StartTimer({T_PLAY}, seconds(delay))",
        "end",
        f"handlers[{T_PLAY}] = function()",
        f"    evt.StopTimer({T_PLAY})",
        "    if var(\"PlayDue\") ~= 1 then return end",
        "    set(\"PlayDue\", 0)",
        "    local i = var(\"PlayLine\")",
        "    if i < 1 then return end",
        "    if i > #PLAY then set(\"PlayLine\", 0); playCurtain(false) return end   -- the bow is over",
        "    local line = PLAY[i]",
        "    if playReaches(line) then evt.PlaySoundName(line[1], line[2], line[3], line[4])",
        "    elseif not line.side then set(\"PlayLine\", 0) return end",
        "    set(\"PlayLine\", i + 1)",
        f"    playNext(i < #PLAY and line[5] or line[5] + {PLAY_BOW_SECONDS})",
        "end",
        "local function playSchedule()",
        "    local now = math.floor(evt.CurrentGameMinutes())",
        "    if PLAY_STARTS[now % 1440] and var(\"PlayLine\") == 0 and var(\"PlayStartedAt\") ~= now then",
        "        set(\"PlayStartedAt\", now)",
        "        set(\"PlayShows\", var(\"PlayShows\") + 1)",
        "        set(\"PlayLine\", 1)",
        "        playCurtain(true)",
        f"        playNext({PLAY_CURTAIN_SECONDS})",
        f"        playCues({PLAY_CURTAIN_SECONDS})",
        "    end",
        "end",
    ]



def play_cues(build, hooks) -> list[str]:
    """The players' walks, faces and clips during the show (Narrator.scr, Trislan.scr, Abriel.scr, Wilam.scr,
    Ralof.scr, Leffery.scr), as cues on THEPLAY.scr's timeline (play_timeline): each line's speaker loops his conv
    clip while it plays (LoopAnim conv<n>, then Stop and LoopAnim stand), the players walk to their markers and face
    whom MM9 targets, Abriel slaps Ralof, Ralof slaps Trislan, who dies and gets up (Play_Death, Play_getup), the cast
    lines up facing the audience (peasant2) and bows, and walks off after the bow. MM9 starts some of these on a
    walk's arrival or a wait inside a line: here at the same offsets from the line's start. A walk ends a body's
    width short of its point (ScriptedActorMoveArrivalDistance), so a walk to another player (MM9's walkto <player>)
    stops in front of him. A clip a player's model
    lacks takes another conv clip, or is left out (Ralof has no bow, Leffery no Aware). The cues run on their own
    timer from the show's start (playCues) and stop with the show (PlayLine 0)."""
    from dungeon.lua import model_clip_seconds
    native = build.project.native
    players = hooks.players
    roles = {name: set(model_clip_seconds(players[name]["monster_id"])) for name in PLAYERS}

    def mark(name: str) -> list[int]:
        p = build.source.properties(name)["Pos"]
        floor = build.content.floor_at(p[0], p[2], p[1] + 16)
        return [int(round(v)) for v in native([p[0], floor if floor is not None else p[1], p[2]])]

    marks = {name: mark(name) for name in PLAY_MARKS}

    def clip(who: str, role: str) -> str | None:
        if role in roles[who]:
            return role
        if role.startswith("conv"):
            return next((c for c in ("conv1", "conv2", "conv3", "conv4", "talk") if c in roles[who]), None)
        return None

    def loop(who, role):
        found = clip(who, role)
        return f'loop("{who}", "{found}")' if found else None

    def stop(who):
        return f'stop("{who}")'

    def face(who, target):
        return f'face("{who}", "{target}")'

    def once(who, *chain, then=None):
        clips = [c for c in (clip(who, r) for r in chain) if c]
        last = clip(who, then) if then else None
        if not clips:
            return None
        names = ", ".join(f'"{c}"' for c in clips + ([last] if last else []))
        return f'evt.PlayActorClip(P.{who}, {{{names}}}, {"true" if last else "false"})'

    def walk(who, target, *arrival):
        body = "; ".join(a for a in arrival if a)
        return f'walk("{who}", "{target}", function() {body} end)' if body else f'walk("{who}", "{target}")'

    def sound(name, who):
        return f'sound("{name}", "{who}")'

    timeline = play_timeline()
    names = [name for name, _, _ in timeline]
    starts, t = {}, 0.0
    for name, _, seconds in timeline:
        starts[name] = t
        t += seconds
    end = t + PLAY_BOW_SECONDS
    # (line, seconds after its start, actions): MM9's scripts by label, cited.
    cues = [
        ("01.wav", 0, [loop("Narrator", "conv2")]),                                   # Narrator :OnStart2
        ("02.wav", 0, [loop("Narrator", "conv3"), face("Narrator", "Abriel1"),         # Narrator :TriggerStart
                       walk("Trislan", "Trislan1", face("Trislan", "Abriel")),         # Trislan :OnWalk1
                       walk("Abriel", "Abriel1", face("Abriel", "Trislan"))]),         # Abriel :OnWalk1
        ("03.wav", 0, [stop("Narrator"), loop("Trislan", "conv1")]),                  # Trislan :OnSpeak1
        ("04.wav", 0, [stop("Trislan"), loop("Abriel", "conv2")]),                    # Abriel :OnSpeak4
        ("05.wav", 0, [stop("Abriel"), loop("Trislan", "conv3")]),
        ("06.wav", 0, [stop("Trislan"), loop("Abriel", "conv2")]),
        ("07.wav", 0, [stop("Abriel"), loop("Trislan", "conv3")]),
        ("08.wav", 0, [stop("Trislan"), loop("Abriel", "conv2")]),
        ("09.wav", 0, [stop("Abriel"), loop("Narrator", "conv3"),                     # Narrator :OnSpeak9: Exit, Start
                       walk("Trislan", "Trislan2", face("Trislan", "Wilam")),
                       walk("Abriel", "Abriel2", face("Abriel", "Wilam")),
                       walk("Ralof", "Ralof1", face("Ralof", "Wilam")),
                       walk("Wilam", "Wilam1"),
                       walk("Leffery", "Leffery1", face("Leffery", "Ralof"))]),
        ("09.wav", 4, [stop("Narrator")]),                                            # Narrator :Trigger9
        ("10.wav", 0, [loop("Wilam", "conv2")]),                                      # Wilam :OnSpeak9
        ("10.wav", 1, [walk("Wilam", "Wilam2", face("Wilam", "Ralof"), loop("Wilam", "conv3"))]),   # :Walkto
        ("11.wav", 0, [stop("Wilam"), face("Ralof", "Wilam"), loop("Ralof", "conv1")]),            # Ralof :OnSpeak11
        ("12.wav", 0, [stop("Ralof"), loop("Leffery", "conv2")]),                     # Leffery :OnSpeak12
        ("13b.wav", 0, [stop("Leffery"), face("Ralof", "Leffery"), loop("Ralof", "conv1")]),       # Ralof :OnSpeak13
        ("13b.wav", 5, [face("Ralof", "Wilam"), loop("Ralof", "conv2")]),             # :FaceWilam, :converse
        ("14.wav", 0, [stop("Ralof"), stop("Wilam"),                                  # Ralof :Trigger14; Wilam :OnAttention
                       walk("Abriel", "Ralof", face("Abriel", "Ralof"),               # Abriel :OnSpeak14, :OnSlap
                            once("Abriel", "attack_melee", then="conv2"),             # (attack, then :speak15's conv2)
                            once("Ralof", "hit"), sound("weapons/fleshhit03.wav", "Ralof"))]),   # :Slapsound, wince
        ("20.wav", 0, [stop("Abriel"), loop("Ralof", "conv1")]),                      # Abriel :Trigger20; Ralof :OnSpeak20
        ("21.wav", 0, [stop("Ralof"), loop("Narrator", "conv1")]),                    # Narrator :OnSpeak21
        ("21.wav", 4, [stop("Narrator"),                                              # Narrator :Trigger22: exit
                       walk("Abriel", "Abriel2", face("Abriel", "Wilam")),
                       walk("Ralof", "Ralof2", face("Ralof", "Trislan")),
                       walk("Wilam", "Wilam3", face("Wilam", "Trislan")),
                       walk("Leffery", "Leffery2", face("Leffery", "Trislan"))]),
        ("22.wav", 0, [loop("Narrator", "conv1"),                                     # Narrator :OnSpeak22
                       walk("Trislan", "Trislan1", face("Trislan", "Ralof"))]),       # Trislan :OnWalk2
        ("22.wav", 1, [walk("Abriel", "Abriel3", face("Abriel", "Ralof"))]),          # :Abrielwalk
        ("22.wav", 5.5, [walk("Ralof", "Trislan", face("Ralof", "Trislan"))]),        # :Trigger23
        ("22.wav", 6.5, [walk("Leffery", "Wilam2", face("Leffery", "Trislan")),       # :Guardwalk
                         walk("Wilam", "Ralof1", face("Wilam", "Trislan"))]),
        ("23.wav", 0, [stop("Narrator"), face("Trislan", "Ralof"), loop("Trislan", "conv2")]),     # Trislan :OnSpeak23
        ("24.wav", 0, [stop("Trislan"), loop("Ralof", "conv4")]),                     # Ralof :OnSpeak24
        ("25.wav", 0, [stop("Ralof"), loop("Trislan", "conv2")]),                     # Trislan :OnSpeak25
        ("26.wav", 0, [stop("Trislan"), loop("Ralof", "conv3")]),                     # Ralof :OnSpeak26
        ("26.wav", 3, [stop("Ralof"), once("Ralof", "attack_melee")]),               # Ralof :Attack
        ("26.wav", 3.6, [sound("weapons/fleshhit04.wav", "Trislan")]),                # :Slapsound
        ("27a.wav", 0, [once("Trislan", "play_death", "play_getup")]),               # Trislan :OnDie, :GetUp
        ("27.wav", 0, [loop("Narrator", "conv3"), face("Narrator", "peasant2")]),     # Narrator :OnSpeak27
        ("27.wav", 13, [walk(who, spot, face(who, "peasant2"))                        # :Trigger28: CastCall
                        for who, spot in (("Ralof", "Ralof3"), ("Wilam", "Wilam4"), ("Leffery", "Leffery3"),
                                          ("Abriel", "Abriel4"), ("Trislan", "Trislan3"))]),
        ("28.wav", 0, [loop("Narrator", "conv3")]),                                   # Narrator :Bow
        ("28.wav", 1, [stop("Narrator")] + [once(who, "bow") for who in ("Ralof", "Wilam", "Leffery", "Abriel",
                                                                           "Trislan")]),   # :OnBow
    ]
    exits = [walk("Trislan", "Trislan2", face("Trislan", "Wilam")), walk("Abriel", "Abriel2", face("Abriel", "Wilam")),
             walk("Ralof", "Ralof2", face("Ralof", "Trislan")), walk("Wilam", "Wilam3", face("Wilam", "Trislan")),
             walk("Leffery", "Leffery2", face("Leffery", "Trislan"))]
    timed = sorted([(starts[line] + delay, [a for a in actions if a]) for line, delay, actions in cues]
                   + [(end - 0.5, exits)], key=lambda cue: cue[0])     # :Exit, just before the curtain closes
    assert all(line in names for line, _, _ in cues)
    rows = []
    for at, actions in timed:
        rows.append(f"    {{{at:.2f}, function()")
        rows += [f"        {a}" for a in actions]
        rows.append("    end},")
    home = ", ".join(f"{name} = {{{p['position']['x']}, {p['position']['y']}, {p['position']['z']}}}"
                     for name, p in players.items())
    arrivals = [f"handlers[{EV_ARRIVE + k}] = function() arrived(\"{name}\") end" for k, name in enumerate(PLAYERS)]
    return [
        "-- The players' cues (Narrator.scr, Trislan.scr, Abriel.scr, Wilam.scr, Ralof.scr, Leffery.scr): walks, faces",
        "-- and clips at THEPLAY.scr's times from the first line (convert.py citylua.play_cues). A walk's arrival",
        "-- (EV_ARRIVE + k) runs what MM9 does there: faces whom it targets, and the slap.",
        f"local P = {{{', '.join(f'{n} = {players[n]['actor_index']}' for n in PLAYERS)}}}",
        f"local ARRIVAL = {{{', '.join(f'{n} = {EV_ARRIVE + k}' for k, n in enumerate(PLAYERS))}}}",
        "local MARKS = {" + ", ".join(f"{k} = {{{v[0]}, {v[1]}, {v[2]}}}" for k, v in marks.items()) + "}",
        f"local HOME = {{{home}}}",
        "local function place(name)",
        "    if P[name] then return evt.GetMapActorPosition(P[name]) end",
        "    local m = MARKS[name]",
        "    return m[1], m[2], m[3]",
        "end",
        "local function loop(who, clip) evt.PlayActorClip(P[who], clip, true) end",
        "local function stop(who) evt.PlayActorClip(P[who], \"\") end",
        "local function face(who, name)",
        "    local x, y = place(name)",
        "    if x ~= nil then evt.FaceActorTo(P[who], x, y, 0.4) end",
        "end",
        "local function sound(name, who)",
        "    local x, y, z = place(who)",
        "    if x ~= nil then evt.PlaySoundName(name, math.floor(x), math.floor(y), math.floor(z)) end",
        "end",
        "local onArrival = {}",
        "local function walk(who, name, arrive)",
        "    local x, y, z = place(name)",
        "    if x == nil then return end",
        "    evt.ClearActorPresentation(P[who])",
        "    onArrival[who] = arrive",
        "    evt.MoveActorTo(P[who], x, y, z, ARRIVAL[who])",
        "end",
        "local function arrived(who)",
        "    local f = onArrival[who]",
        "    onArrival[who] = nil",
        "    if f ~= nil and var(\"PlayLine\") > 0 then f() end",
        "end",
        *arrivals,
        "local CUES = {", *rows, "}",
        "local cue = 0",
        "local function playCues(delay)",
        "    cue = 1",
        f"    evt.StartTimer({T_CUE}, seconds(delay + CUES[1][1]))",
        "end",
        f"handlers[{T_CUE}] = function()",
        f"    evt.StopTimer({T_CUE})",
        "    if cue < 1 or cue > #CUES then return end",
        "    if var(\"PlayLine\") == 0 then cue = 0 return end   -- the show stopped",
        "    local at = CUES[cue][1]",
        "    CUES[cue][2]()",
        "    cue = cue + 1",
        f"    if cue <= #CUES then evt.StartTimer({T_CUE}, seconds(CUES[cue][1] - at)) else cue = 0 end",
        "end",
        "local function playersHome()   -- a show left half-way: the players back at their places",
        "    for who, p in pairs(HOME) do",
        "        evt.ClearActorPresentation(P[who])",
        "        evt.SetMapActorPosition(P[who], p[1], p[2], p[3])",
        "    end",
        "end",
    ]
