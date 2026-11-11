"""
Sturmford City's map Lua: the doors (MM9's locked doors say so and jiggle), the chests (the two treasure bags) and the
scripted objects as native handlers, each citing its .scr (README.md, "Scripted objects"; the behaviour spec of every
script is work/scr_spec.md).

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h). The RUDEProps (Bjarni, Ludwig, the innkeeper, the drinkers, Ercc) are actors that loop
their MM9 pose (../mm9r_common/rude_props.py): the load handler starts the pose, their use and exit parts are the
actor hooks above.
"""

from __future__ import annotations

import csv
import json

from dungeon import lua
from dungeon import town_portal
from dungeon.objects import trigger_box
from dungeon.source import ROOT
import rude_props
from quest_xp import balanced_experience, experience_note

LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
EV_LOAD, EV_LOCKED, EV_JAIL_DOOR = 1, 230, 231
EV_DIMENSIONAL_TRAVEL = 250         # the dimensional travel pedestal and its orb (convert.py PEDESTAL)
T_POLL = 260
T_ERCC = 261                        # Ercc's second line, as he passes out (ErccSpeech.scr :OnPassOut)
ERCC_PASSOUT_SECONDS = 66           # his ercc01a-c animations (66.0 s) and ercc01.wav (66.4 s): then he passes out
EV_NPC_PROP = 300                   # posed talking props (props.json kind npc): EV_NPC_PROP + k
EV_SCRIPTED_PROP = 330              # letters, books, the town portal altar: EV_SCRIPTED_PROP + k
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr", "townportal.scr")
COG_NPC_PROP = 400                  # SetSprite keys of the posed talking props (hidden while hired or away)

# MM9 doors with Locked 1 and no key, script or trigger that unlocks them: the facades' doors (`Door` objects with
# MoveDist 0) and the locked swing doors. A click says the door is locked (MM9 jiggles it, doorlock01.wav). The jail
# door has its own event (Sturmguard.scr opens and locks it).
LOCKED_GROUPS = ["Door0", "Door5", "Door6", "Door7", "Door8", "Door9", "Door11", "Door12", "Door13", "Door14",
                 "Door15", "Door16", "Door17", "Door18", "Door19", "Door20", "Door21", "Door22", "Door23", "Door24",
                 "Door25", "Door26", "Door27", "Door28", "Door29", "Door30", "Door31", "Door32", "Door33", "Door34",
                 "Door35", "Door36", "Door37", "Door38", "RotatingDoor16", "vaultdoor", "TestHouse1",
                 "f10doorl", "f10doorr", "f10doorl0", "f10doorr0", "RotatingDoor18"]
# Movers that are no doorway but open on a click: the sewer hatches over ExitS and ExitW (an invisible plate under each
# seals its shaft), the grate over the shaft to Beethoven, the tavern's upstairs back door, the bar's counter flap.
TOGGLE_GROUPS = {"RotatingDoor7": 240, "RotatingDoor9": 241, "BeetHovengrate": 242, "RotatingDoor2": 243,
                 "barflap1": 244}
MOVER_EVENTS = {**{group: (EV_LOCKED, "click") for group in LOCKED_GROUPS}, "Jaildoor": (EV_JAIL_DOOR, "click"),
                **{group: (event, "click") for group, event in TOGGLE_GROUPS.items()}}
MARKERS = ("HatlatiHome", "PrisonMarker", "ItlorWork", "IvsarMarker", "RandverHide")
PROP_COGS = ("CommonerElfFemaleA1", "Bjarni")      # posed props a script hides (Ake while hired, Bjarni on key 40)


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


def posed_people(build) -> list:
    """props.json's posed people placed as actors (rude_props.py), in file order: [(name, entry)]."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    return [(e["source_name"], e) for e in entries if rude_props.is_posed_person(e)]


def scripted_props(build) -> tuple[list, list]:
    """props.json's posed talking props left as decorations (none: every one is a posed person) and scripted props, in
    file order: [(name, entry)] each."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    npcs = [(e["source_name"], e) for e in entries if e["kind"] == "npc" and not rude_props.is_posed_person(e)]
    scripted = [(e["source_name"], e) for e in entries
                if e["kind"] == "prop" and str(e.get("script") or "").lower().replace("scripts\\", "")
                in SCRIPTED_PROP_SCRIPTS]
    return npcs, scripted


