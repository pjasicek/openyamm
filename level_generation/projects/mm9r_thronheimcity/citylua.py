"""
Thronheim City's map Lua: the doors (MM9's locked doors say so), the chest, and the scripted objects as native
handlers, each citing its .scr (README.md, "Scripted objects"; the behaviour spec of every script is work/scr_spec.md).

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h). The council RUDEProps (the six Jarls) are posed decorations: a click opens their dialogue.
The Argument (ARGUMENT.scr, a camera scene on a stage under the city) is the in-engine cinematic council_argument
(council.py, filmed in Kira's hall): opening Kira's council door with both signatures (keys 90, 91) starts it; its
steps give the reward ("War"), swap the live Markel for the dead one and let Yrsa appear; Knut's rant is council.py's
too. The breakout of the Desert Terror (Thronheimcity_BadAss.scr) runs on the 1-second poll when the
party walks across one of MM9's two trigger planes by the prison: the Terror walks to the cell's back wall and breaks
it, runs to Shmoe and kills him, and turns on the town; the guards hunt it, and each breakout guard that dies sends a
new one from GuardSpawn0 (Thronheimcity_Guard.scr :OnDeath), the Terror alive or dead (the OnDeath of the dying guard
fires and GuardSpawn0 is no AI, so the dead-receiver rule drops nothing); a guard sent after the Terror's death finds
only its corpse and hunts nothing.
"""

from __future__ import annotations

import csv
import json

from dungeon import lua
from dungeon import town_portal
from dungeon.source import ROOT, SCALE
from quest_xp import balanced_experience, experience_note

import council
import rude_props

LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
EV_LOAD, EV_LOCKED, EV_KIRA_DOOR = 1, 230, 232
T_POLL, T_GUARD = 260, 261
EV_AT_WALL, EV_AT_SHMOE, EV_GUARD_KILLED = 262, 263, 264   # the Terror's walks' arrivals, the breakout guards' deaths
EV_HONK_GONE = 265                  # + k: a persuaded Honk reaches HonkyMarker (Honkies.scr :OnShanghai)
EV_NPC_PROP = 300                   # posed npc props that are not posed people (props.json kind npc): + k
EV_SCRIPTED_PROP = 330              # letters, books, the town portal altar: EV_SCRIPTED_PROP + k
# (KiraShield.scr's shield is a world item, ../mm9r_common/dungeon/pickups.py: taken only with key 214, key 216 on pickup)
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr", "townportal.scr")
COG_PROP = 400                      # SetSprite keys of props scripts show and hide
# ARG_Unhide.scr's council set, NPC239.scr's dead Markel, KiraShield.scr's shield
COUNCIL = ("SvenProp", "TryygvaProp", "MarkeProp", "ForadProp", "SigmundProp", "BjarniProp", "TreatyProp", "BookProp")
PROP_COGS = COUNCIL + ("MarkeProp0",)

# MM9 doors with Locked 1 and no key or script that unlocks them: the facade doors (`Door` objects with MoveDist 0
# or 1), the safe, the guard house, the second inn, the prison cells and the bank vault. A click says so.
LOCKED_GROUPS = ["Door1", "Door2", "Door3", "Door4", "RotatingDoor3", "RotatingDoor13", "InnDoor1", "Prisondoor0",
                 "Prisondoor1", "vaultdoor"]
MOVER_EVENTS = {**{group: (EV_LOCKED, "click") for group in LOCKED_GROUPS}, "KiraDoor1": (EV_KIRA_DOOR, "click")}
MARKERS = ("BadAssWander1", "HonkyMarker", "BenMarker", "GuardSpawn0")
THOROLF0_TARGET_LT = (-2806, 1240, 5040)      # NPC378.scr's Thronheim fix: with key 83 Thorolf0 waits here
# BadAssTrigger / BadAssTrigger0: thin player planes across the two streets by the prison (DAT Pos, Dims)
BREAKOUT_PLANES = (((4312, 1244, 96), (10, 50, 300)), ((3348, 1306, -154), (10, 50, 370)))
GUARD_ROW, BADASS_ROW = 9107, 9238
PRISON_WALL = "PrisonWall"          # the cell's back wall (DestructableBrush): a scene destructible (dungeon/destructibles.py)
# Thronheimcity_Guard.scr :OnDeath sends GuardSpawn0 "Default" (a new PoorTownGuard1 with GetBadAss) for every dead guard
# running the script, the ones it sends too, with no end, the Terror's death included: the dying guard's OnDeath fires
# (a dead AI keeps OnDeath) and the spawner is no AI, so nothing drops the message; the new guard's GetBadAss then gets
# the Terror's corpse (GetObjectHandle on a dead AI) and fights nothing. Here at most this many come in all, so a Terror
# the guards cannot kill (MM9 drops its HitPoints to 250 and AC to 20 at the breakout: not carried) ends the stream.
GUARDS_SENT_CAP = 12
BREAKOUT_TIMEOUT = 12               # seconds the Terror's walks may take before the breakout completes at once (TELP 1.3:
                                    # MM9's own Terror could stall at the broken wall)


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


