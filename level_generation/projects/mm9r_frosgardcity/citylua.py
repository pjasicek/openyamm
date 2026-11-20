"""
Frosgard City's map Lua: the doors (MM9's locked doors say so), the bank's hatch, the harbour's ice and the scripted
objects as native handlers, each citing its .scr (README.md, "Scripted objects"; behaviour spec: work/scr_spec.md).

Hooks: an actor's RUDE exit is event 50000 + its DAT object index, a click that runs before its dialogue 53000 + index
(game/mm9/Mm9RudeDialogue.h). Decorations a script shows or hides have a cog (evt.SetSprite(cog, visible, "0")).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cutscenes
from dungeon import lua
from dungeon import town_portal
from dungeon.objects import bonus_call
from dungeon.source import ROOT
from quest_xp import balanced_experience, experience_note

LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
EV_LOAD, EV_LOCKED, EV_BANK, EV_BARREL, EV_WELL, EV_TRIGGER0 = 1, 230, 231, 232, 233, 234
T_POLL = 260
T_CANNON = 235                      # FrosgardShooter.scr's volley: one shot every 0.4 s
EV_FORAD_DEATH = 236                # Forad.scr :OnDeath: his death after the betrayal (monster killed hook)
EV_SCRIPTED_PROP = 330              # letters, the book, the town portal altar: EV_SCRIPTED_PROP + k
SCRIPTED_PROP_SCRIPTS = ("book.scr", "bookletter.scr", "townportal.scr")
# Decorations a script shows or hides: the maypole pair (ChangeModel.scr, key 268), the runestone (HideModel.scr 278),
# the powder barrel on the ice (NPC215.scr, key 1022)
COGS = {"Prop0": 401, "Prop0Maypole": 402, "Prop1": 403, "DestructableProp0": 404}
PROP_EVENTS = {"DestructableProp0": EV_BARREL, "WellMMIX0": EV_WELL}
GROUP_FORAD, GROUP_TAMUR, GROUP_HORDE, GROUP_CLAN = 4, 5, 6, 7
HORDE_ROWS = (9129, 9130, 9131)      # MM9 Horde A/B/C: BattleMan.scr's HordeGrunt, HordeLeader, HordeWarrior
CLAN_ROW = 9107                      # MM9 107 Town Guard: the clan soldiers (no MM9 row of their own)

# MM9 doors with Locked 1 and no key, script or trigger that unlocks them: the facades' doors (`Door` objects with
# MoveDist 0). A click says the door is locked (MM9 jiggles it).
LOCKED_GROUPS = ["Door0", "Door1", "Door2", "Door4", "Door5", "Door6", "Door8", "Door9", "Door10", "Door11", "Door12",
                 "Door14", "Door15", "Door16", "Door17", "Door18", "Door19", "Door20", "Door21", "Door22", "Door23"]
MOVER_EVENTS = {**{group: (EV_LOCKED, "click") for group in LOCKED_GROUPS}, "Bankdoor": (EV_BANK, "click")}
# The harbour's ice floes (BreakIce.scr): the order its cinema breaks them in (:FadeIn .. :Destroy25, :Group1-3)
ICE_STAGES = [[27, 6, 17, 18, 16], [15, 26, 25], [14, 21, 24, 30, 33, 36, 39, 42, 45, 9],
              [19, 22, 28, 31, 34, 37, 40, 43, 7], [20, 23, 29, 32, 35, 38, 41, 44, 8]]
ICE_ALL = sorted({k for stage in ICE_STAGES for k in stage} | {46})
# BreakIce.scr's cinema as the cinematic break_ice (frosgardcity.cinematics.yml; README "Cinematics"): the done event
# and its gameplay steps 36001.. (free: the map's object events end at 30721, the damaged ones at 34721)
BREAK_ICE = "break_ice"
EV_BREAK_ICE = 36000
# NPC214.scr / NPC213.scr's banter (Douglas and Robert, key 111) as the cinematic bob_and_doug: no cameras
BOB_AND_DOUG = "bob_and_doug"
EV_BOB_AND_DOUG = 36050
BANTER_SIGHT_LT = 600.0             # Douglas's SightDistance: his OnFoundPlayer starts it
MARKERS = ("Atlimarker", "BadGuys0", "BadGuys1", "BadGuys2", "BadGuys3", "GoodGuys", "GoodGuys0")
# PLEDGE.inc's pledge drive: the townsfolk whose dialogue exit counts the pledges (NPC191/193/195/196/197/199.scr and
# Pledge.scr's 217, 218; NPC190's exit runs it before the maypole)
PLEDGE_OBJECTS = ("191", "193", "195", "196", "197", "199", "217", "218")
# United.inc's :TryygvaInit, the five other clans: Kira 82, Bjarni 38, Sigmund 51, Markel 63, Sven 34 -> 178
# (Tryygva's own pledge, 74, is not in his list; until 2026-11-08 Sven's list was used here)
CLAN_KEYS = (82, 38, 51, 63, 34)


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
    """props.json's scripted props, in file order: [(name, entry)]."""
    from convert import PROPS
    entries = json.loads(PROPS.read_text()) if PROPS.exists() else []
    return [(e["source_name"], e) for e in entries
            if e["kind"] == "prop" and str(e.get("script") or "").lower().replace("scripts\\", "")
            in SCRIPTED_PROP_SCRIPTS]


def prop_events(build) -> dict:
    """DAT prop name -> click event: the scripted props, the powder barrel, the well."""
    events = {name: EV_SCRIPTED_PROP + k for k, (name, _) in enumerate(scripted_props(build))}
    events.update(PROP_EVENTS)
    return events


def prop_cogs(build) -> dict:
    return dict(COGS)