def prop_events(build) -> dict:
    """DAT prop name -> click event: the posed talking props and the scripted props."""
    npcs, scripted = scripted_props(build)
    events = {name: EV_NPC_PROP + k for k, (name, _) in enumerate(npcs)}
    events.update({name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted)})
    return events


def prop_cogs(build) -> dict:
    npcs, _ = scripted_props(build)
    return {name: COG_NPC_PROP + k for k, (name, _) in enumerate(npcs) if name in PROP_COGS}


def marker_points(build) -> dict:
    """The MM9 markers the scripts walk NPCs to, as native points on the floor under them."""
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


def map_script(hooks, build) -> str:
    script = lua.Script(build, "Sturmford City")
    script.doors()
    script.chests()
    a, o, points = hooks.actor, hooks.objects, hooks.points
    npcs, scripted = scripted_props(build)
    lines = [
        "local function has(k) return MM9.hasKey(k) == 1 end",
        "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; "
        "if gold > 0 then MM9.giveGold(gold) end; quest() end",
        "",
        "-- MM9's locked doors (Locked 1, no key): the facades' doors and the locked swing doors.",
        f"handlers[{EV_LOCKED}] = function()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        "-- The jail door (Jaildoor, Locked 1): the prison guard opens and locks it (Sturmguard.scr).",
        f"handlers[{EV_JAIL_DOOR}] = function()",
        "    if var(\"JailOpen\") == 1 then evt.SetDoorState(DOORS.Jaildoor, DoorAction.Trigger) else "
        f"handlers[{EV_LOCKED}]() end",
        "end",
        "",
        "-- ForadWorld.scr (ScriptObject0, \"Sturmford\"): key 1026 is the party's location while here (keys 1024-1033",
        "-- are the towns'); key 5017 closes the shops from 20:00 to 06:00 (42 MM9 dialogues forbid or require it).",
        "local function shopHours()",
        "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
        "    local closed = hour >= 20 or hour < 6",
        "    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end",
        "end",
        "",
    ]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"), (EV_JAIL_DOOR, "Jail door", "Door"))
    script.add(["-- Chedian's dimensional travel pedestal (not MM9's: the user, 2026-11-09), as on the other continents.",
                f"handlers[{EV_DIMENSIONAL_TRAVEL}] = function() evt.OpenDimensionDoor() end", ""],
               (EV_DIMENSIONAL_TRAVEL, "Dimensional Travel", "Dimensional Travel"))
    toggles = ["-- Hatches, the grate, the tavern's back door and the bar's flap: a click opens or shuts them."]
    for group, event in TOGGLE_GROUPS.items():
        leaves = [m["node"][5:] for m in build.movers if m["group"] == group]
        calls = " ".join(f"evt.SetDoorState(DOORS[\"{leaf}\"], DoorAction.Trigger)" for leaf in leaves)
        toggles.append(f"handlers[{event}] = function() {calls} end   -- {group}")
    script.add(toggles + [""], *[(event, group, "Door") for group, event in TOGGLE_GROUPS.items()])

    hx, hy, hz = points["PrisonMarker"]
    lines = [
        "-- Hatlati Oord (NPC48.scr, RUDE 48), arrested: in the cell, the door shut and locked, key 5009 (MM9 walks him",
        "-- there behind the guard).",
        "local function jailHatlati()",
        f"    evt.SetMapActorPosition({a['Hatlati']}, {hx}, {hy}, {hz})",
        "    set(\"JailOpen\", 0); close(\"Jaildoor\")",
        "    MM9.giveKey(5009)",
        "end",
        "",
        "-- Bankorb.scr (Herdis the Stout, RUDE 56): the Orb of Linking. A click with the orb (item 252) after the quest",
        "-- (key 322) unlocks the row that installs it (key 330); the exit places it (key 324) and the sixth bank's orb",
        "-- pays 20 000 experience and 15 000 gold (key 337; banks' keys 331-336).",
        f"handlers[{rude_use_event(o['Banker'])}] = function()",
        "    if not has(324) and has(322) and MM9.hasItem(252, \"sturmfordcity:Banker\") == 1 then MM9.giveKey(330) end",
        "    MM9.openRude(56)",
        "end",
        f"handlers[{rude_exit_event(o['Banker'])}] = function()",
        "    if not has(330) then return end",
        "    MM9.takeKey(330)",
        "    if not has(336) then return end",
        "    quest(); MM9.takeItem(252, \"sturmfordcity:Banker\"); MM9.giveKey(324)",
        "    if has(337) then return end",
        "    for k = 331, 336 do if not has(k) then return end end",
        f"    reward(337, {balanced_experience(20000, 337)}, 15000){experience_note(20000, 337)}",
        "end",
        "",
        "-- Beathag.scr (the healer, RUDE 58): a party that broke a temple window (key 5002) and offered to pay (5003)",
        "-- pays 700 gold on leaving. (The 11 windows are glass faces here, not breakable: README.)",
        f"handlers[{rude_exit_event(o['Healer'])}] = function()",
        "    if has(5002) and has(5003) then",
        "        if MM9.hasGold(700) == 1 then MM9.takeGold(700); MM9.takeKey(5002); MM9.takeKey(5003)",
        "        else evt.StatusText(\"You don't have enough gold.\") end",
        "    end",
        "end",
        "",
        "-- SpiesLikeUs.scr (Bjarni Herjolfssen, RUDE 46): told of Randver (key 18): 2 000 experience, 500 gold (key 471).",
        f"handlers[{rude_exit_event(o['CommonerHumanMaleA4'])}] = function()",
        f"    if not has(471) and has(18) then reward(471, {balanced_experience(2000, 471)}, 500) end",
        "end",
        "",
        "-- Randverrun.scr (Randver the Storm, RUDE 51): asked about sabotage (key 15): 800 experience (key 495) and he",
        "-- vanishes by town portal (MM9 runs him to RandverHide first); gone on every later visit.",
        f"handlers[{rude_exit_event(o['RUDEProp3'])}] = function()",
        "    if not has(15) then return end",
        f"    if not has(495) then MM9.giveKey(495); MM9.giveExperience({balanced_experience(800, 495)}) end",
        "    quest()",
        f"    MM9.clientFx({a['RUDEProp3']}, \"mm9:town_portal\")   -- :Vanish: DoClientFX g_hmyObject, Ceffect",
        f"    MM9.removeActor({a['RUDEProp3']})",
        "end",
        "",
        "-- NPC61.scr (Fridleif Gjukissen, the clerk, RUDE 61): the Basilisk Skin (item 380 or 591) with the labours",
        "-- taken (key 214) unlocks its row (215); the Gladiator promotion (key 26 -> 221, 63 000 experience, 5 000 gold,",
        "-- every character holding key 409-412); with Kira's Shield delivered (219) the shield (item 375) is taken.",
        f"handlers[{rude_use_event(o['Clerk'])}] = function()",
        "    if has(214) and (MM9.hasItem(380, \"sturmfordcity:Clerk\") == 1",
        "        or MM9.hasItem(591, \"sturmfordcity:Clerk\") == 1) then MM9.giveKey(215) end",
        "    MM9.openRude(61)",
        "end",
        f"handlers[{rude_exit_event(o['Clerk'])}] = function()",
        "    if not has(221) and has(26) then",
        f"        reward(221, {balanced_experience(63000, 221)}, 5000){experience_note(63000, 221)}",
        "        MM9.promoteParty(\"Gladiator\")   -- every eligible member (not MM9's per-character keys 409-412)",
        "    end",
        "    if has(219) and MM9.hasItem(375, \"sturmfordcity:Clerk\") == 1 then MM9.takeItem(375, \"sturmfordcity:Clerk\") end",
        "end",
        "",
        "-- Sturmguard.scr (the prison guard; the DAT gives him no dialogue, his script opens 425): the jail door (keys",
        "-- 5018 open, 5019 close and lock) and Hatlati's arrest (key 154 -> in the cell, key 5009).",
        f"handlers[{rude_use_event(o['PoorTownGuard10'])}] = function()",
        "    MM9.giveKey(5008)",
        "    MM9.openRude(425)",
        "end",
        f"handlers[{rude_exit_event(o['PoorTownGuard10'])}] = function()",
        "    MM9.takeKey(5008)",
        "    if has(5019) then MM9.takeKey(5018); MM9.takeKey(5019); set(\"JailOpen\", 0); close(\"Jaildoor\")",
        "    elseif has(5018) then set(\"JailOpen\", 1); open(\"Jaildoor\") end",
        "    if has(5009) or not has(154) then return end",
        "    -- the guard sends Hatlati GotoJail and opens the cell for him: a dead Hatlati takes no message",
        "    -- (MM9.receives), so the door stays open and he never walks in (no key 5009)",
        f"    if MM9.receives(\"sturmfordcity\", \"Hatlati\", \"GotoJail\", {a['Hatlati']}) then jailHatlati()",
        "    else set(\"JailOpen\", 1); open(\"Jaildoor\") end",
        "end",
        "",
        "-- NPC90.scr (Ivsar Forktooth, RUDE 90): leaving with him (key 194 taken) sends him home: key 196 enables",
        "-- Bjarni's reward row. MM9 also gives Drangheim Prison's alarm key 5006 here (a source quirk, left out: README).",
        f"handlers[{rude_exit_event(o['Ivsar'])}] = function()",
        "    MM9.takeKey(194)",
        "    if not has(21) then MM9.giveKey(196) end",
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
               (rude_use_event(o["Banker"]), "Herdis the Stout", None), (rude_exit_event(o["Banker"]), "Bank", None),
               (rude_exit_event(o["Healer"]), "Beathag", None),
               (rude_exit_event(o["CommonerHumanMaleA4"]), "Bjarni Herjolfssen", None),
               (rude_exit_event(o["RUDEProp3"]), "Randver", None),
               (rude_use_event(o["Clerk"]), "Fridleif", None), (rude_exit_event(o["Clerk"]), "Fridleif", None),
               (rude_use_event(o["PoorTownGuard10"]), "Guard", None),
               (rude_exit_event(o["PoorTownGuard10"]), "Guard", None),
               (rude_exit_event(o["Ivsar"]), "Ivsar", None),
               *[(f(o[n]), "Thorolf", None) for n in ("Thorolf0", "Thorolf1") for f in (rude_use_event, rude_exit_event)])

    # --- posed people -----------------------------------------------------------------------------------------------
    # Actors (rude_props.py). A use hook replaces the native opening, so each opens its own dialogue after its
    # script's use part: the voice line (:OnUse Playsound), Bjarni's keys, Ludwig looking up. Bjarni's and Ludwig's
    # :OnRude are their exit hooks.
    use_parts = {
        # Bjarni.scr :OnUse: the Basilisk Skin with the labours (key 214 -> 215); the five clans (key 178).
        "Bjarni": ["if has(214) and (MM9.hasItem(380, \"sturmfordcity:Bjarni\") == 1",
                   "    or MM9.hasItem(591, \"sturmfordcity:Bjarni\") == 1) then MM9.giveKey(215) end",
                   "if not has(178) and has(82) and has(34) and has(51) and has(63) and has(74) then "
                   "MM9.giveKey(178) end"],
        # LudwigVan.scr :OnUse PlayAnim Ludwig_Lookup (:OnRude's Init loops Ludwig_writting again)
        "Ludwig": [f"evt.PlayActorClip({a.get('Ludwig')}, {{\"ludwig_lookup\", \"ludwig_writing\"}}, true)"],
    }
    exit_parts = {"Bjarni": "bjarniExit()", "Ludwig": "ludwigExit()"}
    hook_lines = ["-- MM9's RUDEProps: people posed as props (actors looping their pose); their scripts' use and exit parts."]
    hooked = []
    for name, entry in posed_people(build):
        rude, voice = hooks.rude.get(name), rude_props.use_voice(entry)
        body = use_parts.get(name, []) + ([f"MM9.playSound(\"{voice}\")"] if voice else [])
        body.append(f"MM9.openRude({rude})" if rude else "evt.StatusText(\"He is too drunk to talk.\")")  # Ercc
        hook_lines.append(f"handlers[{rude_use_event(o[name])}] = function()   -- {name} ({entry.get('script')})")
        hook_lines += ["    " + line for line in body] + ["end"]
        hooked.append((rude_use_event(o[name]), name, None))
        if name in exit_parts:
            hook_lines.append(f"handlers[{rude_exit_event(o[name])}] = function() {exit_parts[name]} end")
            hooked.append((rude_exit_event(o[name]), name, None))
    lines = [
        "-- LudwigVan.scr :OnRudeExit (Ludwig Van, RUDE 47): his manuscript found (key 19): 12 000 experience, 2 000 gold,",
        "-- the manuscript (item 248) taken (key 116).",
        "local function ludwigExit()",
        "    if not has(116) and has(19) then",
        f"        reward(116, {balanced_experience(12000, 116)}, 2000); MM9.takeItem(248, \"sturmfordcity:Ludwig\")"
        f"{experience_note(12000, 116)}",
        "    end",
        "end",
        "-- Bjarni.scr :OnRudeExit (Jarl Bjarni Thorvaldssen, RUDE 45): Ivsar rescued (key 21: 117, 42 000 experience,",
        "-- 3 500 gold, Ivsar to his marker by the throne); the love letter (22: item 247, key 150) and its answer (24 or",
        "-- 25: 151, 15 200 experience, 2 000 gold); Anskram Keep (41: 149, 20 000, 3 000); the clans united (83: 179,",
        "-- 26 500, 6 000).",
        "local function bjarniExit()",
        "    if not has(117) and has(21) then",
        f"        reward(117, {balanced_experience(42000, 117)}, 3500){experience_note(42000, 117)}",
    ]
    if "IvsarMarker" in points:
        ix, iy, iz = points["IvsarMarker"]
        # Bjarni's `trigger Ivsar stop` (NPC90.scr :OnStop walks him to IvsarMarker): a dead Ivsar takes no message
        lines.append(f"        if MM9.receives(\"sturmfordcity\", \"Ivsar\", \"stop\", {a['Ivsar']}) then "
                     f"evt.SetMapActorPosition({a['Ivsar']}, {ix}, {iy}, {iz}) end")
    lines += [
        "    end",
        "    if has(22) and not has(150) then MM9.giveKey(150); MM9.giveItem(247, \"sturmfordcity:Bjarni\") end",
        f"    if (has(24) or has(25)) and not has(151) then "
        f"reward(151, {balanced_experience(15200, 151, 'bjarni.scr', 'loveletter2')}, 2000) end"
        f"{experience_note(15200, 151, 'bjarni.scr', 'loveletter2')}",
        f"    if not has(149) and has(41) then reward(149, {balanced_experience(20000, 149)}, 3000) end"
        f"{experience_note(20000, 149)}",
        f"    if not has(179) and has(83) then MM9.giveKey(179); "
        f"MM9.giveExperience({balanced_experience(26500, 179)}); MM9.giveGold(6000) end{experience_note(26500, 179)}",
        "end",
        "",
    ]
    script.add(lines + hook_lines + [""], *hooked)

    # --- scripted props --------------------------------------------------------------------------------------------
    lines = ["-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9), TownPortal.scr."]
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
    load = [f"    show({a['Ivsar']}, has(242))   -- NPC90.scr :Init (Sturmford): here once he made it home (242)"]
    load += altar_load
    if "IvsarMarker" in points:
        ix, iy, iz = points["IvsarMarker"]
        # a dead Ivsar never walked home (his :OnStop took no message): only a living one stands at the marker
        load.append(f"    if has(117) and MM9.actorAlive({a['Ivsar']}) then "
                    f"evt.SetMapActorPosition({a['Ivsar']}, {ix}, {iy}, {iz}) end   -- TELP intent")
    load += [f"    if has(15) then MM9.removeActor({a['RUDEProp3']}) end   -- Randverrun.scr :Init",
             "    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (Frosgard's third copy: 106)",
             f"    show({a['Thorolf0']}, thorolf); show({a['Thorolf1']}, thorolf)",
             f"    show({a['CommonerHalfOrcMaleA0']}, not has(451))   -- Retainer.scr: Tesar Olin, hidden while hired"]
    if "ItlorWork" in points:
        tx, ty, tz = points["ItlorWork"]
        load.append(f"    if has(157) then evt.SetMapActorPosition({a['RUDEProp5']}, {tx}, {ty}, {tz}) end   -- NPC49.scr")
    # NPC48.scr :Init (OnPostStartWorld) runs for a living Hatlati only (a dead AI's callbacks do not fire)
    load.append(f"    if has(154) and MM9.actorAlive({a['Hatlati']}) then jailHatlati() end   -- NPC48.scr :Init")
    # The posed people loop their pose and keep their seat's facing (rude_props.py; the presentation is not saved, so
    # every load starts it, as their scripts' OnPostSaveLoad Init do)
    for name, _ in posed_people(build):
        load += hooks.posed[name]
    if "CommonerElfFemaleA1" in a:
        load.append(f"    show({a['CommonerElfFemaleA1']}, not has(454))   -- AkeRetainer.scr: away while hired")
    if "Bjarni" in a:
        load.append(f"    show({a['Bjarni']}, not (has(40) and not has(108)))   -- Bjarni.scr :Init Vanish")
    # The barks (Trigger1/2, PlayerTriggerable, ActivationCount 1: 'blabber' to the RUDEProps, README "Barks").
    def at(name):
        return ", ".join(str(int(round(v))) for v in build.project.native(build.source.properties(name)["Pos"]))
    t1, t2 = (trigger_box(build, build.source.by_name[name]) for name in ("trigger1", "trigger2"))
    lines = [
        "-- The barks: Trigger1 and Trigger2 (once each) send 'blabber'. TryggvaSpeech.scr (RUDEProp0, Tryggva at his",
        "-- table): one of his four drunken lines (Tryygva01-04, at random); ErccSpeech.scr (RudeProp1, Ercc): with no key",
        "-- 113, key 113, ercc01 and, as he passes out, ercc02. At the speaker (MM9: Playsound radius 512).",
        f"local BARKS = {{{{name = \"Trigger1\", box = {{{lua.point(t1[0])}, {lua.point(t1[1])}}}}}, "
        f"{{name = \"Trigger2\", box = {{{lua.point(t2[0])}, {lua.point(t2[1])}}}}}}}",
        "local function barked(name)",
        "    if name == \"Trigger1\" then",
        f"        evt.PlaySoundName(\"voices/cinema/tryygva0\" .. MM9.random(1, 4) .. \".wav\", {at('RUDEProp0')})",
        # :Onblabber LoopAnim conv1 while his line plays (conv1 is not in PeasantSeated: its conv), then :Anim listen
        f"        evt.PlayActorClip({a['RUDEProp0']}, {{\"conv_seated\", \"conv_seated\", \"listen\"}}, true)",
        "    elseif not has(113) then",
        "        MM9.giveKey(113)",
        f"        evt.PlaySoundName(\"voices/cinema/ercc01.wav\", {at('RudeProp1')})",
        # :OnBlabber PlayAnim ercc01a, ercc01b, ercc01c, then ercc02 once (:Passout PlayAnim ercc02 DoNothing: he stays
        # passed out: the townsman's ercc_out loops ercc02's last pose)
        f"        evt.PlayActorClip({a['RUDEProp1']}, "
        "{\"ercc01a\", \"ercc01b\", \"ercc01c\", \"ercc02\", \"ercc_out\"}, true)",
        "        set(\"ErccDue\", 1)",
        f"        evt.StartTimer({T_ERCC}, seconds({ERCC_PASSOUT_SECONDS}))",
        "    end",
        "end",
        f"handlers[{T_ERCC}] = function()",
        f"    evt.StopTimer({T_ERCC})",
        "    if var(\"ErccDue\") ~= 1 then return end",
        "    set(\"ErccDue\", 0)",
        f"    evt.PlaySoundName(\"voices/cinema/ercc02.wav\", {at('RudeProp1')})",
        "end",
        "local function barks()",
        "    local x, y, z = evt.GetPartyPosition()",
        "    for _, t in ipairs(BARKS) do",
        "        local b = t.box",
        "        if var(\"Barked\" .. t.name) == 0 and x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]",
        "                and z >= b[1][3] and z <= b[2][3] then",
        "            set(\"Barked\" .. t.name, 1)",
        "            barked(t.name)",
        "        end",
        "    end",
        "end",
        "local function poll()",
        "    shopHours()",
        "    barks()",
        f"    evt.StartTimer({T_POLL}, seconds(1))",
        "end",
        f"handlers[{T_POLL}] = poll",
        f"handlers[{EV_LOAD}] = function()   -- map load",
        "    for k = 1024, 1033 do if k ~= 1026 and has(k) then MM9.takeKey(k) end end",
        "    MM9.giveKey(1026)",
        "    if var(\"JailOpen\") == 1 then open(\"Jaildoor\") end",
        *load,
        "    poll()",
        "end",
    ]
    script.add(lines, (T_POLL, "Poll", None, "timer"), (EV_LOAD, "Map load", None), (T_ERCC, "Ercc passes out", None,
                                                                                     "timer"))
    return script.finish(on_load=[EV_LOAD])