def posed_people(build=None) -> list:
    """props.json's posed people placed as actors (../mm9r_common/rude_props.py): the six council Jarls (PropAnim
    "Sit"), in file order: [(name, entry)]. Until 2026-11-08 they were posed decorations (MM9's ABC poses); the user
    asked for their own HD models, seated."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    return [(e["source_name"], e) for e in entries if rude_props.is_posed_person(e)]


def scripted_props(build=None) -> tuple[list, list]:
    """props.json's other posed npc props and scripted props, in file order: [(name, entry)] each."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    npcs = [(e["source_name"], e) for e in entries if e["kind"] == "npc" and not rude_props.is_posed_person(e)]
    scripted = [(e["source_name"], e) for e in entries
                if str(e.get("script") or "").lower().replace("scripts\\", "") in SCRIPTED_PROP_SCRIPTS]
    return npcs, scripted


def prop_events(build=None) -> dict:
    """DAT prop name -> click event: the posed Jarls and the scripted props."""
    npcs, scripted = scripted_props(build)
    events = {name: EV_NPC_PROP + k for k, (name, _) in enumerate(npcs)}
    events.update({name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted)})
    return events


def prop_cogs(build=None) -> dict:
    """SetSprite keys of the decorations the scripts show and hide (the posed Jarls are actors, no decorations)."""
    from convert import PROPS
    posed = {name for name, _ in posed_people(build)}
    names = [e["source_name"] for e in json.loads(PROPS.read_text()) if e["source_name"] not in posed] \
        if PROPS.exists() else []
    return {name: COG_PROP + k for k, name in enumerate(PROP_COGS) if name in names}


def native_on_floor(build, lt) -> list | None:
    floor = build.content.floor_at(lt[0], lt[2], lt[1] + 16)
    if floor is None:
        return None
    return build.project.native([lt[0], floor, lt[2]]).round().astype(int).tolist()


def marker_points(build) -> dict:
    """The MM9 markers the scripts walk people to, as native points on the floor under them."""
    points = {}
    for name in MARKERS:
        found = build.source.by_name.get(name.lower())
        if found is not None:
            point = native_on_floor(build, found["properties"]["Pos"])
            if point is not None:
                points[name] = point
    points["Thorolf0Target"] = native_on_floor(build, THOROLF0_TARGET_LT)
    return points


def council_actors(hooks) -> dict:
    """council.py's roles -> scene actor indices: the seated Jarls (the posed people) and Kira's stage actor
    (convert.py), Kira the Cold, Yrsa, Knut, Ake."""
    a = hooks.actor
    roles = {role: a[council.POSED_JARLS[role]] if role in council.POSED_JARLS else a[f"Stage{name}"]
             for role, name, *_ in council.STAGE_ACTORS}
    roles.update(kira_cold=a["KiraCold"], yrsa=a["YrsatheTroll0"], knut=a["CommonerHuman2MaleB0"], ake=a["Ake"])
    return roles