def marker_points(build) -> dict:
    """The MM9 markers the battle spawns at, as native points on the floor under them."""
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
    script = lua.Script(build, "Frosgard City")
    script.doors()
    script.chests()
    a, o = hooks.actor, hooks.objects
    points = marker_points(build)
    scripted = scripted_props(build)
    ice = [m["node"][5:] for m in build.movers if m["group"].startswith("Ice")]
    # the bank's hatch has only invisible faces (MM9's Bankdoor: an Invisible slab in the counter's opening; the grille
    # is Bankwindow): its mover is Bankdoor_INV
    bank = [m["node"][5:] for m in build.movers if m["group"] == "Bankdoor"]
    lines = [
        "local function has(k) return MM9.hasKey(k) == 1 end",
        "local function quest() MM9.playSound(\"sounds/events/quest.wav\") end",
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; "
        "if gold > 0 then MM9.giveGold(gold) end; quest() end",
        "local function cog(c, on) evt.SetSprite(c, on and 1 or 0, \"0\") end",
        "",
        "-- MM9's locked doors (Locked 1, no key): the facades' doors.",
        f"handlers[{EV_LOCKED}] = function()",
        "    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0)",
        "    evt.StatusText(\"The door is locked.\")",
        "end",
        "",
        "-- ForadWorld.scr (ScriptObject0, \"Frosgard\"): key 1029 is the party's location while here (keys 1024-1033",
        "-- are the towns'); key 5017 closes the shops from 20:00 to 06:00.",
        "local function shopHours()",
        "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
        "    local closed = hour >= 20 or hour < 6",
        "    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end",
        "end",
        "",
        "-- NPC206.scr / BankOrb.inc (the banker Cormac A'Ghrie, RUDE 206) and the bank's counter hatch (Bankdoor: its",
        "-- OpenTrigger sends the banker \"bank\"): a click on the hatch opens it and the banker's dialogue; with the orb",
        "-- quest (322) and the Orb of Linking (item 252) the row that installs it is unlocked (330).",
        "local BANK = {" + ", ".join(f'"{n}"' for n in bank) + "}",
        "local function bankHatch(on) for _, n in ipairs(BANK) do if on then open(n) else close(n) end end end",
        "local function bankDialogue()",
        "    if has(322) and MM9.hasItem(252, \"frosgardcity:Banker\") == 1 then MM9.giveKey(330) end",
        f"    MM9.openRude(206, {a['Banker']})   -- the banker speaks (from the hatch too): his exit shuts it",
        "end",
        f"handlers[{EV_BANK}] = function()",
        "    if var(\"BankOpen\") == 0 then set(\"BankOpen\", 1); bankHatch(true) end",
        "    -- \"bank\" is a message to the banker: a dead banker takes none (MM9.receives); the hatch still opens",
        f"    if MM9.receives(\"frosgardcity\", \"Banker\", \"bank\", {a['Banker']}) then bankDialogue() end",
        "end",
        f"handlers[{rude_use_event(o['Banker'])}] = bankDialogue",
        "-- BankOrb.inc :OnRude: the hatch shuts; the orb placed (330 taken; with 333 the orb taken, 327); six banks'",
        "-- orbs (331-336): 337, 20 000 experience, 15 000 gold.",
        f"handlers[{rude_exit_event(o['Banker'])}] = function()",
        "    if var(\"BankOpen\") == 1 then set(\"BankOpen\", 0); bankHatch(false) end",
        "    if not has(330) then return end",
        "    MM9.takeKey(330)",
        "    if not has(333) then return end",
        "    quest(); MM9.takeItem(252, \"frosgardcity:Banker\"); MM9.giveKey(327)",
        "    if has(337) then return end",
        "    for k = 331, 336 do if not has(k) then return end end",
        f"    reward(337, {balanced_experience(20000, 337)}, 15000){experience_note(20000, 337)}",
        "end",
        "",
    ]
    script.add(lines, (EV_LOCKED, "Locked door", "Door"), (EV_BANK, "Bank", "Bank"),
               (rude_use_event(o["Banker"]), "Banker", None), (rude_exit_event(o["Banker"]), "Banker", None))

    # --- the harbour's ice ------------------------------------------------------------------------------------------
    def native(name):
        found = build.source.by_name.get(name.lower())
        return None if found is None else [int(round(v)) for v in build.project.native(found["properties"]["Pos"])]
    shooter = native("Shooter0")
    cannon = "nil" if shooter is None else "{" + ", ".join(map(str, shooter)) + "}"
    cannon_targets = ["{" + ", ".join(map(str, at)) + "}" for at in (native(f"Shoot{k}") for k in range(6))
                      if at is not None]
    lines = [
        "-- BreakIce.scr: the quest to free the frozen docks. Jarl Tryggva gives it (key 71); the powder seller (NPC215,",
        "-- key 1022) puts a powder barrel on the ice by the docks (DestructableProp0). MM9: the barrel's death starts the",
        "-- cannon (Shooter0, FrosgardShooter.scr), whose start runs BreakIce's cinema; here its click or its breaking",
        f"-- does, and the cinema is the cinematic {BREAK_ICE}: Shooter1-4 bolt the first floes, the rest break in MM9's",
        "-- waves (each floe drops under the ocean surface) and :GivePoints gives 72 and 8 000 experience (with 71), else",
        "-- 174 and 8 000: its steps (the block at the end of this file).",
        "local ICE_ALL = {" + ", ".join(f'"{n}"' for n in sorted(ice)) + "}",
        "local function iceGone() for _, n in ipairs(ICE_ALL) do open(n) end end",
        "local function floes(names) for _, n in ipairs(names) do if DOORS[n] then open(n) end end end",
        "local function iceReward()   -- BreakIce.scr :GivePoints",
        "    iceGone()",
        f"    if not has(72) and has(71) then MM9.giveKey(72); MM9.giveExperience({balanced_experience(8000, 72)})",
        f"    elseif not has(174) then MM9.giveKey(174); MM9.giveExperience({balanced_experience(8000, 174)}) end",
        "    quest()",
        "end",
        "-- FrosgardShooter.scr \"Shoot\" (Shooter0, under the ice): its Start (the barrel's death) fires FireBolts up at",
        "-- Shoot0-5, one picked at random every 0.4 s, eight in all (:Target, nCounter 8), as the floes break.",
        f"local CANNON = {cannon}",
        f"local CANNON_AT = {{{', '.join(cannon_targets)}}}",
        f"handlers[{T_CANNON}] = function()",
        "    local left = var(\"CannonShots\")",
        f"    if left <= 0 or CANNON == nil then evt.StopTimer({T_CANNON}); return end",
        "    local to = CANNON_AT[evt.RandomBetween(1, #CANNON_AT)]",
        "    evt.FireMissile(\"Fire\", CANNON[1], CANNON[2], CANNON[3], to[1], to[2], to[3], 0, \"Fire\", 0)",
        "    MM9.launchSound(\"FireBolt\", CANNON[1], CANNON[2], CANNON[3])",
        "    set(\"CannonShots\", left - 1)",
        f"    evt.StartTimer({T_CANNON}, seconds(0.4))",
        "end",
        f"handlers[{EV_BARREL}] = function()   -- DestructableProp0, the powder barrel",
        f"    if not has(1022) or var(\"BarrelGone\") == 1 then return end",
        f"    set(\"BarrelGone\", 1); cog({COGS['DestructableProp0']}, false)",
        "    MM9.playSound(\"sounds/events/iceimpact.wav\")",
        "    evt.StatusText(\"The powder barrel explodes!\")",
        f"    set(\"CannonShots\", 8); evt.StartTimer({T_CANNON}, seconds(0.1))",
        f"    MM9Cinematic.start(\"{BREAK_ICE}\")",
        "end",
        "",
        "-- NPC215.scr (the powder seller, RUDE 215): the delivery (key 1022) puts the barrel on the ice. (His night",
        "-- cannon test, Shooter6 from 22:00 to 04:00 with key 71, and Shooter5's test shot by DestructableProp1 are",
        "-- not carried: no quest hangs on them.)",
        f"handlers[{rude_exit_event(o['215'])}] = function()",
        f"    if has(1022) and var(\"BarrelGone\") == 0 and not has(72) then cog({COGS['DestructableProp0']}, true) end",
        "end",
        "",
        "-- NPC209.scr (the dockmaster, RUDE 209): with the docks free (72), the dock schedule (item 562), key 378.",
        f"handlers[{rude_exit_event(o['Dockmaster'])}] = function()",
        "    if not has(378) and has(72) then MM9.giveItem(562, \"frosgardcity:Dockmaster\"); MM9.giveKey(378) end",
        "end",
        "",
        f"handlers[{EV_WELL}] = function()   -- WellMMIX0: its class's use (dungeon/objects.py bonus_call)",
        f"    {bonus_call(build, 'WellMMIX0')}",
        "end",
        "",
    ]
    script.add(lines, (T_CANNON, "Cannon", None, "timer"), (EV_BARREL, "Powder barrel", "Barrel"), (rude_exit_event(o["215"]), "Powder seller", None),
               (rude_exit_event(o["Dockmaster"]), "Dockmaster", None), (EV_WELL, "Well", "Well"))

    # --- the townsfolk's quests -------------------------------------------------------------------------------------
    tryggva = "TryggvaRavenlocks0"
    lines = [
        "-- NPC180.scr (Jarl Tryggva Ravenlocks, RUDE 180; United.inc): the click checks the five clans (82, 38, 51, 63,",
        "-- 74 -> 178); the exit: Yanmir's Fort (70 -> 172, 58 000 experience, 10 000 gold), the ice (73 -> 175, 30 000,",
        "-- 3 000), the clans united (83 -> 179, 26 500, 6 000). Away during the battle (104) or on key 40, unless 108.",
        f"handlers[{rude_use_event(o[tryggva])}] = function()",
        "    if not has(178) and " + " and ".join(f"has({k})" for k in CLAN_KEYS) + " then MM9.giveKey(178) end",
        "    MM9.openRude(180)",
        "end",
        f"handlers[{rude_exit_event(o[tryggva])}] = function()",
        f"    if not has(172) and has(70) then reward(172, {balanced_experience(58000, 172)}, 10000) end"
        f"{experience_note(58000, 172)}",
        f"    if not has(175) and has(73) then reward(175, {balanced_experience(30000, 175)}, 3000) end"
        f"{experience_note(30000, 175)}",
        f"    if not has(179) and has(83) then reward(179, {balanced_experience(26500, 179)}, 6000) end"
        f"{experience_note(26500, 179)}",
        "end",
        "",
        "-- NPC181.scr (RUDE 181): the Ranger promotion (248 -> 249, 63 000 experience, 5 000 gold, every character",
        "-- holding key 417-420); the click with item 184 gives key 241.",
        f"handlers[{rude_use_event(o['181'])}] = function()",
        "    if MM9.hasItem(184, \"frosgardcity:181\") == 1 then MM9.giveKey(241) end",
        "    MM9.openRude(181)",
        "end",
        f"handlers[{rude_exit_event(o['181'])}] = function()",
        "    if not has(249) and has(248) then",
        f"        reward(249, {balanced_experience(63000, 249)}, 5000){experience_note(63000, 249)}",
        "        MM9.promoteParty(\"Ranger\")   -- every eligible member (not MM9's per-character keys 417-420)",
        "    end",
        "end",
        "-- NPC183.scr (RUDE 183): with key 295, item 245 unless the party has it.",
        f"handlers[{rude_exit_event(o['183'])}] = function()",
        "    if has(295) and MM9.hasItem(245, \"frosgardcity:183\") ~= 1 then MM9.giveItem(245, \"frosgardcity:183\") end",
        "end",
        "-- NPC184.scr (the brewmaster, RUDE 184): the keg (302 -> 303, item 249); delivered (307 -> 308, 20 000",
        "-- experience); the bad delivery (309 -> 310, 2 000 experience, 200 gold, the keg taken).",
        f"handlers[{rude_exit_event(o['184'])}] = function()",
        "    if not has(303) and has(302) then MM9.giveKey(303); MM9.giveItem(249, \"frosgardcity:184\") end",
        f"    if not has(308) and has(307) then reward(308, {balanced_experience(20000, 308)}, 0) end"
        f"{experience_note(20000, 308)}",
        f"    if not has(310) and has(309) then reward(310, {balanced_experience(2000, 310)}, 200); "
        "MM9.takeItem(249, \"frosgardcity:184\") end",
        "end",
        "-- NPC188.scr (RUDE 188): the ritual (257 -> 258, item 430, 5 000 experience).",
        f"handlers[{rude_exit_event(o['188'])}] = function()",
        f"    if not has(258) and has(257) then reward(258, {balanced_experience(5000, 258)}, 0); "
        "MM9.giveItem(430, \"frosgardcity:188\") end",
        "end",
        "-- PLEDGE.inc (:Pledge, :CheckAllNPC, :reward), on the dialogue exit of NPC190/191/193/195/196/197/199 and",
        "-- Pledge.scr (217, 218): with the pledge drive (265) and at most one of the pledges 269-274 missing (its loop",
        "-- reads 269-275 and stops on a second missing one only before 275; 276 is never read): key 277, 5 000",
        "-- experience, the quest sound, once.",
        "local function pledge()",
        "    if not has(265) or has(277) then return end",
        "    local missing = 0",
        "    for k = 269, 274 do if not has(k) then missing = missing + 1 end end",
        f"    if missing <= 1 then reward(277, {balanced_experience(5000, 277)}, 0) end"
        f"{experience_note(5000, 277)}",
        "end",
        "for _, index in ipairs({" + ", ".join(str(rude_exit_event(o[n])) for n in PLEDGE_OBJECTS if n in o)
        + "}) do handlers[index] = pledge end",
        "",
        "-- NPC190.scr (RUDE 190): the maypole (267: 500 gold -> 268, the new maypole stands; without the gold 267 is",
        "-- taken), then PLEDGE.inc's check.",
        "local function maypole()",
        f"    cog({COGS['Prop0']}, not has(268)); cog({COGS['Prop0Maypole']}, has(268))   -- ChangeModel.scr (Prop0)",
        "end",
        f"handlers[{rude_exit_event(o['190'])}] = function()",
        "    pledge()",
        "    if not has(268) and has(267) then",
        "        if MM9.hasGold(500) == 1 then MM9.takeGold(500); MM9.giveKey(268) else MM9.takeKey(267) end",
        "    end",
        "    maypole()",
        "end",
        "",
        "-- NPC309.scr (Tamur Leng, RUDE 309): hidden until the battle (BattleMan.scr); with key 106 his dialogue's",
        "-- close: 190, 412 000 experience; he joins the party (AddNPC 309: the MM9 hireling, story companion) and leaves",
        "-- the map; Thorolf appears (Thorolf2).",
        f"handlers[{rude_exit_event(o['TamurLeng0'])}] = function()",
        "    if has(190) or not has(106) then return end",
        f"    reward(190, {balanced_experience(412000, 190)}, 0){experience_note(412000, 190)}",
        "    MM9.addHireling(309)",
        f"    MM9.removeActor({a['TamurLeng0']})",
        f"    show({a['Thorolf2']}, true)",
        "end",
        "-- Forad.scr (Forad Darre, \"Hate\"): hidden until the battle; the first click 480 and 800 experience; his",
        "-- dialogue's close during the battle (104) turns him on the party; else 368 and 4 000 experience, gone on 29.",
        "-- The click (:OnUse) also turns him to the party (FaceObject, 200 degrees a second) and bows (PlayAnim bow).",
        f"handlers[{rude_use_event(o['ForadDarre'])}] = function()",
        f"    if not has(480) then reward(480, {balanced_experience(800, 480)}, 0) end",
        "    local x, y = evt.GetPartyPosition()",
        f"    evt.FaceActorTo({a['ForadDarre']}, x, y, 0.5); evt.PlayActorClip({a['ForadDarre']}, \"bow\", false)",
        f"    MM9.openRude({hooks.rude['ForadDarre']})",
        "end",
        f"handlers[{rude_exit_event(o['ForadDarre'])}] = function()",
        f"    if has(104) then   -- Hate: AddEnemy Player; MM9's monster AI walks him at the party (placed still)",
        "        set(\"ForadTalked\", 1)   -- bTalking stays set: he never opens his dialogue by himself again",
        f"        evt.ClearActorPresentation({a['ForadDarre']})   -- the bow's facing goes back to his AI",
        f"        evt.SetMonGroupBit({GROUP_FORAD}, MonsterBits.Hostile, true)",
        f"        evt.SetActorImmobile({a['ForadDarre']}, false)",
        "        return",
        "    end",
        f"    if not has(368) then reward(368, {balanced_experience(4000, 368)}, 0) end",
        f"    if has(29) then MM9.removeActor({a['ForadDarre']}) end",
        "end",
        "-- Forad.scr :OnAppear (BattleMan.scr's Appear: battle() below shows him): OnFoundPlayer OnTarget 256 ->",
        "-- target the player, OnTargetWithinDist 16 :Talk: he opens his dialogue himself when the party comes near (the",
        "-- approach talks' poll); with key 104 its close turns him on the party. :Talk and :OnUse set bTalking, which",
        "-- only :Forad (no 104) clears: after that close he never talks by himself again, on later visits too (ForadTalked).",
        "-- Forad.scr :OnDeath: once (key 494), 194 000 experience (capped) and the quest sound.",
        f"handlers[{EV_FORAD_DEATH}] = function(context)",
        f"    if context.actorIndex ~= {a['ForadDarre']} or has(494) then return end",
        f"    reward(494, {balanced_experience(194000, 494)}, 0){experience_note(194000, 494)}",
        "    MM9.playSound(\"sounds/events/quest.wav\")",
        "end",
        "",
        "-- NPC378.scr (Thorolf Ratatoskssen, three copies, RUDE 378): Thorolf0/1 here with 83 until 84; talking to one",
        "-- removes the other; Thorolf2 comes after Tamur Leng (106). 107 or 84: he vanishes; 106 or 83: the dialogue",
        "-- reopens.",
    ]
    for name, twin in (("Thorolf0", "Thorolf1"), ("Thorolf1", "Thorolf0"), ("Thorolf2", None)):
        remove_twin = f"MM9.removeActor({a[twin]}); " if twin else ""
        lines += [f"handlers[{rude_use_event(o[name])}] = function() {remove_twin}MM9.openRude(378) end",
                  f"handlers[{rude_exit_event(o[name])}] = function()",
                  # :Vanish: DoClientFX g_hmyObject, Ceffect ("spell-town portal")
                  f"    if has(107) or has(84) then MM9.clientFx({a[name]}, \"mm9:town_portal\"); "
                  f"MM9.removeActor({a[name]})"
                  + (f"; MM9.removeActor({a[twin]})" if twin else ""),
                  "    elseif has(106) or has(83) then MM9.openRude(378) end",
                  "end"]
    # Forad.scr :OnAppear -> :OnTarget -> OnTargetWithinDist 16 :Talk (stop, bTalking, DoRude 2; not :OnUse's key 480);
    # :OnTarget exits while bTalking, which a close with 104 leaves set (ForadTalked): once, not once per visit
    script.approach_talk(a["ForadDarre"], f"MM9.openRude({hooks.rude['ForadDarre']}, {a['ForadDarre']})",
                         armed="has(104) and var(\"ForadTalked\") == 0",
                         note="ForadDarre: FORAD.scr :OnAppear OnTargetWithinDist 16 :Talk")
    # NPC378.scr :OnFound: he runs to the party and talks (dungeon/lua.py thorolf_approaches)
    lua.thorolf_approaches(script, a, ("Thorolf0", "Thorolf1", "Thorolf2"))
    lines += [""]
    regs = [(rude_use_event(o[tryggva]), "Tryggva", None), (rude_exit_event(o[tryggva]), "Tryggva", None),
            (rude_use_event(o["181"]), "181", None), (rude_exit_event(o["181"]), "181", None),
            (rude_exit_event(o["183"]), "183", None), (rude_exit_event(o["184"]), "184", None),
            (rude_exit_event(o["188"]), "188", None), (rude_exit_event(o["190"]), "190", None),
            *[(rude_exit_event(o[n]), f"Pledge {n}", None) for n in PLEDGE_OBJECTS if n in o],
            (rude_exit_event(o["TamurLeng0"]), "Tamur Leng", None),
            (rude_use_event(o["ForadDarre"]), "Forad Darre", None), (rude_exit_event(o["ForadDarre"]), "Forad", None)]
    regs += [(f(o[n]), "Thorolf", None) for n in ("Thorolf0", "Thorolf1", "Thorolf2")
             for f in (rude_use_event, rude_exit_event)]
    script.add(lines, *regs)
    script.hooks.append(f'RegisterMonsterKilledHook({EV_FORAD_DEATH}, "Forad Darre killed", handlers[{EV_FORAD_DEATH}])')

    # --- the Battle of Frosgard -------------------------------------------------------------------------------------
    def at(name):
        return "{" + ", ".join(str(v) for v in points[name]) + "}" if name in points else None
    # HateNPC.scr AddEnemy NPC: every townsperson's row (the friendly placements of the town's group, not Forad's or
    # Tamur's, nor the Horde's or the clan soldiers' rows)
    town_rows = sorted({r["monster_id"] for r in build.content.report["actors"]
                        if r["friendly"] and r["group"] not in (GROUP_FORAD, GROUP_TAMUR)
                        and r["monster_id"] not in (*HORDE_ROWS, CLAN_ROW)})
    spawn = [
        "-- BattleMan.scr: the Battle of Frosgard. Entering with key 104 (once: 377): Forad Darre and Tamur Leng appear,",
        "-- the Horde attacks (HordeGrunt/Leader/Warrior: MM9 Horde A/B/C at Atlimarker, BadGuys0, 2, 3) and the clan",
        "-- soldiers come (ClanSoldier/Corporal/Sergeant: the town guard row 9107 at GoodGuys, set against the Horde).",
        "-- Trigger0 (Fight2, the touch line south of the square) adds a wave at BadGuys1 and soldiers at GoodGuys0.",
        "local function summon(row, p, group, hostile, count)",
        "    evt.SummonMonstersById({monster = row, x = p[1], y = p[2], z = p[3], radius = 96, count = count,",
        "        group = group, hostile = hostile, loot = false})",
        "end",
        "-- HateNPC.scr (the Horde's spawn script): AddEnemy NPC, ClanSoldier, KiratheCold: the Horde also goes for the",
        f"-- townsfolk (their rows: {', '.join(map(str, town_rows))}; one way, as AddEnemy: MM9's IsFriend asks both",
        "-- sides, and the townsfolk's NPCBase loop flees). Kira the Cold is not in Frosgard City.",
        "local function clansAgainstHorde()",
        f"    for _, h in ipairs({{{', '.join(map(str, HORDE_ROWS))}}}) do evt.SetMonsterRelation({CLAN_ROW}, h, 2); "
        f"evt.SetMonsterRelation(h, {CLAN_ROW}, 2) end",
        *([f"    for _, h in ipairs({{{', '.join(map(str, HORDE_ROWS))}}}) do for _, t in ipairs({{"
           f"{', '.join(map(str, town_rows))}}}) do evt.SetMonsterRelation(h, t, 2) end end"] if town_rows else []),
        "end",
        "local function battle()",
        "    MM9.giveKey(377)",
        f"    show({a['ForadDarre']}, true); show({a['TamurLeng0']}, true)",
        "    clansAgainstHorde()",
    ]
    for name, rows in (("Atlimarker", (9129, 9129, 9130, 9131)), ("BadGuys0", (9129, 9129, 9130)),
                       ("BadGuys2", (9129, 9129, 9130)), ("BadGuys3", (9131, 9131))):
        if at(name):
            for row in sorted(set(rows)):
                spawn.append(f"    summon({row}, {at(name)}, {GROUP_HORDE}, true, {rows.count(row)})   -- {name}")
    if at("GoodGuys"):
        spawn.append(f"    summon({CLAN_ROW}, {at('GoodGuys')}, {GROUP_CLAN}, false, 4)   -- GoodGuys")
    spawn += ["end",
              f"handlers[{EV_TRIGGER0}] = function()   -- Trigger0 (BattleMan :OnFight2)",
              "    if not has(104) or var(\"Fight2\") == 1 then return end",
              "    set(\"Fight2\", 1); clansAgainstHorde()"]
    if at("BadGuys1"):
        spawn += [f"    summon(9129, {at('BadGuys1')}, {GROUP_HORDE}, true, 2)",
                  f"    summon(9130, {at('BadGuys1')}, {GROUP_HORDE}, true, 1)",
                  f"    summon(9131, {at('BadGuys1')}, {GROUP_HORDE}, true, 1)"]
    if at("GoodGuys0"):
        spawn.append(f"    summon({CLAN_ROW}, {at('GoodGuys0')}, {GROUP_CLAN}, false, 3)")
    spawn += ["end", ""]
    script.add(spawn, (EV_TRIGGER0, "Trigger0", None))

    # --- scripted props ---------------------------------------------------------------------------------------------
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

    # --- map load and the poll --------------------------------------------------------------------------------------
    load = [
        f"    show({a[tryggva]}, has(108) or not (has(104) or has(40)))   -- NPC180.scr :Init",
        # Forad.scr "Hate" and NPC309.scr :Main hide them once, when the object is made (no OnPostSaveLoad: MM9 keeps their
        # flags over a save load), and BattleMan.scr's Appear shows them: once the battle has started (key 377) a load
        # leaves them as the save has them (README, Deviations: a load in the battle hid Tamur for good before 2026-11-08)
        f"    if not has(377) then show({a['ForadDarre']}, false); show({a['TamurLeng0']}, false) end   -- Forad.scr \"Hate\", NPC309.scr :Main",
        "    local thorolf = has(83) and not has(84)   -- NPC378.scr :Init",
        # Thorolf2 (NPC309's exit shows him with key 106) stays until his summons gives key 107: MM9's :Init hides him on
        # every load (OnPostSaveLoad), which left a party that saved before hearing him without key 107 (README, Deviations)
        f"    show({a['Thorolf0']}, thorolf); show({a['Thorolf1']}, thorolf); show({a['Thorolf2']}, has(106) and not has(107))",
        f"    show({a['238']}, not has(460))   -- Retainer.scr (238: key 460): hidden while hired",
        f"    cog({COGS['Prop1']}, has(278))   -- HideModel.scr \"278 UnHide\": the runestone",
        f"    cog({COGS['DestructableProp0']}, has(1022) and var(\"BarrelGone\") == 0 and not has(72))   -- NPC215.scr :Init",
        "    maypole()",
        "    if has(72) or has(174) then iceGone() end   -- BreakIce.scr :Init (TELP 1.3)",
        "    if has(104) and not has(377) then battle() end   -- BattleMan.scr :Init",
    ]
    load += altar_load
    lines = banter_lua(a["Douglas"]) + [
        "local function poll()",
        "    shopHours()",
        "    banter()",
        f"    evt.StartTimer({T_POLL}, seconds(1))",
        "end",
        f"handlers[{T_POLL}] = poll",
        f"handlers[{EV_LOAD}] = function()   -- map load",
        "    for k = 1024, 1033 do if k ~= 1029 and has(k) then MM9.takeKey(k) end end",
        "    MM9.giveKey(1029)",
        "    if var(\"BankOpen\") == 1 then set(\"BankOpen\", 0); bankHatch(false) end",
        *load,
        "    poll()",
        "end",
    ]
    script.add(lines, (T_POLL, "Poll", None, "timer"), (EV_LOAD, "Map load", None))
    return script.finish(on_load=[EV_LOAD]) + cutscenes.lua_block(scenes(hooks.actor)) + barrel_death_lua()


