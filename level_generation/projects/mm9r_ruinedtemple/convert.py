#!/usr/bin/env python3
"""
Ruined Temple, MM9 rework: MM9's RUINEDTEMPLE.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_ruinedtemple/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_ruinedtemple/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules; this file adds the temple's population (props.json from
../../props/mm9_ruinedtemple_claude, the perception hints, the genie) and its scripted objects as native Lua, each
citing what it reproduces (README.md, "Scripted objects"):
- the entrance's plank floor gives way under the party (Trigger0/Trigger1 destroy DestructableBrush6 and glass1-8);
- the sun buttons on the two hidden doors (door object wiring): SunButton opens HiddenDoor, SunButton4 opens HiddenDoor2,
  which unlocks LeftDoor; SunButton2/SunButton3 on the doors' far sides are their DoubleDoorName pairs and open
  them too; HiddenButton/HiddenButton2 open HiddenDoor3;
- the elevator (SunTempleButtons.scr): six symbol buttons, the main button on the lift, SecondButton at its foot;
- the crypt (RT_CounterBalance.scr): PrisonButton2 drops the counterbalance onto the crypt lid; the dirt plugs of the
  shaft under it (DestructableBrush0-5) break; PrisonButton3 in the tunnel opens DoorCryptEscape0 and the cell door;
- the Tree of Life (TreeofLife.scr): item 241, key 256, arms the second cave-in;
- the cave-ins (RT_CaveIn.scr): TriggerCaveIn0 at the hidden door, TriggerCaveIn1 on the way out with the Tree;
- the genie (GenieCrystal.scr, ColloidalGenie.scr): the lamp calls a genie who grants one wish (dialogue 435);
- the scrolls (BookLetter.scr 502, 503).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import review_root  # noqa: E402
from dungeon import lua, tables  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402
from quest_xp import balanced_experience  # noqa: E402

PROPS = PROJECT / "props.json"

# MM9's PerceptionBrushes: the red glow on the real sun buttons, the elevator's right symbols, the counterbalance and the
# dirt plugs, seen by a party whose Perception reaches the PerceptionValue (8 on all eleven brushes here).
PERCEPTION_TEXTURE = "sprites\\perception.spr"
PERCEPTION_COG = 300                # brush k (PerceptionBrush<k>): cog PERCEPTION_COG + k
PERCEPTION_SKILL = 29               # evt.CheckSkill's id: the party's best Perception value (mastery counted)
PERCEPTION_OPACITY = 0.35           # the brushes' Alpha (times the texture's own)
FRAME_FLAGS = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}
# MM9's translucent surfaces (the Translucent bit), as translucent faces: alias -> opacity (brush Alpha; the texture's
# alpha on top): the webs (WorldObject14-45, Alpha 0.7), the chains, the rail's ladder wood, the leaded glass.
# (opacity, two-sided): the glass and the chains are single polygons MM9 draws from both sides; the webs come in pairs.
TRANSLUCENT = {"WEB32N735S": (0.7, False), "CHAIF3VQ5B": (1.0, True), "RWOOMBH4KX": (1.0, True),
               "RUINB0UT4A": (1.0, True)}

# --- Events, cogs, timers ----------------------------------------------------------------------------------------------
EV = {"SunButton": 201, "SunButton2": 202, "SunButton3": 203, "SunButton4": 204, "HiddenButton": 205,
      "HiddenButton2": 206, "LeftDoor": 207, "StarButton1": 210, "StarButton2": 211, "DiamondButton1": 212,
      "DiamondButton2": 213, "MoonButton1": 214, "MoonButton2": 215, "MainButton": 216, "SecondButton": 217,
      "PrisonButton2": 220, "PrisonButton3": 221}
PLUGS = [f"DestructableBrush{k}" for k in range(6)]      # the shaft's dirt plugs; PerceptionBrush4-9 mark them
EV_PLUG = {name: 230 + k for k, name in enumerate(PLUGS)}   # a plug's destroyed event (weapons or its click)
# The other scene destructibles' destroyed events: DB_Crypt0 (DeathTrigger TriggerHostile0), the cave-ins' rails and
# ceiling (DeathTrigger DBEffectsTrigger1/2)
EV_BROKEN = {"DB_Crypt0": 244, "DB_RailLeft": 245, "DB_RailRight": 246, "DB_CeilingLeft": 247, "DB_CeilingRight": 248}
EV_TREE, EV_LAMP, EV_LETTER = 240, 241, {"Prop7": 242, "Prop8": 243}
COG_LAMP = 321
T_POLL, T_HIDDEN, T_HIDDEN2, T_HIDDEN3 = 400, 401, 402, 403
T_CRYPT, T_CAVE_A_LEFT, T_CAVE_A_RIGHT, T_CAVE_B_LEFT, T_CAVE_B_RIGHT = 404, 405, 406, 407, 408
T_GENIE_APPEAR, T_GENIE_GONE, T_PRISON_DOOR = 409, 410, 411
# Symbol buttons (SunTempleButtons.scr): each sends its toggle message on open and on close. MM9 wires MoonButton1 to
# "Star1" (not "Moon1"), so Moon1 never changes; kept as MM9 plays it.
SYMBOLS = {"StarButton1": "Star1", "StarButton2": "Star2", "DiamondButton1": "Diamond1",
           "DiamondButton2": "Diamond2", "MoonButton1": "Star1", "MoonButton2": "Moon2"}
SYMBOL_HINTS = {"StarButton1": "PerceptionBrush2", "DiamondButton2": "PerceptionBrush1"}
KEY_TREE, ITEM_TREE = 256, 241
WISH_KEYS = {5022: "gold", 5023: "experience", 5024: "item", 5025: "attribute"}
GENIE_RUDE = 435
LETTERS = {  # MM9's BOOK AND SCROLL TEXT.csv rows the scrolls show (BookLetter.scr DoLetter <item>)
    "Prop7": ("Excerpt from Book", "..And Igdrasa said, \"Let light travel through the world\", and it was so.  Her "
              "worshippers praised her as being just and good.  All creatures mourned when she traveled on to the next "
              "world.  She bade them not to.  She asked that they remember her, and wait patiently for their time to "
              "join her."),
    "Prop8": ("Diary Entry", "..Today was the day I was supposed to be shown the Ritual of Consecration.  I don't "
              "understand why the Elders still have not shown me!  Perhaps I have not been pious enough.  I shall speak "
              "to..perhaps he will see the light, so to speak.."),
}
# MM9's bodies: the ABC's AnimBinding half extents (x, y) in LT, times MONSTERS.txt Scale (1 for all five) and 2.56:
# radius = x, height = 2 y. The shared rows carry 60-70 wide, 170-220 tall stand-ins (README, monster reach).
BODY_LT = {"Skeleton": (15, 35), "SkeletonWarrior": (15, 37), "SkeletonMaster": (15, 37), "Dagrell": (25, 29),
           "SpectreDagrell": (25, 29)}
# Trigger volumes polled four times a second (MM9 fires them on any part of the party in their box).
VOLUMES = ["Trigger0", "Trigger1", "TriggerCaveIn0", "TriggerCaveIn1", "TriggerHostile0"]
# Trigger1 lies under the skylight frame's low lattice (56 LT over the floor): the native party (a 37-unit cylinder,
# 170 tall) is stopped by the lattice short of the box, where MM9's party box already reaches it. Its box grows by
# 100 units on every side, so a party pressing against the lattice sets it off.
VOLUME_MARGIN = {"Trigger1": 100}
# MM9's camera quakes and dust (EarthQuake and Fire objects; devdocs/mm9_rework/MM9_CUTSCENES.md section 5) as
# evt.CameraShake and the mm9:smoke effect in the handlers of what sets them off. TriggerCaveIn0/1 shake QuakeObject0/2
# at once. The relay triggers MM9 parks above the roof, DBEffectsTrigger0-2 (never touched), turn their DustObject on
# and shake their DBQuakeObject when TriggerHostile0 fires (0: DB_Crypt0's death or the party at the shaft's foot, once)
# and when a cave-in rail (1) or ceiling (2) breaks (each brush's death, twice per cave-in). QuakeObject1 has no sender.
QUAKES = ["QuakeObject0", "QuakeObject2", "DBQuakeObject0", "DBQuakeObject1", "DBQuakeObject2"]
DUSTS = ["DustObject0", "DustObject1", "DustObject2"]
DUST_EFFECT, DUST_SCALE = "mm9:smoke", 1.5
QUAKE_CLAMP = 12.0                  # MM9's client clamps the view offset at 12 units


def quake_shake(values: dict) -> tuple[float, float, float]:
    """An EarthQuake as evt.CameraShake's (intensity, seconds, radius): ShakeAmount clamped to 12 over 12, its
    QuakeDuration plus the decay to nothing, OuterRadius (MM9's all-or-nothing range) in native units."""
    amount = min(float(values["ShakeAmount"]), QUAKE_CLAMP)
    decay = float(values["DecayRate"])
    seconds = float(values["QuakeDuration"]) + (amount / decay if decay > 0 else 0.0)
    return amount / QUAKE_CLAMP, seconds, float(values["OuterRadius"]) * SCALE


def effects_lua(properties, native) -> list[str]:
    """The quakes' and the dust's Lua (tables and helpers); properties(name) -> the DAT values, native(lt) -> x, y, z."""
    def xyz(name):
        return ", ".join(str(int(round(float(v)))) for v in native(properties(name)["Pos"]))

    quakes = []
    for name in QUAKES:
        intensity, seconds, radius = quake_shake(properties(name))
        quakes.append(f"{name} = {{{intensity:g}, {round(seconds, 2):g}, {xyz(name)}, {int(round(radius))}}}")
    dusts = [f"{name} = {{{xyz(name)}}}" for name in DUSTS]
    return [
        "-- The quakes and the dust (EarthQuake, Fire): ShakeAmount 100 clamped to MM9's 12 units (intensity 1) for",
        "-- QuakeDuration plus the decay, felt within OuterRadius of the object; the dust is a puff of smoke there.",
        f"local QUAKES = {{{', '.join(quakes)}}}",
        "local function quake(name) local q = QUAKES[name]; evt.CameraShake(q[1], q[2], q[3], q[4], q[5], q[6], q[6]) end",
        f"local DUST = {{{', '.join(dusts)}}}",
        f"local function dust(name) local p = DUST[name]; evt.SpawnWorldEffect(\"{DUST_EFFECT}\", p[1], p[2], p[3], "
        f"{DUST_SCALE:g}) end",
        "-- DBEffectsTrigger<k>: DustObject<k> on, DBQuakeObject<k> Trigger.",
        "local function dbEffects(k) dust(\"DustObject\" .. k); quake(\"DBQuakeObject\" .. k) end",
        "-- TriggerHostile0 (one activation): DB_Crypt0's death or the party's touch relays DBEffectsTrigger0.",
        "local function hostile0()",
        "    if var(\"Hostile0Fired\") == 1 then return end",
        "    dbEffects(0)",
        "    set(\"Hostile0Fired\", 1)",
        "end",
    ]


# The blue torches' light (0, 128, 255) as MM9's own lightmaps show it: over the neutral floor of every zone their
# contribution has G/B 0.26 (entrance 0.211 / 0.253 / 0.371: +0.04 green, +0.16 blue), not the authored 0.5; at 0.5 the
# bake read cyan (hue_vs_lightmaps.py: G/R 1.3-1.75 x MM9's). Halved, the zone means matched but the pools round each
# torch, where the bake's blue clips at max_lighting 1 and its green keeps rising, read teal (top 5 % G/B 0.83 against
# MM9's 0.57, 2026-10-31): the torches carry 0.3 of their green in the BLV.
BLUE_TORCH, BLUE_TORCH_GREEN = [0, 128, 255], 0.3
# The white fills (255, 255, 255 at BrightScale 0.2-0.6, over the main temple, the pew hall and the crypt level): in MM9's
# lightmaps they add only 0.02-0.04 of red over the zones' neutral floor (main temple R 0.224, pew hall 0.212, against
# 0.192 in the torch-only south ruins); at colour x BrightScale the bake put 0.12-0.14 there (README, Baked lighting).
# They carry a quarter of that in the BLV.
WHITE_FILL, WHITE_FILL_SCALE = [255, 255, 255], 0.25


def blv_colour(colour, bright_scale: float) -> list:
    """A Light's BLV colour: colour x BrightScale, the blue torches' green and the white fills' strength as MM9's
    lightmaps have them."""
    green = BLUE_TORCH_GREEN if list(colour) == BLUE_TORCH else 1.0
    fill = WHITE_FILL_SCALE if list(colour) == WHITE_FILL else 1.0
    return [int(round(c * bright_scale * fill * (green if k == 1 else 1.0))) for k, c in enumerate(colour)]


def rude_exit_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a dialogue with actor object `index` runs when it closes."""
    return 50000 + index


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


class RuinedTemple(dungeon.Hooks):
    generator = "mm9r_ruinedtemple"
    mover_events = {name: (event, "click") for name, event in EV.items()}

    def destructible_events(self, build) -> dict:
        """The scene destructibles' deaths (dungeon/destructibles.py `break`): the plugs, the crypt lid, the cave-ins'
        rails and ceiling."""
        return {name: (event, 0) for name, event in {**EV_PLUG, **EV_BROKEN}.items()}

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        self.scale_lights(build)
        if PROPS.exists():
            content.props(PROPS, events={"Treeoflife": EV_TREE, "Lamp": EV_LAMP, **EV_LETTER},
                          cogs={"Lamp": COG_LAMP})
        else:
            print("note: props.json is missing; no decorations or chests placed")
        self.place_perception_hints(build)
        self.boxes = {}
        for name in VOLUMES:
            p = source.properties(name)
            centre, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
            low, high = project.native(centre - dims), project.native(centre + dims)
            grow = np.array([VOLUME_MARGIN.get(name, 0)] * 2 + [0])
            low, high = np.minimum(low, high) - grow, np.maximum(low, high) + grow
            self.boxes[name] = [np.minimum(low, high).round().astype(int).tolist(),
                                np.maximum(low, high).round().astype(int).tolist()]
        # The genie stands on the floor under MM9's Smoke marker (ColloidalGenie.scr: SetPOS to the marker + 36 up).
        smoke = source.properties("Smoke")["Pos"]
        floor = content.floor_at(smoke[0], smoke[2], smoke[1] + 40)
        self.genie_point = project.native([smoke[0], floor, smoke[2]]).round().astype(int).tolist()
        self.smoke_point = project.native(smoke).round().astype(int).tolist()   # hAppear: the genie's effects

    def scale_lights(self, build) -> None:
        """MM9 weights each Light by its BrightScale (here 0.2-1.0: the blue torches 0.6, the white fills 0.2-0.6, the
        shaft's green 1.0); the shared converter writes the colour as authored, which made the white fills twice as
        strong as MM9's against the blue torches and the bake grey (README, Baked lighting). The BLV lights carry
        colour x BrightScale; the profile's direct_scale makes up the level."""
        scale = {light["name"]: light["bright_scale"] for light in build.lights}
        for record in build.package.metadata["lights"]:
            record["color"] = blv_colour(record["color"], scale.get(record["id"], 1.0))
        for light in build.lights:
            light["colour_in_blv"] = blv_colour(light["colour"], light["bright_scale"])
            if not light["kept"]:
                # A bake-only light (lighting.py reads work/lights.json: its colour, strength by BrightScale): the
                # same hue fit, without the BrightScale the bake applies itself.
                light["colour_authored"] = light["colour"]
                light["colour"] = blv_colour(light["colour"], 1.0)

    def place_perception_hints(self, build) -> None:
        """Each PerceptionBrush's visible polygons (MM9's Perception.spr; the rest of the brush is Invisible.dtx) as
        untouchable translucent faces with a cog, in the room of the air beside them, drawn from both sides
        (Drangheim Prison's route)."""
        package, source = build.package, build.source
        self.hints, self.hint_faces = {}, 0
        difficulties = perception_difficulties_by_model_name(source.world)
        names = sorted(difficulties, key=lambda n: int(n[len("perceptionbrush"):]))
        self.hint_difficulty = max(difficulties[n] for n in names)
        for lower in names:
            k = int(lower[len("perceptionbrush"):])
            name = next(model for model in source.models if model.lower() == lower)
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                rooms = build.content.rooms
                room = room_id(_side_room(rooms, polygon, 1) or _side_room(rooms, polygon, -1)
                               or rooms.owner(polygon.points.mean(0)))
                node = f"TRIGGER_perception_{name}_{i}"
                package.add_polygon(node, polygon, build.stats)
                package.room_nodes[room].append(node)
                package.metadata["surfaces"].append({"id": node[8:], "source_node": node, "flags": ["untouchable"],
                                                     "cog_number": PERCEPTION_COG + k})
                self.hint_faces += 1
            self.hints[name] = PERCEPTION_COG + k

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out = []
        self.genie = None
        for o in source.objects:
            if o["class"] not in build.project.monster_classes or o["name"] not in bases:
                continue
            if o["name"] == "Genie":
                # ColloidalGenie.scr: the party's friend, out of sight until the lamp calls it; it stands where the
                # smoke rises (placed there hidden from the start) and talks when clicked (dialogue 435).
                smoke = source.properties("Smoke")["Pos"]
                at_smoke = dict(o, properties=dict(o["properties"], Pos=[smoke[0], smoke[1] + 40, smoke[2]]))
                # MM9's body at the DAT's Scale 0.94, which replaces the Colloidal Warrior row's 1.75
                actor = content.actor(at_smoke, bases["Genie"], sector_of_room, hidden=True, friendly=True,
                                      **placed_body(bases["Genie"]["monster_id"], o["properties"]))
                actor["immobile"] = True
                actor["mm9_rude_id"] = GENIE_RUDE
                actor["mm9_source_object_index"] = o["index"]
                content.report["actors"][-1]["note"] = "stands at the Smoke marker, hidden until the lamp calls it"
                self.genie = {"actor": actor["actor_index"], "object": o["index"]}
                out.append(actor)
                continue
            actor = content.actor(o, bases[o["name"]], sector_of_room)
            half_x, half_y = BODY_LT[o["class"]]
            actor["radius"] = int(round(half_x * SCALE))
            actor["height"] = int(round(2 * half_y * SCALE))
            out.append(actor)
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Ruined Temple")
        script.doors()
        script.chests()
        lines = script.lines
        hint = self.hints
        index = {name: build.source.by_name[name.lower()]["index"] for name in EV_BROKEN}     # scene destructible ids
        groups = ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(script.groups.items()))
        lines += [
            "-- Mover groups (each MM9 model's mechanism and its invisible collision part move together).",
            f"local GROUPS = {{{groups}}}",
            "local function openG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Open) end end",
            "local function closeG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Close) end end",
            "local function toggleG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Trigger) end end",
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "-- MM9 fires a trigger on any part of the party in its box: the party's 37-unit radius widens the box.",
            "local function inBox(b, x, y, z) return x >= b[1][1] - 37 and x <= b[2][1] + 37 and y >= b[1][2] - 37 "
            "and y <= b[2][2] + 37 and z + 170 >= b[1][3] and z <= b[2][3] end",
            "-- A PerceptionBrush switched off by MM9's wiring stays hidden; the rest show to a party with the Perception.",
            "local function hintOff(cog) set(\"HintOff\" .. cog, 1); evt.SetFacetBit(cog, FacetBits.Invisible, true) end",
            "local function hintOn(cog) set(\"HintOff\" .. cog, 0); set(\"PerceptionHints\", 0) end",
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            *effects_lua(build.source.properties, build.project.native),
            "",
            "-- The entrance (Trigger0, Trigger1, each triggering the other): the plank floor and the glass under it give way",
            "-- (MM9 destroys DestructableBrush6 and glass1-8); they drop out of sight and the party falls into the hall.",
            "local function collapse()",
            "    if var(\"FloorFallen\") == 1 then return end",
            "    set(\"FloorFallen\", 1)",
            "    openG(\"EntranceFloor\")",
            "    evt.PlaySoundName(\"sounds/weapons/eqhammerimpact.wav\", 0, 0, 0)",
            "end",
            "",
            "-- The hidden doors (door object wiring): SunButton opens HiddenDoor and SunButton4 opens HiddenDoor2, each with",
            "-- both sun buttons riding it (MM9 AttachTo). SunButton2 and SunButton3, on the doors' far sides, are MM9's",
            "-- DoubleDoorName pairs of SunButton and SunButton4: a press moves both buttons, so it opens the door from that",
            "-- side too (as decoys the party that rode the lift down or climbed the spiral could not get out).",
            "-- A door shuts after 10 s (CloseWaitTime) and its buttons unlock. HiddenDoor2 opening unlocks LeftDoor.",
            "local function hiddenOpen(door, a, b, timer, cog)",
            "    if var(\"Open\" .. door) == 1 then return end",
            "    set(\"Open\" .. door, 1)",
            "    openG(door); openG(a); openG(b)",
            "    if cog then hintOff(cog) end",
            "    arm(timer, 10 + 88 / 100)",
            "end",
            "local function hiddenClose(door, a, b, cog)",
            "    closeG(door); closeG(a); closeG(b)",
            "    set(\"Open\" .. door, 0)",
            "    if cog then hintOn(cog) end",
            "end",
            f"handlers[{EV['SunButton']}] = function() hiddenOpen(\"HiddenDoor\", \"SunButton\", \"SunButton2\", {T_HIDDEN}, "
            f"{hint['PerceptionBrush0']}) end",
            f"handlers[{EV['SunButton4']}] = function()",
            f"    hiddenOpen(\"HiddenDoor2\", \"SunButton3\", \"SunButton4\", {T_HIDDEN2}, {hint['PerceptionBrush10']})",
            "    set(\"LeftDoorUnlocked\", 1)",
            "end",
            f"handlers[{EV['SunButton2']}] = handlers[{EV['SunButton']}]   -- SunButton's DoubleDoorName pair",
            f"handlers[{EV['SunButton3']}] = handlers[{EV['SunButton4']}]   -- SunButton4's DoubleDoorName pair",
            f"handlers[{T_HIDDEN}] = function() if fired({T_HIDDEN}) then hiddenClose(\"HiddenDoor\", \"SunButton\", "
            f"\"SunButton2\", {hint['PerceptionBrush0']}) end end",
            f"handlers[{T_HIDDEN2}] = function() if fired({T_HIDDEN2}) then hiddenClose(\"HiddenDoor2\", \"SunButton3\", "
            f"\"SunButton4\", {hint['PerceptionBrush10']}) end end",
            "local function hiddenButton(button)",
            "    openG(button)",
            "    if var(\"OpenHiddenDoor3\") == 1 then return end",
            "    set(\"OpenHiddenDoor3\", 1)",
            "    openG(\"HiddenDoor3\")",
            f"    arm({T_HIDDEN3}, 10 + 88 / 100)",
            "end",
            f"handlers[{EV['HiddenButton']}] = function() hiddenButton(\"HiddenButton\") end",
            f"handlers[{EV['HiddenButton2']}] = function() hiddenButton(\"HiddenButton2\") end",
            f"handlers[{T_HIDDEN3}] = function()",
            f"    if not fired({T_HIDDEN3}) then return end",
            "    closeG(\"HiddenDoor3\"); closeG(\"HiddenButton\"); closeG(\"HiddenButton2\")",
            "    set(\"OpenHiddenDoor3\", 0)",
            "end",
            f"handlers[{EV['LeftDoor']}] = function()   -- Locked until HiddenDoor2 opens",
            "    if var(\"LeftDoorUnlocked\") ~= 1 then evt.StatusText(\"The door is locked.\") return end",
            "    toggleG(\"LeftDoor\")",
            "end",
            "",
            "-- The elevator (SunTempleButtons.scr): each symbol button toggles in and out and toggles its symbol; the main",
            "-- button on the lift sends it when Star1 and Diamond2 are set and Star2, Diamond1, Moon1, Moon2 are not",
            "-- (MM9 wires MoonButton1 to Star1, so Moon1 stays unset). SecondButton at the foot calls the lift; MM9's lift",
            "-- stays where it went (Sticky): the main button and SecondButton send it to the other end here.",
            "local function symbol(button, flag, cog)",
            "    toggleG(button)",
            "    local on = 1 - var(\"Sym\" .. flag)",
            "    set(\"Sym\" .. flag, on)",
            "    set(\"Pressed\" .. button, 1 - var(\"Pressed\" .. button))",
            "    if cog then if var(\"Pressed\" .. button) == 1 then hintOff(cog) else hintOn(cog) end end",
            "end",
        ]
        for button, flag in SYMBOLS.items():
            cog = hint[SYMBOL_HINTS[button]] if button in SYMBOL_HINTS else "nil"
            lines.append(f"handlers[{EV[button]}] = function() symbol(\"{button}\", \"{flag}\", {cog}) end")
        lines += [
            "local function sendLift()",
            "    local down = 1 - var(\"LiftDown\")",
            "    set(\"LiftDown\", down)",
            "    set(\"LiftTrips\", var(\"LiftTrips\") + 1)",
            "    if down == 1 then openG(\"MainElevator\"); openG(\"MainButton\") else closeG(\"MainElevator\"); "
            "closeG(\"MainButton\") end",
            "end",
            f"handlers[{EV['MainButton']}] = function()",
            "    if var(\"SymStar1\") == 1 and var(\"SymStar2\") == 0 and var(\"SymDiamond1\") == 0 and var(\"SymDiamond2\") == 1",
            "            and var(\"SymMoon1\") == 0 and var(\"SymMoon2\") == 0 then",
            "        sendLift()",
            "    else",
            "        evt.StatusText(\"Nothing happens.\")",
            "    end",
            "end",
            f"handlers[{EV['SecondButton']}] = function()",
            "    openG(\"SecondButton\")",
            "    sendLift()",
            f"    arm({T_PRISON_DOOR + 1}, 1)",
            "end",
            f"handlers[{T_PRISON_DOOR + 1}] = function() if fired({T_PRISON_DOOR + 1}) then closeG(\"SecondButton\") end end",
            "",
            "-- The crypt (RT_CounterBalance.scr): PrisonButton2 drops the counterbalance (252 LT at 300 LT/s) onto the crypt",
            "-- lid, which breaks (DB_Crypt0 destroyed); the shaft under it is plugged with packed dirt (DestructableBrush0-5,",
            "-- 20 hit points each, scene destructibles): weapons or a click break a plug. PrisonButton3 in the tunnel below unlocks and opens",
            "-- DoorCryptEscape0, which opens the Tree of Life's cell (PrisonDoor, PrisonBars).",
            f"handlers[{EV['PrisonButton2']}] = function()",
            "    if var(\"CounterBalanceFallen\") == 1 then return end",
            "    set(\"CounterBalanceFallen\", 1)",
            "    openG(\"PrisonButton2\"); openG(\"WO_CounterBalance\")",
            f"    arm({T_CRYPT}, 0.9)",
            "end",
            f"handlers[{T_CRYPT}] = function()",
            f"    if not fired({T_CRYPT}) then return end",
            "    evt.PlaySoundName(\"sounds/door/doorslammetal01.wav\", 0, 0, 0)",
            f"    evt.DestroyDestructible({index['DB_Crypt0']})",
            "end",
            f"handlers[{EV_BROKEN['DB_Crypt0']}] = function()   -- DB_Crypt0 broken (the counterbalance, or weapons)",
            "    hostile0()   -- DB_Crypt0's death triggers TriggerHostile0",
            "    set(\"CryptOpen\", 1)",
            "end",
        ]
        for k, plug in enumerate(PLUGS):
            lines += [f"handlers[{EV_PLUG[plug]}] = function()   -- {plug} broken: PerceptionBrush{k + 4} goes off with it",
                      f"    set(\"Broken{plug}\", 1)",
                      f"    hintOff({hint[f'PerceptionBrush{k + 4}']})",
                      "    evt.StatusText(\"The packed dirt gives way.\")",
                      "end"]
        lines += [
            f"handlers[{EV['PrisonButton3']}] = function()",
            "    if var(\"EscapeOpen\") == 1 then return end",
            "    set(\"EscapeOpen\", 1)",
            "    openG(\"PrisonButton3\"); openG(\"DoorCryptEscape0\")",
            f"    arm({T_PRISON_DOOR}, 0.5 + 120 / 25)",
            "end",
            f"handlers[{T_PRISON_DOOR}] = function()   -- DoorCryptEscape0 is open: PrisonDoor Unlock, Open",
            f"    if not fired({T_PRISON_DOOR}) then return end",
            "    openG(\"PrisonDoor\")   -- the bars and the door",
            "    -- SunTemplePrison.scr :HandlePrisonGateOpen: RopeWheel reverse, on (the winch turns from then on)",
            "    evt.SpinMover(DOORS.RopeWheel, \"reverse\"); evt.SpinMover(DOORS.RopeWheel, \"on\")",
            "end",
            "",
            f"-- The Tree of Life (TreeofLife.scr): a world item ({ITEM_TREE}, dungeon/pickups.py); its pickup gives key "
            f"{KEY_TREE} and arms TriggerCaveIn1.",
            f"handlers[{EV_TREE}] = function()",
            f"    if MM9.hasKey({KEY_TREE}) == 1 then return end",
            f"    MM9.giveKey({KEY_TREE})",
            "    set(\"CaveIn1Armed\", 1)",
            "end",
            "",
            "-- The cave-ins (RT_CaveIn.scr): the rails (A) or the ceiling (B) break and the rocks drop onto their markers",
            "-- (220 LT/s) half a second (left) and a second (right) after the trigger; MM9's floor slabs under them",
            "-- shatter into the same floor (not built: overrides.yml). The trigger shakes its QuakeObject; each broken",
            "-- rail or ceiling brush (a scene destructible: weapons break it too) sends its DBEffectsTrigger (dust and a",
            "-- quake) from its destroyed event.",
            "local function caveIn(left, right, timerLeft, timerRight, quakeName)",
            "    evt.PlaySoundName(\"sounds/weapons/eqhammerimpact.wav\", 0, 0, 0)",
            "    quake(quakeName)",
            "    arm(timerLeft, 0.5); arm(timerRight, 1)",
            "end",
            f"handlers[{T_CAVE_A_LEFT}] = function() if fired({T_CAVE_A_LEFT}) then "
            f"evt.DestroyDestructible({index['DB_RailLeft']}); openG(\"CaveInLeft\") end end",
            f"handlers[{T_CAVE_A_RIGHT}] = function() if fired({T_CAVE_A_RIGHT}) then "
            f"evt.DestroyDestructible({index['DB_RailRight']}); openG(\"CaveInRight\"); set(\"CaveIn0Done\", 1) end end",
            f"handlers[{T_CAVE_B_LEFT}] = function() if fired({T_CAVE_B_LEFT}) then "
            f"evt.DestroyDestructible({index['DB_CeilingLeft']}); openG(\"CaveInLeftB\") end end",
            f"handlers[{T_CAVE_B_RIGHT}] = function() if fired({T_CAVE_B_RIGHT}) then "
            f"evt.DestroyDestructible({index['DB_CeilingRight']}); openG(\"CaveInRightB\"); set(\"CaveIn1Done\", 1) end end",
            *[f"handlers[{EV_BROKEN[n]}] = function() dbEffects({1 if 'Rail' in n else 2}) end   -- {n} broken"
              for n in ("DB_RailLeft", "DB_RailRight", "DB_CeilingLeft", "DB_CeilingRight")],
            "",
        ]
        boxes = self.boxes
        runs = {
            "Trigger0": "collapse()", "Trigger1": "collapse()",
            "TriggerCaveIn0": f"caveIn(\"Left\", \"Right\", {T_CAVE_A_LEFT}, {T_CAVE_A_RIGHT}, \"QuakeObject0\")",
            "TriggerCaveIn1": f"caveIn(\"LeftB\", \"RightB\", {T_CAVE_B_LEFT}, {T_CAVE_B_RIGHT}, \"QuakeObject2\")",
            "TriggerHostile0": "set(\"ShaftBottomReached\", 1); hostile0()",   # DBEffectsTrigger0: dust and a quake
        }
        armed = {"TriggerCaveIn1": "var(\"CaveIn1Armed\") == 1"}
        volume_lua = ",\n".join(
            f"    {{name = \"{name}\", box = {{{lua.point(boxes[name][0])}, {lua.point(boxes[name][1])}}}, "
            f"armed = function() return {armed.get(name, 'true')} end, run = function() {runs[name]} end}}"
            for name in VOLUMES)
        lines += [
            "-- MM9's Trigger volumes, polled four times a second; each fires once (MM9 turns each off after it fires).",
            "local VOLUMES = {",
            volume_lua,
            "}",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for _, v in ipairs(VOLUMES) do",
            "        if var(\"Done\" .. v.name) == 0 and v.armed() and inBox(v.box, x, y, z) then",
            "            set(\"Done\" .. v.name, 1)",
            "            v.run()",
            "        end",
            "    end",
            "end",
            "",
        ]
        genie = self.genie
        lines += [
            "-- The genie (GenieCrystal.scr, ColloidalGenie.scr): the lamp calls it once; two seconds later it stands in",
            f"-- the smoke over the lamp. MM9 opens its dialogue ({GENIE_RUDE}) by itself; here the party clicks it. The wish",
            "-- (keys 5022-5025 from the dialogue): 5000 gold, 5000 experience, a random item 234-238, or Might +10 for the",
            "-- active member (GiveAttribute 0, 10). Three seconds after the talk the genie vanishes.",
            f"local GENIE = {genie['actor']}",
            "-- ColloidalGenie.scr's DoClientFX at its Smoke marker (hAppear): black smoke on the call, mist as it",
            "-- appears, mist and black smoke as it goes",
            f"local GENIE_SMOKE = {lua.point(self.smoke_point)}",
            "local function genieFx(effect) evt.SpawnWorldEffect(effect, GENIE_SMOKE[1], GENIE_SMOKE[2], GENIE_SMOKE[3], 1) end",
            f"handlers[{EV_LAMP}] = function()",
            "    if var(\"GenieCalled\") == 1 then return end",
            "    set(\"GenieCalled\", 1)",
            "    genieFx(\"mm9:blacksmoke\")",
            "    evt.PlaySoundName(\"sounds/animsounds/dragon/fidget1.wav\", 0, 0, 0)",
            f"    arm({T_GENIE_APPEAR}, 2)",
            "end",
            f"handlers[{T_GENIE_APPEAR}] = function()",
            f"    if not fired({T_GENIE_APPEAR}) then return end",
            "    set(\"GenieShown\", 1)",
            "    genieFx(\"mm9:mist\")",
            "    evt.SetMonsterBit(GENIE, ActorAttribute.Invisible, 0)",
            "    evt.PlaySoundName(\"sounds/animsounds/zombie/ressurect2.wav\", 0, 0, 0)",
            "    evt.StatusText(\"A genie rises out of the lamp's smoke.\")",
            "end",
            f"handlers[{rude_exit_event(genie['object'])}] = function()   -- ColloidalGenie.scr :GrantWish",
            "    if var(\"WishGranted\") == 1 then return end",
            "    set(\"WishGranted\", 1)",
            "    if MM9.hasKey(5022) == 1 then MM9.giveGold(5000); set(\"Wish\", 1)",
            f"    elseif MM9.hasKey(5023) == 1 then MM9.giveExperience({balanced_experience(5000, 5023)}); "
            "set(\"Wish\", 2)",
            "    elseif MM9.hasKey(5024) == 1 then give(MM9.random(234, 238, 1), \"ruinedtemple:Genie\"); set(\"Wish\", 3)",
            "    elseif MM9.hasKey(5025) == 1 then AddValue(BaseMight, 10); set(\"Wish\", 4)",
            "    end",
            f"    arm({T_GENIE_GONE}, 3)",
            "end",
            f"handlers[{T_GENIE_GONE}] = function()",
            f"    if not fired({T_GENIE_GONE}) then return end",
            "    genieFx(\"mm9:mist\"); genieFx(\"mm9:blacksmoke\")",
            "    MM9.removeActor(GENIE)",
            "    set(\"GenieGone\", 1)",
            "end",
            "",
            "-- The scrolls (BookLetter.scr DoLetter): MM9's book and scroll texts.",
        ]
        for name, event in EV_LETTER.items():
            title, text = LETTERS[name]
            lines.append(f"handlers[{event}] = function() evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end"
                         f"   -- {name}")
        lines += [
            "",
            f"-- The PerceptionBrushes: the red glow shows to a party with Perception {self.hint_difficulty} or better "
            "(MM9's PerceptionValue)",
            "-- unless MM9's wiring has switched the brush off; on load and every 3 s.",
            f"local HINTS = {{{', '.join(str(cog) for cog in self.hints.values())}}}",
            "local function updateHints()",
            f"    local want = evt.CheckSkill({PERCEPTION_SKILL}, 0, {self.hint_difficulty}) and 2 or 1",
            "    if var(\"PerceptionHints\") == want then return end",
            "    set(\"PerceptionHints\", want)",
            "    for _, cog in ipairs(HINTS) do",
            "        evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or var(\"HintOff\" .. cog) == 1)",
            "    end",
            "end",
            f"handlers[{T_POLL + 20}] = updateHints",
            "handlers[1] = function()   -- map load: what MM9 saves stays as it was left",
            f"    if var(\"GenieShown\") == 1 and var(\"GenieGone\") == 0 then evt.SetMonsterBit(GENIE, "
            "ActorAttribute.Invisible, 0) end",
            "    set(\"PerceptionHints\", 0)",
            "    updateHints()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "end",
            "",
        ]
        script.add([], *[(EV[name], name, "Button") for name in EV if name != "LeftDoor"],
                   (EV["LeftDoor"], "Door", "Door"),
                   *[(EV_PLUG[plug], "Packed dirt", None) for plug in PLUGS],
                   *[(event, name, None) for name, event in EV_BROKEN.items()],
                   (EV_TREE, "Tree of Life", None), (EV_LAMP, "Lamp", "Lamp"),
                   *[(event, "Scroll", "Scroll") for event in EV_LETTER.values()],
                   (rude_exit_event(genie["object"]), "Genie", None),
                   (T_POLL, "Trigger volumes", None, "timer"), (T_POLL + 20, "Perception hints", None, "timer"),
                   *[(t, "Timer", None, "timer") for t in (T_HIDDEN, T_HIDDEN2, T_HIDDEN3, T_CRYPT, T_CAVE_A_LEFT,
                                                           T_CAVE_A_RIGHT, T_CAVE_B_LEFT, T_CAVE_B_RIGHT,
                                                           T_GENIE_APPEAR, T_GENIE_GONE, T_PRISON_DOOR,
                                                           T_PRISON_DOOR + 1)],
                   (1, "Map load", None))
        return script.finish(on_load=[1])

    # --- scene ------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """MM9's translucent faces (webs, chains, the rail, the glass; found in the compiled BLV by texture) and the
        perception hints at their brushes' Alpha."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        hint_alias = build.source.aliases[PERCEPTION_TEXTURE]["alias"]
        faces, hints = {}, []
        for face in blv["faces"]:
            if face["is_portal"]:
                continue
            name = str(face.get("texture_name", ""))
            if name in TRANSLUCENT:
                faces.setdefault(TRANSLUCENT[name], []).append(face["index"])
            elif name.lower() == hint_alias.lower():
                hints.append(face["index"])
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        entries = scene.setdefault("translucent_faces", [])
        for (opacity, two_sided), ids in sorted(faces.items()):
            entries.append({"faces": sorted(ids), "opacity": opacity, "tint": [1.0, 1.0, 1.0], "two_sided": two_sided})
        entries.append({"faces": sorted(hints), "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0],
                        "two_sided": True})
        build.stats["translucent_faces"] = sum(len(e["faces"]) for e in entries)
        if build.project.install:
            self.install_frames(build, PERCEPTION_TEXTURE)

    def install_frames(self, build, texture: str) -> None:
        """An MM9 .spr as a texture frame sequence (the review root's engine table, as Drangheim Prison's)."""
        entry = build.source.aliases[texture]
        frames = [entry["alias"]] + [frame["alias"] for frame in entry["animation_frames"][1:]]
        relative = "engine/data_tables/texture_frame_data.txt"
        with tables.locked("review_tables.lock"):
            text = review_root.mirror_path(relative).read_text()
            if f"\n{frames[0]}\t" in text:
                return
            rows = [f"{name}\t0\t1\t{len(frames) if i == 0 else 0}\t{FRAME_FLAGS[i == 0, i < len(frames) - 1]}"
                    for i, name in enumerate(frames)]
            review_root.install(relative, (text.rstrip("\n") + "\n" + "\n".join(rows) + "\n").encode())

    def report(self, build) -> dict:
        return {"scripted": {"genie": getattr(self, "genie", None), "hints": getattr(self, "hints", {}),
                             "boxes": getattr(self, "boxes", {}), "genie_point": getattr(self, "genie_point", None)}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, RuinedTemple()))
