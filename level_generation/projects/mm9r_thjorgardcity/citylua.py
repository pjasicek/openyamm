"""
Thjorgard City's map Lua: the doors (MM9's locked facade doors say so), the scripted townsfolk and props as native
handlers, each citing its .scr (README.md, "Scripted objects"; the behaviour spec of every script is
work/scr_spec.md).

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h; the handler ends by opening the dialogue itself).
"""

from __future__ import annotations

import csv
import json

from dungeon import town_portal
from dungeon.objects import bonus_call
from dungeon.source import ROOT
from quest_xp import balanced_experience, experience_note

LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
EV_LOAD, EV_LOCKED = 1, 230
T_POLL = 260
EV_KILLED = 270                     # monster killed hook (NPC416.scr :OnDeath); outside every map event range
EV_SCRIPTED_PROP = 330              # letters, books, the town portal altar, the book key, the well: + k
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr", "townportal.scr", "greatbookkey.scr")
SCRIPTED_PROP_NAMES = ("WellMMIX0",)
COG_BOOK_KEY = 400                  # SetSprite key of the Great Book key (GreatBookKey.scr hides it)
LOCATION_KEY = 1025                 # ForadWorld.scr "Thjorgard"
TOWN_PORTAL_KEY = 5011              # TownPortal.scr "Thjorgard"
SVEN_CLAN_KEYS = (82, 38, 51, 63, 74)   # United.inc :SvenInit

# MM9 doors with Locked 1, MoveDist 0 and no key, script or trigger that unlocks them: every linear `Door` of the city
# (facades, upper rooms of the shops, the palace's side rooms). A click says the door is locked (doorlock01.wav).
# (work/doors_survey.txt: the 69 `Door` objects, Door2-Door71 without Door15, a swing door)
LOCKED_GROUPS = [f"Door{n}" for n in range(2, 72) if n != 15]


def locked_groups(build) -> list:
    """The linear Door groups that exist in this DAT (the list above is a superset)."""
    return sorted({m["group"] for m in build.movers if m["group"] in set(LOCKED_GROUPS)})


MOVER_EVENTS = {group: (EV_LOCKED, "click") for group in LOCKED_GROUPS}


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
    return {name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted_props(build))}


def prop_cogs(build) -> dict:
    return {name: COG_BOOK_KEY for name, entry in scripted_props(build)
            if "greatbookkey" in str(entry.get("script") or "").lower()}