# --- the cutscenes --------------------------------------------------------------------------------------------------
def scenes(actors: dict) -> list:
    """The map's cutscenes (cutscenes.Scene) from the built actors (DAT name -> actor index: hooks.actor, or
    work/build_report.json's scripted actors): the converter's Lua and install and cinematics_pilot.py use these."""
    return [break_ice_scene(), bob_and_doug_scene(actors["Robert"], actors["Douglas"])]


def banter_lua(douglas: int) -> list[str]:
    """The poll's start of bob_and_doug: Douglas (his map actor) sees the party within his SightDistance."""
    sight = int(round(BANTER_SIGHT_LT * 2.56))
    return [
        "-- NPC214.scr :OnStart (Douglas's OnFoundPlayer, SightDistance 600 LT): without key 111 he and Robert (NPC213.scr)",
        f"-- argue, the cinematic {BOB_AND_DOUG} (no cameras); here on the poll once he sees the party within that range.",
        "local function banter()",
        f"    if not has(111) and evt.ActorSeesParty({douglas}, {sight}) then MM9Cinematic.start(\"{BOB_AND_DOUG}\") end",
        "end",
    ]


def _voice_seconds(name: str) -> float:
    """A cinema voice's length (mm9/extracted/VOICES/VOICES/CINEMA/<folder>/<file>.wav; cutscenes.wav_seconds only
    searches SOUNDS)."""
    import wave
    folder, file = name.split("\\")[-2:]
    path = cutscenes.ROOT / "mm9/extracted/VOICES/VOICES/CINEMA" / folder.upper() / file.upper().replace(".WAV", ".wav")
    with wave.open(str(path)) as stream:
        return stream.getnframes() / float(stream.getframerate())