def map_script(hooks, build) -> str:
    script = lua.Script(build, "Thronheim City")
    script.doors()
    script.chests()
    a, o, points = hooks.actor, hooks.objects, hooks.points
    npcs, scripted = scripted_props(build)
    cogs = prop_cogs(build)
    kira_leaves = [m["node"][5:] for m in build.movers if m["group"] == "KiraDoor1"]
    planes = []
    for (x, y, z), (dx, dy, dz) in BREAKOUT_PLANES:
        planes.append("{x = %d, y0 = %d, y1 = %d}" % (round(x * SCALE), round((z - dz) * SCALE), round((z + dz) * SCALE)))
    lines = [
        "local function has(k) return MM9.hasKey(k) == 1 end",
        "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function sprite(cog, on) if cog then evt.SetSprite(cog, on and 1 or 0, \"0\") end end",
        "local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; "
        "if gold > 0 then MM9.giveGold(gold) end; quest() end",
        "local COG = {" + ", ".join(f"{name} = {cog}" for name, cog in cogs.items()) + "}",
        "",
        "-- MM9's locked doors (Locked 1, no key): facade doors, the safe, the guard house, the second inn, the cells,",
        "-- the bank vault.",
        f"handlers[{EV_LOCKED}] = function()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        "",
        "-- ForadWorld.scr (ScriptObject0, \"Thronheim\"): key 1030 is the party's location while here (keys 1024-1033",
        "-- are the towns'); key 5017 closes the shops and the bank from 20:00 to 06:00.",
        "local function shopHours()",
        "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
        "    local closed = hour >= 20 or hour < 6",
        "    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end",
        "end",
        "",
        "-- ARG_Unhide.scr: the six Jarls, the book and the treaty sit in Kira's council room from both signatures (keys 90,",
        "-- 91) until Bikki's prize is won (94); Markel alive until the council (40). NPC239.scr removes the dead Markel",
        "-- (MarkeProp0) on every load after it. The Jarls are actors on their HD models looping Sit (rude_props.py).",
        "local function councilProps()",
        "    local council = has(90) and has(91) and not has(94)",
    ]
    for name, _ in posed_people(build):
        on = "council and not has(40)" if name == "MarkeProp" else "council"
        lines.append(f"    show({a[name]}, {on})   -- {name}")
    for name in COUNCIL:
        if name in cogs:
            on = "council and not has(40)" if name == "MarkeProp" else "council"
            lines.append(f"    sprite(COG.{name}, {on})")
    lines += ["    sprite(COG.MarkeProp0, false)" if "MarkeProp0" in cogs else "", "end", ""]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"))

    # --- the war council ---------------------------------------------------------------------------------------
    calls = " ".join(f"evt.SetDoorState(DOORS[\"{leaf}\"], DoorAction.Trigger)" for leaf in kira_leaves)
    lines = [
        "-- ARGUMENT.scr (Argueman; KiraDoor2 sends it \"start\" when it opens): with both Jarls' signatures (keys 90, 91)",
        "-- and no council yet (40), the war council: the cinematic council_argument (council.py; its steps are the",
        "-- cinematic block at the end of this file). :War, the reward: keys 184, 40, 85 and 93, 26 500 experience, the",
        "-- Peace Treaty (401) taken. Forad leaves the party at :Cam2b (RemoveNPC 2: the MM9 hireling; key 29 stays).",
        "local function war()",
        "    if has(184) then return end",
        f"    MM9.giveKey(184); MM9.giveKey(40); MM9.giveKey(85); "
        f"MM9.giveExperience({balanced_experience(26500, 85)}); "
        f"quest(){experience_note(26500, 85)}",
        "    MM9.takeItem(401, \"thronheimcity:Kira\")",
        "    MM9.giveKey(93)",
        "end",
        f"handlers[{EV_KIRA_DOOR}] = function()   -- KiraDoor1/2",
        f"    {calls}",
        f"    if has(90) and has(91) and not has(40) then MM9Cinematic.start(\"{council.CINEMA_ID}\") end",
        "end",
        "",
        "-- ARG_Yrsa.scr (Yrsa the Troll, RUDE 1): she appears after the council; talking gives key 93 (her errand: the",
        "-- prize at the Thing in Thjorgard), the exit gives 185 and she vanishes. MM9 shows her only during that",
        "-- session; here she also waits on later visits until 185 (README).",
        f"handlers[{rude_use_event(o['YrsatheTroll0'])}] = function()",
        "    MM9.giveKey(93)",
        "    MM9.openRude(1)",
        "end",
        f"handlers[{rude_exit_event(o['YrsatheTroll0'])}] = function()",
        "    if not has(185) and has(93) then",
        "        quest(); MM9.giveKey(185)",
        f"        MM9.clientFx({a['YrsatheTroll0']}, \"mm9:GreaterDemon\")   -- :Vanish: DoClientFX g_hMyObject, GreaterDemon",
        f"        MM9.removeActor({a['YrsatheTroll0']})",
        "    end",
        "end",
        "",
        "-- NPC239.scr (Kira the Cold, RUDE 239): a click with all five clan keys (34, 38, 51, 63, 74) gives 178; the",
        "-- exit pays the love letter (147, item 247 taken), the Honkies gone (146), the Mountain Pass (152), the clans",
        "-- united (179) and the treaty written (181, item 401 given).",
        f"handlers[{rude_use_event(o['KiraCold'])}] = function()",
        "    if not has(178) and has(34) and has(38) and has(51) and has(63) and has(74) then MM9.giveKey(178) end",
        "    MM9.openRude(239)",
        "end",
        f"handlers[{rude_exit_event(o['KiraCold'])}] = function()",
        "    if not has(147) and has(23) then",
        f"        MM9.takeItem(247, \"thronheimcity:Kira\"); reward(147, {balanced_experience(12000, 147)}, 0)",
        "    end",
        f"    if not has(146) and has(78) then reward(146, {balanced_experience(40000, 146)}, 7000) end"
        f"{experience_note(40000, 146)}",
        f"    if not has(152) and has(81) then reward(152, {balanced_experience(120000, 152)}, 12000) end"
        f"{experience_note(120000, 152)}",
        f"    if not has(179) and has(83) then MM9.giveKey(179); "
        f"MM9.giveExperience({balanced_experience(26500, 179)}); MM9.giveGold(6000) end{experience_note(26500, 179)}",
        "    if not has(181) and has(89) then",
        f"        reward(181, {balanced_experience(12000, 181)}, 0); MM9.giveItem(401, \"thronheimcity:Kira\")",
        "    end",
        "end",
        "-- NPC239.scr's clock (@M 6:00): agreed to write the treaty (88) -> 180 at the next 06:00. MM9 fires it only",
        "-- with the map loaded; here the poll gives it once a 06:00 has passed since the poll first saw key 88.",
        "local function kiraClock()",
        "    if has(180) or not has(88) then return end",
        "    local mark = math.floor((evt.CurrentGameMinutes() - 360) / 1440) + 2",
        "    if var(\"Kira88\") == 0 then set(\"Kira88\", mark) elseif mark > var(\"Kira88\") then MM9.giveKey(180) end",
        "end",
        "",
    ]
    script.add(lines, (EV_KIRA_DOOR, "Door", "Door"),
               (rude_use_event(o["YrsatheTroll0"]), "Yrsa", None), (rude_exit_event(o["YrsatheTroll0"]), "Yrsa", None),
               (rude_use_event(o["KiraCold"]), "Kira", None), (rude_exit_event(o["KiraCold"]), "Kira", None))

    # --- the council's aftermath (Yrsa) and Knut's rant (council.py) -----------------------------------------------
    council_lines, council_timers = council.extra_lua(council_actors(hooks))
    script.add(council_lines, *council_timers)

    # --- the townsfolk's scripts -------------------------------------------------------------------------------
    honks = (("CommonerHumanMaleA1", 142), ("CommonerHumanFemaleA1", 143), ("CommonerHumanFemaleA0", 144))
    lines = [
        "-- HONKIES.scr (the three Honk missionaries, RUDE 271, 272, 279): with the dock captain's plan (key 145), each one",
        "-- persuaded (142, 143, 144) leaves for the docks (:Walk: runs to HonkyMarker, gone there: :OnShanghai);",
        "-- the third gives key 77 and 8 000 experience. Gone on 77 (a load removes the persuaded ones at once).",
        "-- (MM9 sends every Honk whose dialogue closes with 145 and any of the three keys; here only the persuaded one.)",
        f"local HONKY_MARKER = {{{', '.join(map(str, points['HonkyMarker']))}}}",
        "local function honkLeaves(actor, arrival)",
        "    local m = HONKY_MARKER",
        "    if not evt.MoveActorTo(actor, m[1], m[2], m[3], arrival, true) then MM9.removeActor(actor) end",
        "end",
        "local function honksDone()",
        "    local n = 0",
        "    for _, k in ipairs({142, 143, 144}) do if has(k) then n = n + 1 end end",
        f"    if n == 3 and not has(77) then reward(77, {balanced_experience(8000, 77)}, 0) end",
        "end",
    ]
    for k, (name, key) in enumerate(honks):
        lines += [f"handlers[{rude_exit_event(o[name])}] = function()",
                  f"    if has(145) and has({key}) then honkLeaves({a[name]}, {EV_HONK_GONE + k}); honksDone() end",
                  "end",
                  f"handlers[{EV_HONK_GONE + k}] = function() MM9.removeActor({a[name]}) end"]
    lines += [
        "",
        "-- BANKORB.scr (Brynhildr the Money-wise, RUDE 243, \"Thronheim\"): the Orb of Linking. A click with the orb",
        "-- (item 252) after the quest (322) unlocks the row that installs it (330); the exit places it (331 -> 328) and",
        "-- the sixth bank's orb pays 20 000 experience and 15 000 gold (337; banks' keys 331-336).",
        f"handlers[{rude_use_event(o['brynhildr'])}] = function()",
        "    if not has(328) and has(322) and MM9.hasItem(252, \"thronheimcity:Bank\") == 1 then MM9.giveKey(330) end",
        "    MM9.openRude(243)",
        "end",
        f"handlers[{rude_exit_event(o['brynhildr'])}] = function()",
        "    if has(330) then MM9.takeKey(330) end",
        "    if not has(331) or has(328) then return end",
        "    quest(); MM9.takeItem(252, \"thronheimcity:Bank\"); MM9.giveKey(328)",
        "    if has(337) then return end",
        "    for k = 331, 336 do if not has(k) then return end end",
        f"    reward(337, {balanced_experience(20000, 337)}, 15000){experience_note(20000, 337)}",
        "end",
        "",
        "-- NPC241.scr (Ealusaid A'Norta a'thrakan, RUDE 241): the Black Orb's inventor found (314): 50 000 experience,",
        "-- 10 000 gold, the Black Orb (item 250) taken (315).",
        f"handlers[{rude_exit_event(o['Ealusaid'])}] = function()",
        f"    if not has(315) and has(314) then reward(315, {balanced_experience(50000, 315)}, 10000); "
        f"MM9.takeItem(250, \"thronheimcity:Ealusaid\") end{experience_note(50000, 315)}",
        "end",
        "-- NPC242.scr (Dagfari the Peevish, RUDE 242) and NPC246.scr (Erlend the Nay-sayer, RUDE 246): the Scroll of",
        "-- Bad News (item 251). Dagfari hands it over (316 -> 317), Erlend takes it (318 -> 319), Dagfari pays (320 ->",
        "-- 321, 5 000 experience, 5 000 gold).",
        f"handlers[{rude_exit_event(o['dagfaripeevish'])}] = function()",
        "    if not has(317) and has(316) then MM9.giveItem(251, \"thronheimcity:Dagfari\"); MM9.giveKey(317) end",
        f"    if not has(321) and has(320) then reward(321, {balanced_experience(5000, 321)}, 5000) end",
        "end",
        f"handlers[{rude_exit_event(o['CommonerHuman2MaleA8'])}] = function()",
        "    if not has(319) and has(318) then MM9.giveKey(319); MM9.takeItem(251, \"thronheimcity:Erlend\") end",
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
    regs = [(rude_exit_event(o[name]), "Honk", None) for name, _ in honks]
    regs += [(EV_HONK_GONE + k, "Honk", None) for k in range(len(honks))]
    regs += [(rude_use_event(o["brynhildr"]), "Bank", None), (rude_exit_event(o["brynhildr"]), "Bank", None),
             (rude_exit_event(o["Ealusaid"]), "Ealusaid", None), (rude_exit_event(o["dagfaripeevish"]), "Dagfari", None),
             (rude_exit_event(o["CommonerHuman2MaleA8"]), "Erlend", None)]
    regs += [(f(o[n]), "Thorolf", None) for n in ("Thorolf0", "Thorolf1") for f in (rude_use_event, rude_exit_event)]
    script.add(lines, *regs)

    # --- the breakout ------------------------------------------------------------------------------------------
    from convert import GROUP_BADASS, GROUP_EXTRA_GUARD, GROUP_GUARDS
    bad, shmoe, extra = a["BadAss"], a["Shmoe"], a["ExtraGuard"]
    ben = a.get("Ben")
    guard1 = a.get("Guard1")
    wall = build.source.by_name[PRISON_WALL.lower()]["index"]
    # the guards running Thronheimcity_Guard.scr (its OnDeath): Guard1, Guard2 and GuardSpawn1's extra guard
    script_guards = [a[name] for name in ("Guard1", "Guard2", "ExtraGuard") if name in a]
    wall_marker, spawn_point = points["BadAssWander1"], points["GuardSpawn0"]
    ben_marker = points.get("BenMarker")
    lines = [
        "-- Thronheimcity_BadAss.scr: the Desert Terror in the prison cell breaks out when the party walks across one",
        "-- of the two trigger planes by the prison (BadAssTrigger, BadAssTrigger0; no key gate in MM9). :OnBreakOut: it",
        "-- walks to BadAssWander1 by the cell's back wall and breaks the wall (:AttackWall, :DestroyWall: the scene",
        "-- destructible's crumble and dust); :WallBroken sends Shmoe and Ben its HereComesBadAss (Ben runs to BenMarker);",
        "-- it runs to Shmoe and kills him (:KillShmoe), then turns on the town (:Taunt3Done: Ben runs to Guard1 for help,",
        "-- and 6 s later :GetExtraGuard brings the guard at GuardSpawn1). The guards become MM9's town guards again (their",
        "-- peasant relations dropped, still the party's friends), whom relations.yml sets against MM9's monsters, the",
        "-- Terror. MM9's taunts, the townsfolk's flight (SendRunAway) and its HitPoints 250 / AC 20 are not carried. A",
        f"-- walk not done in {BREAKOUT_TIMEOUT} s, and a load mid-breakout (walks are not saved), finish it at once.",
        "local PLANES = {" + ", ".join(planes) + "}",
        f"local TERROR, SHMOE, EXTRA_GUARD, WALL = {bad}, {shmoe}, {extra}, {wall}",
        f"local WALL_MARKER, GUARD_SPAWN = {lua.point(wall_marker)}, {lua.point(spawn_point)}",
        "local SCRIPT_GUARDS = {" + ", ".join(f"[{i}] = true" for i in script_guards) + "}",
        "local function loose()",
        f"    evt.ChangeGroupAlly({GROUP_GUARDS}, 0); evt.ChangeGroupAlly({GROUP_EXTRA_GUARD}, 0)",
        f"    evt.SetMonGroupBit({GROUP_GUARDS}, MonsterBits.Hostile, false)",
        f"    evt.SetMonGroupBit({GROUP_EXTRA_GUARD}, MonsterBits.Hostile, false)",
        f"    evt.SetMonGroupBit({GROUP_BADASS}, MonsterBits.Hostile, true)",
        "    -- :Taunt3Done's BaseInit: MM9's own monster AI from here (the placement held it still in its cell)",
        "    evt.SetActorImmobile(TERROR, false)",
        "end",
        "local function alive() return var(\"BadAssDead\") == 0 end",
        "-- Thronheimcity_Guard.scr :GetBadAss: the guard takes the Terror as its target (g_hTarget = hBadAss,",
        "-- SetupTarget, AggressiveStart) and fights it on its own AI.",
        "local function hunt(index)",
        "    if var(\"BadAssStage\") ~= 3 or not alive() then return end",
        "    evt.SetActorTarget(index, TERROR)",
        "end",
        "local function hunters()",
        "    local list = var(\"GuardOut\") == 1 and {EXTRA_GUARD} or {}",
        "    for k = 1, var(\"GuardsSent\") do list[#list + 1] = var(\"GuardSent\" .. k) - 1 end",
        "    return list",
        "end",
        "-- Thronheimcity_Guard.scr :OpenEyes (GetExtraGuard sends it to Guard1 only): Guard1 wakes from its sleep at",
        "-- its post (DisableWandering, GotoSleep) and finds its target again (OnFoundTarget): the Terror loose in the",
        "-- town, given it here (far from the party the guard would not look).",
        "local function openEyes()",
        *([f"    evt.WakeActor({guard1})", f"    hunt({guard1})"] if guard1 is not None else []),
        "end",
        "local function freed()   -- :Taunt3Done",
        "    if var(\"BadAssStage\") == 3 then return end",
        "    -- the Terror's own walks, attacks and taunts (callbacks and waits it set while alive): a Terror that died",
        "    -- on the way does none of it (a dead AI's callbacks do not fire): the wall and Shmoe stay as they are",
        "    if not MM9.actorAlive(TERROR) then return end",
        "    evt.StopActorMove(TERROR)",
        "    evt.DestroyDestructible(WALL)",
        "    evt.KillMapActor(SHMOE)",
        "    set(\"BadAssStage\", 3)",
        "    loose()",
    ]
    if ben is not None:
        # :Taunt3Done: Target Ben, TRUE, then BaseInit: the Terror goes for Ben, who runs to Guard1 for help,
        # bringing it to the guards (the party is no first target of the breakout)
        lines += [f"    if MM9.actorAlive({ben}) then evt.SetActorTarget(TERROR, {ben}) end"]
    if ben is not None and guard1 is not None:
        lines += [f"    local gx, gy, gz = evt.GetMapActorPosition({guard1})",
                  f"    if gx ~= nil and MM9.receives(\"thronheimcity\", \"Ben\", \"RunAwayFromMe\", {ben}) then",
                  f"        evt.MoveActorTo({ben}, gx, gy, gz, 0, true)   -- Ben: RunAwayFromBadAss",
                  "    end"]
    lines += [
        f"    if var(\"GuardOut\") ~= 1 then set(\"GuardArm\", 1); evt.StartTimer({T_GUARD}, seconds(6)) end",
        "end",
        f"handlers[{EV_AT_WALL}] = function()   -- :AtWallMarker, :AttackWall, :DestroyWall, :WallBroken",
        "    if not MM9.actorAlive(TERROR) then return end   -- its walk's arrival: no callback once dead",
        "    if var(\"BadAssStage\") ~= 1 then return end",
        "    set(\"BadAssStage\", 2)",
        "    evt.DestroyDestructible(WALL)",
    ]
    if ben is not None and ben_marker is not None:
        lines += [f"    if MM9.receives(\"thronheimcity\", \"Ben\", \"HereComesBadAss\", {ben}) then",
                  f"        evt.MoveActorTo({ben}, {', '.join(str(v) for v in ben_marker)}, 0, true)   -- Ben: "
                  "OnHereComesBadAssBen",
                  "    end"]
    lines += [
        "    local x, y, z = evt.GetMapActorPosition(SHMOE)",
        f"    if x == nil or not evt.MoveActorTo(TERROR, x, y, z, {EV_AT_SHMOE}, true) then freed() end",
        "end",
        f"handlers[{EV_AT_SHMOE}] = function() if var(\"BadAssStage\") == 2 then freed() end end   -- :KillShmoe",
        "local function breakout()",
        "    set(\"BadAssOut\", 1); set(\"BadAssStage\", 1); set(\"BadAssClock\", 0)",
        "    if not evt.MoveActorTo(TERROR, WALL_MARKER[1], WALL_MARKER[2], WALL_MARKER[3], "
        f"{EV_AT_WALL}) then freed() end",
        "end",
        "local function breakoutClock()",
        "    if var(\"BadAssOut\") ~= 1 or var(\"BadAssStage\") == 3 then return end",
        "    set(\"BadAssClock\", var(\"BadAssClock\") + 1)",
        f"    if var(\"BadAssClock\") > {BREAKOUT_TIMEOUT} then freed() end",
        "end",
        f"handlers[{T_GUARD}] = function()   -- :GetExtraGuard",
        "    if var(\"GuardArm\") ~= 1 then return end",
        "    set(\"GuardArm\", 0); set(\"GuardOut\", 1)",
        "    show(EXTRA_GUARD, true)",
        "    hunt(EXTRA_GUARD)",
        "    openEyes()",
        "end",
        "-- Thronheimcity_Guard.scr :OnDeath: a dead guard of the script (and every one it sends) sends a new PoorTownGuard1",
        "-- from GuardSpawn0 (the dying guard's OnDeath fires and the spawner is no AI: MM9 sends it whether or not the",
        "-- Terror lives), hunting the Terror while it lives (hunt), at most "
        f"{GUARDS_SENT_CAP} in all (GUARDS_SENT_CAP).",
        "-- No loot (GaveTreasure); the party's friend, as the town's guards.",
        f"handlers[{EV_GUARD_KILLED}] = function(context)",
        "    local i = context.actorIndex",
        "    if i == nil then return end",
        "    if i == TERROR then set(\"BadAssDead\", 1) return end",
        "    local ours = SCRIPT_GUARDS[i] == true",
        "    for k = 1, var(\"GuardsSent\") do if var(\"GuardSent\" .. k) == i + 1 then ours = true end end",
        f"    if not ours or var(\"GuardsSent\") >= {GUARDS_SENT_CAP} then return end",
        f"    local _, made = evt.SummonMonstersById({{monster = {GUARD_ROW}, x = GUARD_SPAWN[1], y = GUARD_SPAWN[2], "
        f"z = GUARD_SPAWN[3], radius = 32, count = 1, group = {GROUP_EXTRA_GUARD}, hostile = false, loot = false}})",
        "    if made == nil or made[1] == nil then return end",
        "    set(\"GuardsSent\", var(\"GuardsSent\") + 1)",
        "    set(\"GuardSent\" .. var(\"GuardsSent\"), made[1] + 1)",
        f"    evt.SetMonGroupBit({GROUP_EXTRA_GUARD}, MonsterBits.Hostile, false)",
        "    hunt(made[1])",
        "end",
        "local function crossings()",
        "    local x, y, z = evt.GetPartyPosition()",
        "    local px, py = var(\"PrevX\"), var(\"PrevY\")",
        "    set(\"PrevX\", math.floor(x)); set(\"PrevY\", math.floor(y))",
        "    if var(\"BadAssOut\") == 1 or var(\"Polled\") == 0 then set(\"Polled\", 1) return end",
        "    if math.abs(x - px) + math.abs(y - py) > 1500 then return end   -- a teleport, not a walk",
        "    for _, p in ipairs(PLANES) do",
        "        -- the walk from the last poll crosses the plane's line within its span (where it crosses, not where",
        "        -- the party stands now: a diagonal walk can leave the span within a poll)",
        "        local cy = (px - p.x) * (x - p.x) <= 0 and px ~= x and py + (y - py) * (p.x - px) / (x - px) or nil",
        "        if cy ~= nil and cy >= p.y0 - 64 and cy <= p.y1 + 64 then",
        "            -- the plane's Breakout is a message to the Terror: a dead one takes none (MM9.receives)",
        "            if MM9.receives(\"thronheimcity\", \"BadAss\", \"Breakout\", TERROR) then breakout() end",
        "            return",
        "        end",
        "    end",
        "end",
        "",
    ]
    script.add(lines, (T_GUARD, "Guard", None, "timer"), (EV_AT_WALL, "Breakout", None),
               (EV_AT_SHMOE, "Breakout", None))
    script.hooks.append(f'RegisterMonsterKilledHook({EV_GUARD_KILLED}, "Breakout guards", handlers[{EV_GUARD_KILLED}])')

    # --- posed Jarls and scripted props ------------------------------------------------------------------------
    lines = ["-- The council's RUDEProps (PropAnim \"Sit\"): a click opens the Jarl's dialogue."]
    for k, (name, entry) in enumerate(npcs):
        rude = entry.get("rude_npc_id")
        lines.append(f"handlers[{EV_NPC_PROP + k}] = function() MM9.openRude({rude}) end   -- {name} (RUDE {rude})")
        script.registrations.append((EV_NPC_PROP + k, name, "Talk", "event"))
    lines += ["", "-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (no text in MM9),",
              "-- KiraShield.scr, TownPortal.scr."]
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

    # --- map load and the poll ---------------------------------------------------------------------------------
    load = [
        "    councilProps()",
        f"    show({a['KiraCold']}, not has(40) or has(108))   -- NPC239.scr :Init",
        f"    if has(185) then MM9.removeActor({a['YrsatheTroll0']}) else show({a['YrsatheTroll0']}, has(40)) end",
        "    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init (only Frosgard's third copy comes on 106)",
        f"    show({a['Thorolf0']}, thorolf); show({a['Thorolf1']}, thorolf)",
    ]
    load += altar_load
    # The seated Jarls loop Sit and keep their seat's facing (rude_props.py; the presentation is not saved, so every
    # load starts it, as PropAnim.scr's Init does)
    for name, _ in posed_people(build):
        load += hooks.posed[name]
    if points.get("Thorolf0Target"):
        tx, ty, tz = points["Thorolf0Target"]
        load.append(f"    if has(83) then evt.SetMapActorPosition({a['Thorolf0']}, {tx}, {ty}, {tz}) end")
    load += [
        f"    show({a['CommonerHuman2MaleA7']}, not has(461))   -- Retainer.scr: Cleirach A'Lyrae, hidden while hired",
        "    if has(77) then   -- Honkies.scr :Init",
        *[f"        MM9.removeActor({a[name]})" for name, _ in honks],
        "    else",
        *[f"        if has(145) and has({key}) then MM9.removeActor({a[name]}) end" for name, key in honks],
        "    end",
        f"    if var(\"GuardOut\") == 1 then show({extra}, true); openEyes() end",
        "    if var(\"BadAssOut\") == 1 and var(\"BadAssStage\") ~= 3 then freed()   -- walks are not saved",
        "    elseif var(\"BadAssOut\") == 1 then loose(); for _, h in ipairs(hunters()) do hunt(h) end end",
        "    set(\"Polled\", 0)",
    ]
    lines = [
        "local function poll()",
        "    shopHours()",
        "    kiraClock()",
        "    crossings()",
        "    breakoutClock()",
        f"    evt.StartTimer({T_POLL}, seconds(1))",
        "end",
        f"handlers[{T_POLL}] = poll",
        f"handlers[{EV_LOAD}] = function()   -- map load",
        "    for k = 1024, 1033 do if k ~= 1030 and has(k) then MM9.takeKey(k) end end",
        "    MM9.giveKey(1030)",
        *load,
        "    poll()",
        "end",
    ]
    script.add(lines, (T_POLL, "Poll", None, "timer"), (EV_LOAD, "Map load", None))
    return script.finish(on_load=[EV_LOAD])
