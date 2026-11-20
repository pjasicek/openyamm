#!/usr/bin/env python3
"""
Lich Lab, MM9 rework: MM9's LICHLAB.dat as a native BLV on the shared dungeon converter (../mm9r_common/dungeon).

    python3 level_generation/projects/mm9r_lichlab/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_lichlab/convert.py --plan     # rooms and plans only (work/rooms*.png)

overrides.yml holds the model rules, archway cuts and seeds; this file adds the lab's population (props.json from
../../props/mm9_lichlab_claude, the cage fires, trigger pads, 147 monsters) and its scripted objects as native Lua
(README.md, "Scripted objects"): the Transmutation Engine and its pod (ILSHealerRoom.scr, Switch.scr), the elixir
(Givetake.scr, ElixirCook.scr, GiveElixir.scr), the letters (BookLetter.scr), the skeleton transformers (Converter.scr,
Switch objects), the shooting range (ILSshootingbook.scr), the summoner and its ghost pools (Summoner.scr,
SpawnMgr.scr, SpawnLoc.scr), the explosion lab's cages (KingKong.scr) and the hanging ickies (LL_FlyingCreature.scr).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.source import SCALE, floor_below  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"

# --- Events, timers, cogs, groups -------------------------------------------------------------------------------------
EV_LICHSWITCH = 200                 # the lich switch (Switch.scr "Engineglass1 toggle"): the pod
EV_ENGINE_LEVER = 201               # RotatingDoor1 at the engine (starts and stops its spin in MM9)
# The transformer switches' OpenTrigger2 / CloseTrigger1 AmbientSound (MM9: on while the transformer works)
PANEL_SOUND = {"TransformSwitch0": "panelon0", "TransformSwitch1": "panelon0", "TransformSwitch2": "panelon1",
               "TransformSwitch3": "panelon1"}
EV_TRANSFORM_SWITCH = {"TransformSwitch0": 202, "TransformSwitch1": 203, "TransformSwitch2": 204,
                       "TransformSwitch3": 205}
EV_BOOK = {"firebook2": 206, "firebook3": 207, "firebook4": 208}
EV_COOKPOT = 222                    # Prop18 (ElixirCook.scr)
EV_BURNER = 223                     # Prop17 (GiveElixir.scr)
EV_LETTER = {"Prop16": 224, "Prop19": 225, "Prop20": 226}      # BookLetter.scr
EV_TRIGGER_LICH = 230
EV_EXPLODE = {"TriggerExplodeL": 231, "TriggerExplodeR": 232}
EV_BATS = {"LobbyBatTrigger0": 233, "LobbyBatTrigger1": 234, "RightWingBatTrigger0": 235,
           "RightWingBatTrigger1": 236, "LeftWingBatTrigger0": 237, "LeftWingBatTrigger1": 238}
T_POD_STRIKE, T_POD_RAISE = 250, 251
# LichEngineProp.scr: the lever's travel (its OpenTrigger "start" / CloseTrigger "finish" when it gets there) and the
# end of the engine's startup or shutdown clip
T_ENGINE_LEVER, T_ENGINE_CLIP = 266, 267
ENGINE_CLIP_SECONDS = 3.5           # mm9_deco_lichengine.glb: startup and shutdown both last 3.5 s
T_TRANSFORM = {"SkeletonDoorA": (252, 253), "SkeletonDoorA0": (254, 255)}
T_BOOK = {"firebook2": 256, "firebook3": 257, "firebook4": 258}
# PeasantTransformee.scr (Converter.scr's conscript): per chamber its spawn and walk timers and its arrival event
T_PEASANT = {"SkeletonDoorA": (260, 261, 262), "SkeletonDoorA0": (263, 264, 265)}
PEASANT = 9050                      # Converter.scr p0 "CommonerHuman2MaleA": MM9 50 Commoner (mm9_peasantm2, its Cower)
DOOR_SECONDS = 4.3                  # the chamber door's travel (the door's OpenTrigger "create" when it is down)
COWER_SECONDS = 1.2                 # LoopAnim cower, 1: the Cower clip once (mm9_peasantm2.glb)
WALK_TIMEOUT = 20                   # OnStuck's retries stand-in: the strike comes anyway this long after the walk
KILL_HOOK = 95
DAMAGE_HOOK = 96                    # monster damage hook: SkeletonMaster1's DamageTriggerTarget
# DamageTriggerTarget/Message of placed monsters: a hit on the first sends the message to the second
DAMAGE_TRIGGERS = {"SkeletonMaster1": ("SkeletonMaster52", "Resurrect")}
COG_FIRE = 320
GROUP_ICKIES = {"Lobby": 60, "RightWing": 61, "LeftWing": 62}
GROUP_SUMMONER, GROUP_GHOSTS, GROUP_CAGED, GROUP_SKELETONS, GROUP_BURIED = 70, 71, 72, 73, 74
GROUP_PEASANTS = 75

SPECTER, SKELETON = 9140, 9135      # MM9 monster rows: SpawnLoc's "Specter", Converter's "Skeleton"
ITEM_HERBS, ITEM_JAR, ITEM_FLUID, ITEM_ELIXIR = 378, 358, 561, 246
KEY_INSTRUCTIONS, KEY_LICH = 296, 299
LICH_EXPERIENCE = 63000
GHOSTS_MAX_KILLS = 10               # SpawnMgr.scr: no spawn once ten are dead

# MM9's BOOK AND SCROLL TEXT.csv rows the letter scrolls show (BookLetter.scr DoLetter <item>).
LETTERS = {
    "Prop16": ("The Skeleton Transformer", "As I have told you all numerous times before, do not use the skeleton "
               "transformer to deposit your experimental waste!  On three occasions now, I've created skeletons who "
               "have extra arms growing out of where their eyesockets are, and one had a tentacle growing from its "
               "finger.  I am sure this is all amusing to the rest of you, but I will not tolerate it if I catch "
               "you!"),
    "Prop19": ("Scrap of Diary", "..I've secured the way to my domination!  I will create a giant army of skeletons.  "
               "The machine is here and in working order.  All I need is a constant supply of conscripts, and soon "
               "all will bow down to me!  I can nearly taste victory already.  The only one who might stand in my way "
               "is that lich who calls himself Pinky.  I am certain he has plans to conquer the world as "
               "well..dispatch him..everything would be easy."),
    "Prop20": ("Elixir Instructions", "If you're planning to make a new batch of Elixir of Defidation, follow these "
               "instructions.  If you don't, you could have unpredictable results.\nStep One:  Retrieve the Elixir "
               "Ingredients and a jar from the storeroom.  There should be plenty in Storeroom B next to the "
               "Observation Deck.\nStep Two:  Place the ingredients in the cookpot in the center of the kitchen.  "
               "From this you will get a few vials of Elixir Fluid.\nStep Three:  Take the Elixir Fluid to the "
               "burners, to refine it into the Elixir of Defidation.\nStep Four:  Drink the elixir when you are "
               "ready to be transformed.\n\nMaster-of-Liches"),
}
# The skeleton transformers: switches, chamber door, the shooters over the chamber, the chamber centre (LT).
TRANSFORMERS = {
    "SkeletonDoorA": {"switches": ["TransformSwitch0", "TransformSwitch1"], "transformer": "SkeletonTransformer",
                      "closet": "PeasantDoor",
                      "shooters": ["ShooterTransform0", "ShooterTransform1", "ShooterTransform2"]},
    "SkeletonDoorA0": {"switches": ["TransformSwitch2", "TransformSwitch3"], "transformer": "SkeletonTransformer0",
                       "closet": "PeasantDoor0",
                       "shooters": ["ShooterTransform3", "ShooterTransform4", "ShooterTransform5"]},
}
BOOKS = {"firebook2": ("shootfire1", "Target19"), "firebook3": ("fireball1", "Target16"),
         "firebook4": ("fireball2", "Target6")}
TARGET_SHOTS = 10                   # a straw target: 50 HP, the shooter's FireBolt 5 a shot
CAGES = ["CageGhast", "CageSpectre", "CageVenomous", "CageRevenant"]
# KingKong.scr critter -> its cage (ScriptParams p0: DB1, DB2, RotatingDoor167/168 and the glass their death destroys)
# and the fire that cage's DeathTriggerTarget lights; each critter breaks only its own cage.
KINGKONG = {"ExplodeGhast": ("CageGhast", "ExplodeSmoke3"), "ExplodeRevenant": ("CageRevenant", "ExplodeSmoke2"),
            "ExplodeDagrell0": ("CageSpectre", "ExplodeSmoke0"), "ExplodeDagrell1": ("CageVenomous", "ExplodeSmoke1")}
EXPLODE_FIRES = ["ExplodeSmoke0", "ExplodeSmoke1", "ExplodeSmoke2", "ExplodeSmoke3"]
GHOST_POOLS = ["GhostPool0", "GhostPool1", "GhostPool2", "GhostPool3"]


def lua_string(text: str) -> str:
    return json.dumps(text)


class LichLab(dungeon.Hooks):
    generator = "mm9r_lichlab"
    mover_events = {"EngineLever": (EV_ENGINE_LEVER, "click"),
                    **{name: (event, "click") for name, event in EV_TRANSFORM_SWITCH.items()}}

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        props = json.loads(PROPS.read_text())
        # the herb bags and jars (Givetake.scr) are world items (dungeon/pickups.py): picked up as any ground item
        self.pickups = [e["source_name"] for e in props if (e.get("script") or "").lower() == "givetake.scr"]
        events = dict(EV_BOOK)
        events.update(EV_LETTER)
        events.update({"lichswitch": EV_LICHSWITCH, "Prop18": EV_COOKPOT, "Prop17": EV_BURNER})
        content.props(PROPS, events=events)
        # The explosion lab's fires (MM9 Fire objects ExplodeSmoke0-3, off until a cage breaks): the Anskram gate
        # fire's flames without its light (mm9_gatefire_unlit: Light231-234 already light the cage fronts) on the
        # floor at each, hidden at load.
        for k, name in enumerate(EXPLODE_FIRES):
            p = source.properties(name)["Pos"]
            floor = content.floor_at(p[0], p[2], p[1] + 40)
            position = project.native([p[0], floor, p[2]])
            content.entity(name, "mm9_gatefire_unlit", position, 0, primary=COG_FIRE + k)
        # Touch triggers as pressure pads.
        for name, event in [("TriggerLich", EV_TRIGGER_LICH), *EV_EXPLODE.items(), *EV_BATS.items()]:
            p = source.properties(name)
            content.pad(name, p["Pos"], p["Dims"], event)
        self.positions = {}
        for name in GHOST_POOLS + EXPLODE_FIRES + [t["transformer"] for t in TRANSFORMERS.values()] + \
                [s for t in TRANSFORMERS.values() for s in t["shooters"]] + [b[0] for b in BOOKS.values()] + \
                ["Lightning0"]:
            self.positions[name] = project.native(source.properties(name)["Pos"]).round().astype(int).tolist()
        lightning = source.properties("Lightning0")
        self.positions["Lightning0_end"] = project.native(lightning["EndPos"]).round().astype(int).tolist()
        for pool in GHOST_POOLS:            # summon on the floor round the pool basin
            p = source.properties(pool)["Pos"]
            floor = content.floor_at(p[0], p[2], p[1])
            self.positions[pool][2] = int(round(floor * SCALE)) + 8
        for door in TRANSFORMERS.values():
            p = source.properties(door["transformer"])["Pos"]
            floor = content.floor_at(p[0], p[2], p[1] + 40)
            self.positions[door["transformer"]][2] = int(round(floor * SCALE)) + 8
            # Converter.scr p3: the marker in the closet where the conscript is spawned
            marker = str(source.properties(door["transformer"])["ScriptParams"]).split()[3]
            m = source.properties(marker)["Pos"]
            floor = content.floor_at(m[0], m[2], m[1] + 40)
            self.positions[door["transformer"] + "_spawn"] = project.native(
                [m[0], floor, m[2]]).round().astype(int).tolist()
        # PromoVol1: the pod's promotion volume (LT box) in native units.
        model = source.models["PromoVol1"]
        points = project.native(np.array(model.points, float))
        self.pod_box = [points.min(0).round().astype(int).tolist(), points.max(0).round().astype(int).tolist()]
        # The straw targets' centres (the books' bolts fly at them).
        for target in ("DestructableBrush6", "DestructableBrush16", "DestructableBrush19"):
            pts = project.native(np.array(source.models[target].points, float))
            self.positions["Target" + target[17:]] = ((pts.min(0) + pts.max(0)) / 2).round().astype(int).tolist()

    # --- actors ---------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out = []
        self.actor_index = {}               # DAT name -> placed actor index
        for o in source.objects:
            if o["class"] not in build.project.monster_classes or o["name"] not in bases:
                continue
            name, base, p = o["name"], bases[o["name"]], o["properties"]
            group, hidden, friendly, changes = 0, False, False, {}
            script = (p.get("ScriptName") or "").lower()
            if o["class"] == "FlyingIcky":
                # LL_FlyingCreature.scr: they hang under the ceiling until a bat trigger sends them off.
                group = GROUP_ICKIES[next(k for k in GROUP_ICKIES if name.startswith(k))]
                friendly = True
            elif name == "LichSummoner":
                group = GROUP_SUMMONER
            elif "kingkong" in script:
                group = GROUP_CAGED
            elif "autoresurrect" in script:
                # Buried under the floor until a resurrection that nothing in the lab sends: kept hidden.
                group, hidden = GROUP_BURIED, True
            elif name == "Oculus10":
                # MM9 places it inside the east lab's east wall (a sealed cavity no one sees or reaches): hidden.
                group, hidden = GROUP_BURIED, True
            record = content.actor(o, base, sector_of_room, group=group, hidden=hidden, friendly=friendly,
                                   floor_query_lt=p["Pos"][1] + 40 if group != GROUP_BURIED else 0,
                                   **changes)
            if o["class"] == "FlyingIcky":
                record["position"]["z"] = int(round(p["Pos"][1] * SCALE)) - 120
            record.update(placed_body(record["monster_id"], p))   # MM9's body at the DAT's own Scale (replaces the row's)
            self.actor_index[name] = record["actor_index"]
            out.append(record)
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Lich Lab")
        pos = self.positions
        groups = {g: ids for g, ids in script.groups.items()}
        script.lines += [
            "local GROUPS = {" + ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(groups.items()))
            + "}",
            "local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) "
            "end end",
            "local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, "
            "DoorAction.Close) end end",
            "-- One-shot timers: the map's timers run from load (RegisterMapTimerEvent repeats), so each is armed by a",
            "-- named variable when started and acts only when armed.",
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "local function inside(box, x, y, z) return x >= box[1][1] and x <= box[2][1] and y >= box[1][2] "
            "and y <= box[2][2] and z >= box[1][3] - 40 and z <= box[2][3] end",
            "",
        ]
        script.doors()
        script.chests()
        lines = []
        # The switch's and the engine's clip keys: their entity indices (no SetSprite key of their own; a cog would be
        # an event_id_primary written into the .blv)
        switch_key, engine_key = self.entity_index(build, "lichswitch"), self.entity_index(build, "Lichengine")
        lever = build.source.properties("RotatingDoor1")
        lever_seconds = round(abs(lever["RotationAngles"][0]) / float(lever["Speed"]), 2)
        # The Transmutation Engine. Glow1 (GlowingLight, StartOn 0): the pod's scene pulsing light (dungeon/lights.py).
        from dungeon.lights import PULSING_LIGHT_KEY_BASE
        glow = PULSING_LIGHT_KEY_BASE + build.source.by_name["glow1"]["index"]
        lines += [
            "-- The Transmutation Engine (ILSHealerRoom.scr on PromoTrigger, Switch.scr on lichswitch, LichEngineProp.scr).",
            "-- The lich switch lowers pod 1's lid and glass (MM9 Doors Enginedoor1/Engineglass1: down 96) round",
            "-- whoever stands in it; 3 s later the engine strikes (lightning down the shaft onto it) and, with the",
            "-- party inside PromoVol1, transmutes: MM9 runs this only once the engine is 'fixed', which nothing in",
            "-- MM9 does; here the Lich Instructions (key 296) are what make it work. Each member who carries an",
            "-- Elixir of Defedation (MM9: 'subjects must drink from their own vial'; here any pack's vial, its own first:",
            "-- the burner puts the elixir in the active member's pack) and is a Wizard (MM9's",
            "-- Scholar) becomes a Lich; the first working strike gives MM9's 63000 experience and key 299 (journal",
            "-- 'Become a Lich' done) whoever it changes (every promotion quest pays its rewards to any party, the user",
            "-- 2026-11-08); the engine works again at any time for those ready later. 2 s after the strike the pod rises.",
            f"local POD_BOX = {{{lua.point(self.pod_box[0])}, {lua.point(self.pod_box[1])}}}",
            "local LICH_CLASSES = {Wizard = true, Necromancer = true}  -- one step from Lich (MM7 dark path, MM8)",
            "local function transmute()",
            "    local x, y, z = evt.GetPartyPosition()",
            "    if not inside(POD_BOX, x, y, z) then return 0 end",
            f"    if MM9.hasKey({KEY_INSTRUCTIONS}) == 0 then",
            "        evt.StatusText(\"The engine shudders, but nothing happens.\")",
            "        return 0",
            "    end",
            f"    local elixir = MM9.ItemIds[{ITEM_ELIXIR}]",
            "    local count = evt.GetPartyMemberCount()",
            "    local function takeElixir(i)   -- the subject's own vial, else one from another pack",
            "        for _, j in ipairs({i, 0, 1, 2, 3, 4}) do",
            "            if j < count and evt.PartyMemberHasItem(j, elixir) then",
            "                evt.RemovePartyMemberItem(j, elixir)",
            "                return true",
            "            end",
            "        end",
            "        return false",
            "    end",
            "    local changed, ready = 0, 0",
            "    for i = 0, count - 1 do",
            "        if LICH_CLASSES[evt.GetPlayerClassName(i)] then",
            "            ready = ready + 1",
            "            if elixir ~= nil and takeElixir(i) and evt.ApplyLichTransformation(i) then changed = changed + 1 end",
            "        end",
            "    end",
            f"    if MM9.hasKey({KEY_LICH}) == 0 then",
            f"        {experience_lua(LICH_EXPERIENCE, KEY_LICH, 'ilshealerroom.scr', 'OnPromo')}",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            f"        MM9.giveKey({KEY_LICH})",
            "    end",
            "    if changed == 0 then",
            "        evt.StatusText(ready > 0 and \"The engine roars, but there is no Elixir of Defedation to drink.\"",
            "            or \"The engine roars, but no one is ready for the change.\")",
            "        return 0",
            "    end",
            "    set(\"Transmuted\", var(\"Transmuted\") + changed)",
            "    return changed",
            "end",
            "-- Switch.scr Onuse: each use plays the lever's Down, the next its Up (bUp), and triggers Engineglass1.",
            f"handlers[{EV_LICHSWITCH}] = function()   -- lichswitch",
            "    local down = var(\"LichSwitchDown\") == 0",
            "    set(\"LichSwitchDown\", down and 1 or 0)",
            f"    evt.PlayDecorationClip({switch_key}, down and \"down\" or \"up\")",
            "    if var(\"PodClosed\") == 1 then return end",
            "    set(\"PodClosed\", 1)",
            "    openGroup(\"EnginePod1\")",
            f"    evt.SetLight({glow}, true)   -- Engineglass1's OpenTrigger: Glow1 on (the pod glows while shut)",
            f"    arm({T_POD_STRIKE}, 3)",
            "end",
            f"handlers[{T_POD_STRIKE}] = function()   -- the engine strikes",
            f"    if not fired({T_POD_STRIKE}) or var(\"PodClosed\") ~= 1 then return end",
            f"    evt.Beam(\"EngineLightning\", \"openyamm:fx/arc_beam\", {', '.join(map(str, pos['Lightning0']))}, "
            f"{', '.join(map(str, pos['Lightning0_end']))}, 1.5)",
            "    evt.PlaySoundName(\"sounds/magic/projectile14.wav\", 0, 0, 0)",
            "    set(\"EngineStrikes\", var(\"EngineStrikes\") + 1)",
            "    transmute()",
            f"    arm({T_POD_RAISE}, 2)",
            "end",
            f"handlers[{T_POD_RAISE}] = function()   -- the pod rises",
            f"    if not fired({T_POD_RAISE}) or var(\"PodClosed\") ~= 1 then return end",
            "    closeGroup(\"EnginePod1\")",
            f"    evt.SetLight({glow}, false)   -- Engineglass1's CloseTrigger: Glow1 off",
            "    set(\"PodClosed\", 0)",
            "end",
            "",
            "-- The Lich engine (LichEngineProp.scr on Lichengine): RotatingDoor1, the lever before it, sends it",
            f"-- \"start\" once open and \"finish\" once shut again ({lever_seconds:g} s of travel). \"start\" at rest plays",
            "-- startup, then loops spincycle; \"finish\" while it spins plays shutdown, then it stands at rest",
            "-- (LoopAnim static_model).",
            "-- Each message is heard only in its own state (the script removes the other's trigger): EngineSpin 0 rest,",
            "-- 1 starting, 2 spinning, 3 stopping. EngineLeverOpen is where the lever was last sent (a click while it",
            "-- swings turns it back).",
            f"handlers[{EV_ENGINE_LEVER}] = function()   -- RotatingDoor1",
            "    local open = var(\"EngineLeverOpen\") == 0",
            "    set(\"EngineLeverOpen\", open and 1 or 0)",
            "    for _, id in ipairs(GROUPS.EngineLever) do evt.SetDoorState(id, open and DoorAction.Open or DoorAction.Close) end",
            f"    arm({T_ENGINE_LEVER}, {lever_seconds:g})",
            "end",
            f"handlers[{T_ENGINE_LEVER}] = function()   -- the lever is there: OpenTrigger start / CloseTrigger finish",
            f"    if not fired({T_ENGINE_LEVER}) then return end",
            "    local spin = var(\"EngineSpin\")",
            "    if var(\"EngineLeverOpen\") == 1 and spin == 0 then",
            "        set(\"EngineSpin\", 1)",
            f"        evt.PlayDecorationClip({engine_key}, \"startup\")   -- PowerUp: PlayAnim startup, Spin",
            f"        arm({T_ENGINE_CLIP}, {ENGINE_CLIP_SECONDS:g})",
            "    elseif var(\"EngineLeverOpen\") == 0 and spin == 2 then",
            "        set(\"EngineSpin\", 3)",
            f"        evt.PlayDecorationClip({engine_key}, \"shutdown\")   -- PowerDown: PlayAnim shutdown, Stop",
            f"        arm({T_ENGINE_CLIP}, {ENGINE_CLIP_SECONDS:g})",
            "    end",
            "end",
            f"handlers[{T_ENGINE_CLIP}] = function()   -- startup or shutdown played out",
            f"    if not fired({T_ENGINE_CLIP}) then return end",
            "    if var(\"EngineSpin\") == 1 then",
            "        set(\"EngineSpin\", 2)",
            f"        evt.PlayDecorationClip({engine_key}, \"spincycle\", \"loop\")   -- Spin: LoopAnim spincycle",
            "    elseif var(\"EngineSpin\") == 3 then",
            "        set(\"EngineSpin\", 0)",
            f"        evt.PlayDecorationClip({engine_key}, \"\")   -- Stop: LoopAnim static_model",
            "    end",
            "end",
            "",
        ]
        script.add([], (EV_LICHSWITCH, "Lich switch", "Switch"), (T_POD_STRIKE, "Engine strike", None, "timer"),
                   (T_POD_RAISE, "Pod rises", None, "timer"), (EV_ENGINE_LEVER, "Lever", "Lever"),
                   (T_ENGINE_LEVER, "Engine lever", None, "timer"), (T_ENGINE_CLIP, "Engine clip", None, "timer"))
        # The elixir.
        lines += [
            "-- The elixir (Givetake.scr, ElixirCook.scr, GiveElixir.scr): the storeroom's herb bags (Elixir Ingredients,",
            "-- 378) and jars (a Jar, 358) are world items; the kitchen's cook pot turns ingredients into Elixir Fluid",
            "-- (561); the burner by the kitchen turns fluid and a jar into the Elixir of Defedation (246).",
            "-- MM9's giveitem puts the item in the party's packs: the active member's first, then the others' (the",
            "-- cursor only when every pack is full).",
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
        ]
        lines += [
            f"handlers[{EV_COOKPOT}] = function()   -- Prop18, the cook pot",
            f"    if MM9.hasItem({ITEM_HERBS}, \"lichlab:Prop18\") == 1 then",
            f"        MM9.takeItem({ITEM_HERBS}, \"lichlab:Prop18\")",
            f"        give({ITEM_FLUID}, \"lichlab:Prop18\")",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            "    end",
            "end",
            f"handlers[{EV_BURNER}] = function()   -- Prop17, the burner",
            f"    if MM9.hasItem({ITEM_JAR}, \"lichlab:Prop17\") == 1 and MM9.hasItem({ITEM_FLUID}, \"lichlab:Prop17\") == 1 then",
            f"        MM9.takeItem({ITEM_JAR}, \"lichlab:Prop17\")",
            f"        MM9.takeItem({ITEM_FLUID}, \"lichlab:Prop17\")",
            f"        give({ITEM_ELIXIR}, \"lichlab:Prop17\")",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            "    end",
            "end",
            "",
            "-- The letters (BookLetter.scr DoLetter): MM9's book and scroll texts.",
        ]
        script.add([], (EV_COOKPOT, "Cook pot", "Cook pot"), (EV_BURNER, "Burner", "Burner"))
        for name, event in EV_LETTER.items():
            title, text = LETTERS[name]
            lines.append(f"handlers[{event}] = function() evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end"
                         f"   -- {name}")
            script.add([], (event, "Scroll", "Scroll"))
        # The skeleton transformers.
        transformers_at = len(lines) + 1
        lines += [
            "",
            "-- The skeleton transformers (Converter.scr): a switch locks both switches and lowers the chamber's glass",
            "-- door (4.3 s at MM9's speed); the door's OpenTrigger \"create\" spawns the conscript (a Commoner) at the",
            "-- closet's marker, and 2 s later PeasantTransformee.scr walks him to the chamber's centre, where he cowers",
            "-- (the Cower clip once, wizardeyeloop.wav) and winces: \"convert\", the shooters over the chamber strike and",
            "-- a Skeleton stands where he stood; 1 s later the door rises and the switches unlock. (Converter.scr's",
            "-- TransformCreature removes him only `if (hDummy != 0)`, a name it never sets, and spawns the Skeleton at",
            "-- the marker: the evident intent, the peasant turned where he stands, is carried.)",
        ]
        for door, info in TRANSFORMERS.items():
            strike, release = T_TRANSFORM[door]
            centre = pos[info["transformer"]]
            switches = info["switches"]
            beams = "\n".join(
                f"    evt.Beam(\"{s}\", \"openyamm:fx/arc_beam\", {', '.join(map(str, pos[s]))}, {centre[0]}, {centre[1]}, "
                f"{centre[2] + 60}, 1.2)" for s in info["shooters"])
            for switch in switches:
                lines.append(f"handlers[{EV_TRANSFORM_SWITCH[switch]}] = function() transform(\"{door}\") end   -- {switch}")
                script.add([], (EV_TRANSFORM_SWITCH[switch], "Switch", "Switch"))
            spawn_t, walk_t, arrive = T_PEASANT[door]
            marker = pos[info["transformer"] + "_spawn"]
            lines += [
                f"handlers[{spawn_t}] = function()   -- {door}: the door is down, OpenTrigger create (SpawnCreature)",
                f"    if not fired({spawn_t}) or var(\"{door}\") ~= 1 then return end",
                f"    local _, made = evt.SummonMonstersById({{monster = {PEASANT}, x = {marker[0]}, y = {marker[1]}, "
                f"z = {marker[2]}, radius = 0, group = {GROUP_PEASANTS}, hostile = false, loot = false, count = 1, "
                "mm9 = {wander = \"aimless\", wander_wait = {30, 30}}})   -- a wanderer thinks out of the party's room "
                "(MM9 wakes the actors near the player), so the walk below runs; the wait keeps him still till then",
                f"    set(\"{door}Peasant\", made ~= nil and made[1] ~= nil and made[1] + 1 or 0)",
                f"    openGroup(\"{info['closet']}\")   -- the closet's door (AITriggerable: MM9's conscript opens it)",
                f"    arm({walk_t}, 2)",
                "end",
                f"handlers[{walk_t}] = function()   -- {door}: SignalCreature walk (WalkToSpawner)",
                f"    if not fired({walk_t}) or var(\"{door}\") ~= 1 then return end",
                f"    local i = var(\"{door}Peasant\") - 1",
                f"    if i < 0 or not evt.MoveActorTo(i, {centre[0]}, {centre[1]}, {centre[2]}, {arrive}) then "
                f"arm({strike}, 0.1) return end",
                f"    arm({strike}, {WALK_TIMEOUT})",
                "end",
                f"handlers[{arrive}] = function()   -- {door}: at the chamber's centre (PlayMagicSound)",
                f"    if var(\"{door}\") ~= 1 then return end",
                f"    local i = var(\"{door}Peasant\") - 1",
                "    if i >= 0 then evt.PlayActorClip(i, \"cower\") end",
                f"    closeGroup(\"{info['closet']}\")   -- its CloseWaitTime",
                f"    set(\"{door}Cowered\", var(\"{door}Cowered\") + 1)",
                "    evt.PlaySoundName(\"sounds/magic/wizardeyeloop.wav\", 0, 0, 0)",
                f"    arm({strike}, {COWER_SECONDS})",
                "end",
                f"handlers[{strike}] = function()   -- {door}: the strike (TriggerSpawner convert, TransformCreature)",
                f"    if not fired({strike}) or var(\"{door}\") ~= 1 then return end",
                f"    local x, y, z = {centre[0]}, {centre[1]}, {centre[2]}",
                f"    local peasant = var(\"{door}Peasant\") - 1",
                "    -- \"convert\" comes from the conscript himself (TriggerSpawner): a dead one sends none, and the chamber",
                "    -- stays down with its switches locked (MM9.actorAlive; the walk timeout stands in for a live one's OnStuck)",
                "    if peasant >= 0 and not MM9.actorAlive(peasant) then return end",
                "    if peasant >= 0 then",
                "        local px, py, pz = evt.GetMapActorPosition(peasant)",
                "        if px ~= nil then x, y, z = px, py, pz end",
                "        evt.StopActorMove(peasant); evt.ClearActorPresentation(peasant)",
                "        evt.SetMonsterBit(peasant, ActorAttribute.Invisible, 1)   -- RemoveObject",
                f"        set(\"{door}Peasant\", 0)",
                "    end",
                "    evt.PlaySoundName(\"sounds/animsounds/pig/wince1.wav\", 0, 0, 0)",
                beams,
                "    evt.PlaySoundName(\"sounds/magic/projectile14.wav\", 0, 0, 0)",
                f"    local made = evt.SummonMonstersById({{monster = {SKELETON}, x = x, y = y, "
                f"z = z, radius = 16, group = {GROUP_SKELETONS}, count = 1}})",
                "    set(\"SkeletonsMade\", var(\"SkeletonsMade\") + made)",
                f"    set(\"{door}\", 2)",
                f"    arm({release}, 1)",
                "end",
                f"handlers[{release}] = function()   -- {door}: the release",
                f"    if not fired({release}) or var(\"{door}\") ~= 2 then return end",
                f"    openGroup(\"{door}\")",
                *[f"    evt.SetDoorState(DOORS.{s}, DoorAction.Close)" for s in switches],
                f"    set(\"{door}\", 0)",
                f"    set(\"AmbientSound\" .. TRANSFORMERS.{door}.panel, 2)   -- the switches' CloseTrigger1: PanelOn off",
                "end",
            ]
            script.add([], (strike, f"{door} strike", None, "timer"), (release, f"{door} release", None, "timer"),
                       (spawn_t, f"{door} conscript", None, "timer"), (walk_t, f"{door} conscript walks", None, "timer"),
                       (arrive, f"{door} conscript arrives", None))
        transformer_table = ", ".join(
            f"{door} = {{switches = {{{', '.join(chr(34) + s + chr(34) for s in info['switches'])}}}, strike = {T_TRANSFORM[door][0]}, "
            f"spawn = {T_PEASANT[door][0]}, "
            f"panel = {build.source.by_name[PANEL_SOUND[info['switches'][0]]]['index']}}}"
            for door, info in TRANSFORMERS.items())
        prelude = [
            f"local TRANSFORMERS = {{{transformer_table}}}",
            "local function transform(door)",
            "    if var(door) ~= 0 then evt.StatusText(\"The switch is locked.\") return end",
            "    set(door, 1)",
            "    for _, s in ipairs(TRANSFORMERS[door].switches) do evt.SetDoorState(DOORS[s], DoorAction.Open) end",
            "    closeGroup(door)",
            "    set(\"AmbientSound\" .. TRANSFORMERS[door].panel, 1)   -- the switches' OpenTrigger2: PanelOn on",
            f"    arm(TRANSFORMERS[door].spawn, {DOOR_SECONDS})",
            "end",
        ]
        lines[transformers_at:transformers_at] = prelude
        # The shooting range.
        lines += [
            "",
            "-- The shooting range (ILSshootingbook.scr): a book's first use plays its OpenBook and starts its shooter,",
            "-- which fires a bolt at the straw target in front of it every 1.5 s; ten bolts (50 HP, FireBolt 5) break",
            "-- the target (it sinks into the floor), whose DeathTrigger sends the book Done. A use before that stops and",
            "-- restarts the shooter (MM9's Off/On); the first use after it plays CloseBook and stops it for good.",
            "-- Book var: 0 shut, 1 open and shooting, 2 done (target broken), 3 closed for good.",
        ]
        for book, (shooter, target) in BOOKS.items():
            timer = T_BOOK[book]
            key = self.entity_index(build, book)
            sx, sy, sz = pos[shooter]
            tx, ty, tz = pos[target]
            lines += [
                f"handlers[{EV_BOOK[book]}] = function()   -- {book} -> {shooter} -> {target}",
                f"    local state = var(\"{book}\")",
                "    if state == 3 then return end   -- Stopped",
                "    if state == 2 then",
                f"        evt.PlayDecorationClip({key}, \"closebook\")   -- Done: PlayAnim CloseBook, Stopped",
                f"        set(\"{book}\", 3)",
                "        return",
                "    end",
                f"    if state == 0 then evt.PlayDecorationClip({key}, \"openbook\") end   -- PlayAnim OpenBook",
                f"    set(\"{book}\", 1)",
                f"    evt.StartTimer({timer}, seconds(1.5))",
                "end",
                f"handlers[{timer}] = function()",
                f"    if var(\"{book}\") ~= 1 then evt.StopTimer({timer}) return end",
                f"    evt.FireMissile(\"Fire\", {sx - 30}, {sy}, {sz}, {tx}, {ty}, {tz}, 0, \"Fire\", 0)",
                f"    MM9.launchSound(\"FireBolt\", {sx}, {sy}, {sz})",
                f"    set(\"{target}Hits\", var(\"{target}Hits\") + 1)",
                f"    if var(\"{target}Hits\") >= {TARGET_SHOTS} then",
                f"        evt.StopTimer({timer})",
                f"        set(\"{book}\", 2)",
                f"        openGroup(\"{target}\")",
                "    else",
                f"        evt.StartTimer({timer}, seconds(1.5))",
                "    end",
                "end",
            ]
            script.add([], (EV_BOOK[book], "Book", "Book"), (timer, f"{shooter}", None, "timer"))
        # The summoner.
        pools = ", ".join(lua.point(pos[p]) for p in GHOST_POOLS)
        lines += [
            "",
            "-- The summoner (Summoner.scr on LichSummoner, SpawnMgr.scr, SpawnLoc.scr on GhostPool0-3): the touch trigger",
            "-- at the stair foot wakes it; a Specter rises from each ghost pool, and each time one dies another rises",
            f"-- from a random pool, while the summoner lives and until {GHOSTS_MAX_KILLS} are dead.",
            f"local POOLS = {{{pools}}}",
            "local function raiseGhost(k)",
            "    local p = POOLS[k]",
            f"    local made = evt.SummonMonstersById({{monster = {SPECTER}, x = p[1], y = p[2], z = p[3], radius = 32, "
            f"group = {GROUP_GHOSTS}, count = 1}})",
            "    set(\"GhostsRaised\", var(\"GhostsRaised\") + made)",
            "end",
            f"handlers[{EV_TRIGGER_LICH}] = function()   -- TriggerLich -> LichSummoner startup",
            "    if var(\"Summoner\") ~= 0 then return end",
            f"    if evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_SUMMONER}, 0, false) then return end",
            "    set(\"Summoner\", 1)",
            "    for k = 1, 4 do raiseGhost(k) end",
            "end",
        ]
        script.add([], (EV_TRIGGER_LICH, "TriggerLich", None))
        # Cages.
        kingkong = ", ".join(f"{{\"{critter}\", {self.actor_index[critter]}, \"{cage}\", "
                             f"{COG_FIRE + EXPLODE_FIRES.index(fire)}}}"
                             for critter, (cage, fire) in KINGKONG.items() if critter in self.actor_index)
        lines += [
            "",
            "-- The explosion lab (KingKong.scr on ExplodeGhast, ExplodeRevenant, ExplodeDagrell0/1): either touch",
            "-- trigger (they switch each other off: ForceBreak goes out once) makes each critter smash its own cage",
            "-- front (it sinks away) with a swing (BreakCage: PlayAnim hattack1, the attack_melee clip) and the fire",
            "-- behind that broken glass flares up (ExplodeSmoke0-3). A dead critter takes no ForceBreak (MM9.receives):",
            "-- its cage stays standing and its fire unlit. None has an ANIM_NAME (p1): nothing loops while caged.",
            f"local KINGKONG = {{{kingkong}}}   -- critter, its actor, its cage, its fire",
            "local function bustCages()",
            "    if var(\"CagesBroken\") == 1 then return end",
            "    set(\"CagesBroken\", 1)",
            "    for _, k in ipairs(KINGKONG) do",
            "        if MM9.receives(\"lichlab\", k[1], \"ForceBreak\", k[2]) then",
            "            set(\"Broken\" .. k[3], 1)",
            "            openGroup(k[3])",
            "            evt.PlayActorClip(k[2], \"attack_melee\")",
            "            evt.SetSprite(k[4], true)",
            "        end",
            "    end",
            "end",
        ]
        for name, event in EV_EXPLODE.items():
            lines.append(f"handlers[{event}] = function() bustCages() end   -- {name}")
            script.add([], (event, name, None))
        # Bats.
        lines += [
            "",
            "-- The hanging ickies (LL_FlyingCreature.scr): each wing's touch triggers send its eight ickies off; here",
            "-- they hang peaceful until then and turn hostile.",
        ]
        for name, event in EV_BATS.items():
            wing = next(k for k in GROUP_ICKIES if name.startswith(k))
            group = GROUP_ICKIES[wing]
            lines.append(f"handlers[{event}] = function() if var(\"Bats{wing}\") == 0 then set(\"Bats{wing}\", 1); "
                         f"evt.SetMonGroupBit({group}, MonsterBits.Hostile, true) end end   -- {name}")
            script.add([], (event, name, None))
        # Kill hook and load. evt.CheckMonstersKilled(group, count) says whether at least `count` of the group are
        # dead: the hook counts its ghosts' deaths up and raises one ghost for each new death.
        lines += [
            "",
            f"handlers[{KILL_HOOK}] = function()   -- any monster killed: the summoner's ghosts",
            "    if var(\"Summoner\") ~= 1 then return end",
            f"    if evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_SUMMONER}, 0, false) then set(\"Summoner\", 2) return end",
            "    local killed = var(\"GhostKills\")",
            f"    while killed < {GHOSTS_MAX_KILLS} and evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_GHOSTS}, killed + 1, false) do",
            "        killed = killed + 1",
            "        set(\"GhostKills\", killed)",
            f"        if killed < {GHOSTS_MAX_KILLS} then raiseGhost(evt.RandomBetween(1, 4, 1)) end",
            "    end",
            "end",
        ]
        lines += [
            "handlers[1] = function()   -- map load: the cage fires burn only once broken; the switch and the engine as left",
            "    for _, k in ipairs(KINGKONG) do if var(\"Broken\" .. k[3]) == 0 then evt.SetSprite(k[4], false) end end",
            f"    if var(\"LichSwitchDown\") == 1 then evt.PlayDecorationClip({switch_key}, \"down\", \"end\") end",
            f"    for _, b in ipairs({{{', '.join(f'{{{chr(34)}{b}{chr(34)}, {self.entity_index(build, b)}}}' for b in BOOKS)}}}) do",
            "        local state = var(b[1])",
            "        if state == 1 or state == 2 then evt.PlayDecorationClip(b[2], \"openbook\", \"end\")",
            "        elseif state == 3 then evt.PlayDecorationClip(b[2], \"closebook\", \"end\") end",
            "    end",
            f"    if var(\"EngineSpin\") == 1 or var(\"EngineSpin\") == 2 then evt.PlayDecorationClip({engine_key}, "
            "\"spincycle\", \"loop\") end",
            "end",
        ]
        script.add(lines, (1, "Map load", None))
        script.hooks.append(f'RegisterMonsterKilledHook({KILL_HOOK}, "Lich Lab summoner", handlers[{KILL_HOOK}])')
        # DamageTriggerTarget "Resurrect": a hit on SkeletonMaster1 raises the buried SkeletonMaster52
        # (AutoResurrect.scr :OnResurrect: visible, solid, then its own script; it stays hidden otherwise).
        pairs = [(self.actor_index[source], self.actor_index[target], source, target)
                 for source, (target, _) in DAMAGE_TRIGGERS.items()
                 if source in self.actor_index and target in self.actor_index]
        if pairs:
            table = ", ".join(f"[{s}] = {t}" for s, t, _, _ in pairs)
            script.lines += [
                f"-- DamageTriggerTarget (AutoResurrect.scr :OnResurrect): {', '.join(f'{s} -> {t}' for _, _, s, t in pairs)}.",
                f"local RAISED_BY_HIT = {{{table}}}",
                f"handlers[{DAMAGE_HOOK}] = function(context)",
                "    local risen = RAISED_BY_HIT[context.actorIndex]",
                "    if risen == nil or var(\"Risen\" .. risen) == 1 then return end",
                "    set(\"Risen\" .. risen, 1)",
                "    evt.SetMonsterBit(risen, MonsterBits.Invisible, false)",
                "    evt.SetMonsterBit(risen, MonsterBits.Hostile, true)",
                "    evt.WakeActor(risen)",
                "end",
            ]
            script.hooks.append(f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Lich Lab resurrect on hit", '
                                f'handlers[{DAMAGE_HOOK}])')
        return script.finish(on_load=[1])

    @staticmethod
    def entity_index(build, anchor: str) -> int:
        """A decoration's entity index in the BLV (its clip key when it has no event_id_primary)."""
        entities = build.content.package.metadata["entities"]
        index = next(i for i, e in enumerate(entities) if e["id"] == anchor)
        if entities[index]["event_id_primary"]:
            raise SystemExit(f"{anchor} has a SetSprite key: use it")
        return index

    def report(self, build) -> dict:
        return {"scripted": {"pickups": self.pickups, "pod_box": self.pod_box,
                             "positions": {k: v for k, v in self.positions.items()}}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, LichLab()))