def bob_and_doug_scene(robert: int, douglas: int) -> cutscenes.Scene:
    """NPC214.scr (Douglas) and NPC213.scr (Robert), from Douglas's :OnStart: each line a Loopanim and its wav, then a
    fixed wait (not the wav's length) before :OnStop (Loopanim stand) and the other's Speak<n>: Douglas 01 (2 s),
    Robert 02 (3), Douglas 03 (7.8), Robert 04 (3.8), Douglas 05 (6.5), Robert 06 (2), Douglas 07 (3), Robert 08 (4),
    Douglas 09 (3). No camera: an ambient cinematic (no shots, letterbox or input lock; the HUD stays). The lines
    have no text in MM9's data, so no subtitles. Key 111 (:OnStart givekey) is its step."""
    scene = cutscenes.Scene(BOB_AND_DOUG, EV_BOB_AND_DOUG, source="NPC214.scr :OnStart..:OnSpeak9, NPC213.scr",
                            ambient=True)
    cinema = scene.cinema
    scene.step(0.0, "key", "MM9.giveKey(111)", note=":OnStart givekey 111")
    # :OnStart: Douglas targets Robert and sends him Target (NPC213 :OnTarget: Robert targets Douglas)
    cinema._cue(0.0, "Douglas targets Robert", actor=douglas, action="face", look_at_actor=robert, seconds=0.3)
    cinema._cue(0.0, "Robert targets Douglas (:OnTarget)", actor=robert, action="face", look_at_actor=douglas,
                seconds=0.3)
    lines = [(douglas, "conv2", 2.0), (robert, "conv1", 3.0), (douglas, "conv2", 7.8), (robert, "conv1", 3.8),
             (douglas, "conv5", 6.5), (robert, "conv1", 2.0), (douglas, "conv4", 3.0), (robert, "conv1", 4.0),
             (douglas, "conv5", 3.0)]
    at = 0.0
    for number, (speaker, clip, wait) in enumerate(lines, 1):
        who = "Douglas" if speaker == douglas else "Robert"
        voice = f"voices\\cinema\\bobanddoug\\{number:02d}.wav"
        cinema._cue(at, f"{who}: Loopanim {clip}", actor=speaker, action="clip", clip=clip, loop=True)
        cinema.sound(at, voice, note=f"{who} {number:02d}.wav ({_voice_seconds(voice):.2f} s)")
        at += wait
        cinema._cue(at, f"{who}: :OnStop (Loopanim stand)", actor=speaker, action="clip", clip="stand", loop=True)
    return scene