def map_script(hooks, build) -> str:
    from dungeon import lua
    script = lua.Script(build, "Thjorgard City")
    # MM9 names two leaves Armor-Forge0 and Weapon-Forge0: the DOORS table keys every leaf as a string.
    assert script.lines[4].startswith("local DOORS = {")
    script.lines[4] = "local DOORS = {" + ", ".join(f'["{k}"] = {v}' for k, v in sorted(script.door.items())) + "}"
    script.doors()
    script.chests()
    a, o = hooks.actor, hooks.objects
    locked = locked_groups(build)
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
        f"-- MM9's locked doors (Locked 1, MoveDist 0, no key): the {len(locked)} linear doors of the facades and upper rooms.",
        f"handlers[{EV_LOCKED}] = function()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        "",
        f"-- ForadWorld.scr (ScriptObject0, \"Thjorgard\"): key {LOCATION_KEY} is the party's location while here (keys",
        "-- 1024-1033 are the towns'); key 5017 closes the shops from 20:00 to 06:00 (their dialogues forbid or require it).",
        "local function shopHours()",
        "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
        "    local closed = hour >= 20 or hour < 6",
        "    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end",
        "end",
        "",
    ]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"))

    def item(verb, number, who):
        return f"MM9.{verb}Item({number}, \"thjorgardcity:{who}\")"

    lines = [
        "-- BankOrb.scr (Ragnar Gjalpssen, RUDE 13: nKey 335, nKey2 323): the Orb of Linking. A click with the orb (item",
        "-- 252) after the quest (key 322) unlocks the row that installs it (key 330); the exit places it (key 323) and the",
        "-- sixth bank's orb pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).",
        f"handlers[{rude_use_event(o['Ragnar'])}] = function()",
        f"    if not has(323) and has(322) and {item('has', 252, 'Ragnar')} == 1 then MM9.giveKey(330) end",
        "    MM9.openRude(13)",
        "end",
        f"handlers[{rude_exit_event(o['Ragnar'])}] = function()",
        "    if not has(330) then return end",
        "    MM9.takeKey(330)",
        "    if not has(335) then return end",
        f"    quest(); {item('take', 252, 'Ragnar')}; MM9.giveKey(323)",
        "    if has(337) then return end",
        "    for k = 331, 336 do if not has(k) then return end end",
        f"    reward(337, {balanced_experience(20000, 337)}, 15000){experience_note(20000, 337)}",
        "end",
        "",
        "-- NPC4.scr (Johannes Bem, RUDE 4): Scholar to Mage. With 293 the first task's item is swapped (242 -> 244, key",
        "-- 288); with 493 the reward (item 243 taken, key 294, 5 000 gold, 63 000 experience) and the promotion of the",
        "-- characters holding keys 429-432.",
        f"handlers[{rude_exit_event(o['Johannes'])}] = function()",
        "    if not has(288) and has(293) then",
        f"        {item('take', 242, 'Johannes')}; {item('give', 244, 'Johannes')}; MM9.giveKey(288); quest()",
        "        return",
        "    end",
        "    if not has(294) and has(493) then",
        f"        {item('take', 243, 'Johannes')}; reward(294, {balanced_experience(63000, 294)}, 5000); "
        f"promote(\"Mage\", 429){experience_note(63000, 294)}",
        "    end",
        "end",
        "",
        "-- NPC161.scr (Tymon the Nord, RUDE 161): Initiate to Scholar. :ScholarCheck: unless done (201), a character",
        "-- holding 425-428 gives 201. MM9's engine set those per-character keys from the class check of \"We are seeking",
        "-- promotion to Scholar\" (its granted code 2081, kept as key 2081); here: that row asked, whoever is in the party",
        "-- (every promotion quest is offered to any party, the user 2026-11-08, dialogue/promotions.yml). With 203",
        "-- (24 500 experience) or 204 (11 000) and 1 000 gold: key 205 and the promotion of the members eligible.",
        f"handlers[{rude_exit_event(o['Tymon'])}] = function()",
        "    if not has(201) and has(2081) then MM9.giveKey(201); quest() end",
        "    if has(205) then return end",
        f"    if has(203) then reward(205, {balanced_experience(24500, 205)}, 1000); promote(\"Scholar\", 425)"
        f"{experience_note(24500, 205)}",
        f"    elseif has(204) then reward(205, {balanced_experience(11000, 205)}, 1000); promote(\"Scholar\", 425) end",
        "end",
        "",
        "-- NPC3.scr (Sven Forkbeard, the Jarl, RUDE 3; United.inc). The click: the five clans (82, 38, 51, 63, 74 -> 178).",
        "-- The exit: the battle (104 -> 486), Thjorad Mine (32 -> 163, 12 000 experience, 6 000 gold, item 197 taken), the",
        "-- refinery (33 -> 177, 68 004, 3 000), the clans united (83 -> 179, 26 500, 6 000), the lifesaver (234 -> 235,",
        "-- 5 000 experience, 10 000 gold).",
        f"handlers[{rude_use_event(o['Sven'])}] = function()",
        "    if not has(178) then",
        "        local n = 0",
        "        for _, k in ipairs({" + ", ".join(str(k) for k in SVEN_CLAN_KEYS) + "}) do if has(k) then n = n + 1 end end",
        "        if n == 5 then MM9.giveKey(178) end",
        "    end",
        "    MM9.openRude(3)",
        "end",
        f"handlers[{rude_exit_event(o['Sven'])}] = function()",
        "    if has(104) and not has(486) then MM9.giveKey(486); quest() end",
        f"    if not has(163) and has(32) then reward(163, {balanced_experience(12000, 163)}, 6000); "
        f"{item('take', 197, 'Sven')} end",
        f"    if not has(177) and has(33) then reward(177, {balanced_experience(68004, 177)}, 3000) end"
        f"{experience_note(68004, 177)}",
        f"    if not has(179) and has(83) then MM9.giveKey(179); "
        f"MM9.giveExperience({balanced_experience(26500, 179)}); MM9.giveGold(6000) end{experience_note(26500, 179)}",
        f"    if not has(235) and has(234) then MM9.giveExperience({balanced_experience(5000, 235)}); "
        "MM9.giveGold(10000); quest(); MM9.giveKey(235) end",
        "end",
        "",
        "-- NPC5.scr (Gunnar Thjorsmith, the smith, RUDE 5). The click: Thjorad ore in the packs (items 359, 360, 361) unlocks",
        "-- its row (395 + 396, 397, 398). The exit: after the smithing (464) the ore is paid (399: 700, 400: 1 500, 463:",
        "-- 3 000 gold, the ore taken) and keys 395-400, 463, 464 cleared; the refinery's part (9513 -> 9514, item 398 ->",
        "-- 399).",
        f"handlers[{rude_use_event(o['ShopkeeperElfFemaleB1'])}] = function()",
        f"    if {item('has', 359, 'Gunnar')} == 1 then MM9.giveKey(395); MM9.giveKey(396) end",
        f"    if {item('has', 360, 'Gunnar')} == 1 then MM9.giveKey(395); MM9.giveKey(397) end",
        f"    if {item('has', 361, 'Gunnar')} == 1 then MM9.giveKey(395); MM9.giveKey(398) end",
        "    MM9.openRude(5)",
        "end",
        f"handlers[{rude_exit_event(o['ShopkeeperElfFemaleB1'])}] = function()",
        "    if has(464) then",
        f"        if has(399) then {item('take', 359, 'Gunnar')}; MM9.giveGold(700) end",
        f"        if has(400) then {item('take', 360, 'Gunnar')}; MM9.giveGold(1500) end",
        f"        if has(463) then {item('take', 361, 'Gunnar')}; MM9.giveGold(3000) end",
        "        for _, k in ipairs({395, 396, 397, 398, 399, 400, 463, 464}) do MM9.takeKey(k) end",
        "    end",
        "    if not has(9514) and has(9513) then",
        f"        {item('take', 398, 'Gunnar')}; {item('give', 399, 'Gunnar')}; MM9.giveKey(9514); quest()",
        "    end",
        "end",
        "",
        "-- NPC7.scr (Hjarrand Fixer, RUDE 7; not at the refinery): the payment for fixing the refinery's machine. With 360",
        "-- (1 000 gold) or 361 (2 000) and the gold: key 362, 363 cleared; without the gold: key 363 (MM9 plays a voice).",
        "-- He leaves the city once paid (hidden on 362).",
        f"handlers[{rude_exit_event(o['ShopkeeperElfFemaleB8'])}] = function()",
        "    if has(362) then return end",
        "    for _, cost in ipairs({{360, 1000}, {361, 2000}}) do",
        "        if has(cost[1]) then",
        "            if MM9.hasGold(cost[2]) == 1 then MM9.takeGold(cost[2]); MM9.giveKey(362); MM9.takeKey(363); quest()",
        "            else MM9.giveKey(363) end",
        "            return",
        "        end",
        "    end",
        "end",
        "",
        "-- NPC416.scr (Harris Willington, RUDE 416) :OnDeath: the prize quest's key 233.",
        f"handlers[{EV_KILLED}] = function(context)",
        f"    if context.actorIndex == {a['Harris']} then MM9.giveKey(233) end",
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
               (rude_use_event(o["Ragnar"]), "Ragnar Gjalpssen", None), (rude_exit_event(o["Ragnar"]), "Bank", None),
               (rude_exit_event(o["Johannes"]), "Johannes Bem", None), (rude_exit_event(o["Tymon"]), "Tymon", None),
               (rude_use_event(o["Sven"]), "Sven Forkbeard", None), (rude_exit_event(o["Sven"]), "Sven", None),
               (rude_use_event(o["ShopkeeperElfFemaleB1"]), "Gunnar Thjorsmith", None),
               (rude_exit_event(o["ShopkeeperElfFemaleB1"]), "Gunnar", None),
               (rude_exit_event(o["ShopkeeperElfFemaleB8"]), "Hjarrand", None),
               *[(f(o[n]), "Thorolf", None) for n in ("Thorolf0", "Thorolf1") for f in (rude_use_event, rude_exit_event)])
    script.hooks.append(f'RegisterMonsterKilledHook({EV_KILLED}, "Harris Willington", handlers[{EV_KILLED}])')

    # --- scripted props --------------------------------------------------------------------------------------------
    lines = ["-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9), TownPortal.scr,",
             "-- GreatBookKey.scr, the well."]
    cogs = prop_cogs(build)
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
        elif "greatbookkey" in kind:
            cog = cogs[name]
            lines += [f"-- {name}: GreatBookKey.scr. Shown only with key 375 (its 'appear' message, which nothing in MM9",
                      "-- sends) and gone with 374. A click with the Great Book (item 243) gives items 560, 244 and 347 and",
                      "-- takes the key (374); without it the click gives item 244 (MM9 does).",
                      f"local function bookKeyShown() return has(375) and not has(374) end",
                      f"handlers[{event}] = function()",
                      "    if not bookKeyShown() then return end",
                      f"    if {item('has', 243, name)} == 1 then",
                      f"        {item('give', 560, name)}; {item('give', 244, name)}; {item('give', 347, name)}",
                      f"        MM9.giveKey(374); evt.SetSprite({cog}, 0, \"0\")",
                      f"    else {item('give', 244, name)} end",
                      "end"]
            script.registrations.append((event, name, "Book", "event"))
        elif name in SCRIPTED_PROP_NAMES:
            lines += [f"-- {name}: MM9's WellMMIX, its class's use (dungeon/objects.py bonus_call: the party's Endurance +5,",
                      "-- once).",
                      f"handlers[{event}] = function() {bonus_call(build, name)} end"]
            script.registrations.append((event, name, "Well", "event"))
        else:
            lines.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0) end"
                         f"   -- {name} (Book.scr: pages turn, no text)")
            script.registrations.append((event, name, "Book", "event"))
    script.add(lines + [""])

    # --- map load and the poll -------------------------------------------------------------------------------------
    load = [
        f"    show({a['Sven']}, (not has(40)) or has(108))   -- NPC3.scr :Init (gone on 40 unless 108)",
        f"    show({a['ShopkeeperElfFemaleB8']}, not has(362))   -- NPC7.scr :Init: Hjarrand leaves once paid",
        f"    show({a['ShopkeeperElfFemaleB11']}, not has(450))   -- Retainer.scr: Hrolf Spearmaster, hidden while hired",
        f"    show({a['ShopkeeperElfFemaleB10']}, not has(452))   -- Retainer.scr: Arienh A'Klindor, hidden while hired",
        f"    show({a['ShopkeeperElfFemaleB12']}, not has(453))   -- RandverRetainer.scr: Randver, hidden while hired",
        "    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)",
        f"    show({a['Thorolf0']}, thorolf); show({a['Thorolf1']}, thorolf)",
    ]
    load += altar_load
    if cogs:
        load.append(f"    evt.SetSprite({COG_BOOK_KEY}, bookKeyShown() and 1 or 0, \"0\")   -- GreatBookKey.scr :Init")
    lines = [
        "local function poll()",
        "    shopHours()",
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
    return script.finish(on_load=[EV_LOAD])