# --- BreakIce.scr's cinema ------------------------------------------------------------------------------------------


def _bolt(frame, objects, shooter: str) -> str:
    """A Shooter's FireBolt straight down (its DAT pitch is 90 degrees) onto the ice under it, with its launch sound."""
    x, y, z = (int(round(v)) for v in frame.point(objects.named(shooter)["values"]["Pos"]))
    return (f'evt.FireMissile("Fire", {x}, {y}, {z}, {x}, {y}, {ICE_Z}, 0, "Fire", 0); '
            f'MM9.launchSound("FireBolt", {x}, {y}, {z})')


ICE_Z = -348                        # the floes' surface (LT y -136)
# Camera1's path (MM9: under the pier, 115 units over the ice) moved 400 units west, beside the pier: the rebuilt pier's
# T-head crosses it near IceMarker2 (the camera gate found it inside solid geometry there, and its 128-unit lift put
# the eye on the deck with the floes hidden: captures_break_ice/regate/). Same height and aim, the floes in frame.
CAMERA1_SHIFT = (-400.0, 0.0, 0.0)
BOLT_FALL = 0.4                     # a Shooter's bolt from its post (LT y 352) to the ice


def break_ice_scene() -> cutscenes.Scene:
    """BreakIce.scr from the barrel's death (Shooter0's Start: :OnStart waits 2 s) to :Done, seconds from the death:
    :Start 2 (fade out 1), :FadeIn 3 (Camera0, letterbox, fade in 1), :ShootOn 4 (Shooter1), :LetterboxOff 4.5 (waits
    1.5, 1.7, 1.8, 2.5: Shooter2-4 at 6, 6.2, 6.3, :UnderCam 7), :UnderCam 7 (Camera1 Move: IceCam1.scr MoveToPos
    IceMarker2 at 150 LT/s, its arrival sends Cam3; floes 15, 26, 25 at +0.7, 1.5, 2), :OnCam3 at the arrival (Camera2;
    :Group1-3 at +1.1, 1.11, 1.12; :OnDone +3: fade out 1, :GivePoints), :Done 1.5 s later (letterbox off, Camera2
    off, fade in 1). The shooters' floes (DamageOn, then their 500-damage bolt) drop BOLT_FALL after the shot;
    DestructableBrush16 only gets DamageOn there (no shooter over it) and breaks with :Group1."""
    project = Path(__file__).resolve().parent
    frame, objects = cutscenes.Frame(project), cutscenes.Objects.load("frosgardcity")
    scene = cutscenes.Scene(BREAK_ICE, EV_BREAK_ICE, source="BreakIce.scr :OnStart..:Done, IceCam1.scr")
    cinema = scene.cinema
    fov = cutscenes.MM9_CAMERA_FOV
    eye0, forward0 = frame.camera(objects, "Camera0")
    eye1, forward1 = frame.camera(objects, "Camera1")
    marker, _ = frame.camera(objects, "IceMarker2")
    eye1, marker = (tuple(v + d for v, d in zip(point, CAMERA1_SHIFT)) for point in (eye1, marker))
    eye2, forward2 = frame.camera(objects, "Camera2")
    under = 7.0
    _, arrival = cutscenes.move_to_pos(eye1, marker, frame.speed(150.0), 0.0)
    cam3 = under + arrival                          # 10.84 s
    on_done = cam3 + 3.0
    done = on_done + 1.5

    cinema.party(3.0, note="the barrel's death (the cannon fires), :OnStart wait 2, :Start fade out")
    cinema.fixed(under - 3.0, eye0, direction=forward0, fov=fov, note="Camera0 (:FadeIn .. :UnderCam)")
    cinema.moving(arrival, [(0.0, eye1, {"direction": forward1, "fov": fov}),
                            (arrival, marker, {"direction": forward1, "fov": fov})],
                  easing="linear", note="Camera1 Move (IceCam1.scr: MoveToPos IceMarker2 at 150, OnArrive Cam3), "
                  "400 west of MM9's (beside the pier)")
    cinema.fixed(done - cam3, eye2, direction=forward2, fov=fov, note="Camera2 (:OnCam3 .. :Done)")
    cinema.party(1.0, note=":Done: Camera2 off, the party's view fades in")
    cinema.fade(2.0, "out", 1.0, note=":Start ScreenFadeOut 1")
    cinema.letterbox_cue(3.0, True, 0.0, note=":FadeIn LetterBox TRUE")
    cinema.fade(3.0, "in", 1.0, note=":FadeIn ScreenFadeIn 1")
    cinema.fade(on_done, "out", 1.0, note=":OnDone ScreenFadeOut 1")
    cinema.letterbox_cue(done, False, 0.0, note=":Done LetterBox FALSE")
    cinema.fade(done, "in", 1.0, note=":Done ScreenFadeIn 1")

    def shot(at, shooter, floe, note):
        scene.step(at, shooter.lower(), _bolt(frame, objects, shooter), note=f"{note}: {shooter} on")
        scene.step(at + BOLT_FALL, f"floe{floe}", f'floes({{"DestructableBrush{floe}"}})',
                   note=f"{shooter}'s bolt breaks DestructableBrush{floe}")

    shot(4.0, "Shooter1", 27, ":ShootOn")
    shot(6.0, "Shooter2", 17, ":Shooter2")
    shot(6.2, "Shooter3", 18, ":Shooter3")
    shot(6.3, "Shooter4", 6, ":Shooter4")
    impact = "sounds\\events\\iceimpact.wav"
    for offset, floe, label in ((0.7, 15, "Destroy15"), (1.5, 26, "Destroy16"), (2.0, 25, "Destroy25")):
        scene.step(under + offset, f"floe{floe}", f'floes({{"DestructableBrush{floe}"}})', note=f":{label}")
        cinema.sound(under + offset, impact, note=f":{label}")
    groups = ([16, 14, 21, 24, 30, 33, 36, 39, 42, 45, 9], ICE_STAGES[3], ICE_STAGES[4])
    for number, (offset, group) in enumerate(zip((1.1, 1.11, 1.12), groups), 1):
        names = ", ".join(f'"DestructableBrush{k}"' for k in group)
        scene.step(cam3 + offset, f"group{number}", f"floes({{{names}}})", note=f":Group{number}")
        cinema.sound(cam3 + offset, impact, note=f":Group{number}")
    scene.step(on_done, "points", "iceReward()", note=":OnDone :GivePoints (72 or 174, 8 000 experience)")
    return scene


def barrel_death_lua() -> str:
    """DestructableProp0's DeathTriggerTarget (Shooter0 Start): the barrel broken by an attack starts the cannon and the
    cinematic as its click does, after the shared explosion (dungeon/objects.py, event 30000 + its index)."""
    from dungeon.objects import OBJECT_EVENT_BASE
    death = OBJECT_EVENT_BASE + cutscenes.Objects.load("frosgardcity").named("DestructableProp0")["index"]
    return "\n".join([
        "",
        "-- DestructableProp0's death (DeathTriggerTarget Shooter0 Start): broken, the barrel sets the ice off as its click",
        f"-- does (handler {EV_BARREL}), after its shared explosion.",
        "do",
        f"    local exploded = handlers[{death}]",
        f"    handlers[{death}] = function()",
        "        if exploded ~= nil then exploded() end",
        f"        handlers[{EV_BARREL}]()",
        "    end",
        f"    RegisterEvent({death}, \"DestructableProp0\", handlers[{death}])",
        "end",
        ""])
