#!/usr/bin/env python3
"""
Lindisfarne Monastery, MM9 rework: MM9's LINDISFARNEMONASTERY.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_lindisfarnemonastery/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_lindisfarnemonastery/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the front-wall cut and the ladders; this file adds the sky mapping, the hillside's
outline workaround, the population (props.json from ../../props/mm9_lindisfarnemonastery_claude, 31 monks and NPCs)
and MM9's scripted objects as native Lua, each citing its .scr (README.md, "Scripted objects"):
- the monks' hostility (MonkHostility.inc): friendly until the party hurts or kills one; then the alarm bell rings and
  every monk turns hostile (and Thjorad can be taken);
- the bell puzzle (LindisfarneBell.scr, LindisfarneBellController.scr, the five ropes' OpenTriggers): a used bell swings
  (its Ring and Stop clips, the note on their model keys) and reports to the controller when it stops; Bell1 to Bell5
  in order gives key 9507 and 2000 experience, the bells peal, the Thjorad monks go to pray and Thjorad can be taken;
- Thjorad (Thjorad.scr): item 197 with key 31 (key 2 held) or 162, 1000 experience;
- the organ (25 keys, each a Door playing its note; NPC420.scr: key 9506 plays the hymn);
- the NPCs' dialogue ends (NPC282.scr Grehgknak: letter 419, the paladin promotion; NPC283.scr Abbot Leffery: the
  relic; key 254 at 5:00 and Robert Aefgil (NPC284.scr) appearing);
- the letters (BookLetter.scr 470-473).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from quest_xp import balanced_experience, experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
SKY_TEXELS_PER_LT = 0.2            # the sky faces: one sky04 tile about 2 500 LT wide (as Verhoffin's, Tasar's)
INVISIBLE_FACE = 0x00002000
OUTSIDE_Z_LT = -560                # faces whose centre lies south of this are the porch and the hillside (outside)

# --- events, cogs, timers, groups ------------------------------------------------------------------------------------
EV_THJORAD = 75
EV_LETTER = {"Prop5": 76, "Prop6": 77, "Prop7": 78, "Prop8": 79}          # BookLetter.scr "470".."473 Letter"
LETTER_ID = {"Prop5": 470, "Prop6": 471, "Prop7": 472, "Prop8": 473}
EV_BELL = {f"Bell{n}": 80 + n for n in range(1, 6)}                       # a click on a bell (its AddTrigger Use)
ROPES = {"Rope1": "Bell1", "Rope2": "Bell3", "Rope3": "Bell5", "Rope4": "Bell4", "Rope5": "Bell2"}   # OpenTrigger0
EV_ROPE = {name: 90 + k for k, name in enumerate(ROPES, 1)}
NOTES = ["C1", "C#1", "D1", "D#1", "E1", "F1", "F#1", "G1", "G#1", "A1", "A#1", "B1",
         "C2", "C#2", "D2", "D#2", "E2", "F2", "F#2", "G2", "G#2", "A2", "A#2", "B2", "E3"]
EV_KEY = {note: 130 + k for k, note in enumerate(NOTES)}       # after the door groups (100 + k)
T_RELEASE, T_FINALE, T_CLOCK, T_ORGAN = 260, 261, 262, 263
T_BELL = 270                        # + n: Bell<n>'s swing (its PlayAnim callbacks, model keys and Wait)
HYMN_SECONDS = 24                   # NPC420.scr :Play: LoopAnim play, then Wait 1 24 OnExit
DAMAGE_HOOK, KILL_HOOK = 96, 97
COG_THJORAD = 300
COG_BELL = 310                      # + n: Bell<n> (its ring and stop clips)
GROUP_MONKS, GROUP_THJORAD, GROUP_ROBERT = 1, 2, 3

# keys and items (raw MM9 numbers: keys are QBits 90000 + key, items MM9.ItemIds)
KEY_BELLS = 9507                    # LindisfarneBellController.scr :Finish
KEY_HYMN = 9506                     # NPC420.scr :PlaySong
ITEM_THJORAD, KEY_THJORAD_QUEST, KEY_THJORAD_A, KEY_THJORAD_B = 197, 2, 31, 162
ITEM_LETTER, KEY_LETTER_ASKED, KEY_LETTER_GIVEN = 419, 228, 229
KEY_PALADIN_ASKED, KEY_PALADIN_DONE = 236, 237
PALADIN_KEYS = [421, 422, 423, 424]
ITEM_RELIC, KEY_RELIC_FOUND, KEY_RELIC_DONE = 368, 341, 342
KEY_PRIEST_ASKED, KEY_PRIEST_READY, KEY_PRIEST_GONE = 253, 254, 255
BELL_ABC = ROOT / "mm9/extracted/MODELS/MODELS/PROPS/BELL.abc"   # the bells' model (props.json source_model)
BELL_WAIT = 3                       # LindisfarneBell.scr: OnUse's Wait 1, 3 and RingDone's Wait 1,3,StopDone (slot 1)
FINALE_WAITS = [0.5, 0.5, 0.25, 0.25]   # LindisfarneBellController.scr :Finish, :1, :2, :3 (wait 1 .5 / .25)
BELL_SOUNDS = {"Bell1": "churchbellring.wav", "Bell2": "churchbellring2.wav", "Bell3": "churchbellring3.wav",
               "Bell4": "churchbellring4.wav", "Bell5": "churchbellring5.wav"}  # LindisfarneBell.scr :BellSound
NPC_SCRIPTS = {"npc282.scr": 282, "npc283.scr": 283, "npc284.scr": 284, "npc420.scr": 420}
# MM9's bodies: the ABC's first AnimBinding extents (half sizes, LT) x Scale 1 (MONSTERS.txt) x 2.56
BODIES = {"models\\monk.abc": (11, 36), "models\\peasantmale.abc": (12, 34)}
THJORAD_MARKERS = {"ThjoradMonk1": "Thjorad3", "ThjoradMonk2": "Thjorad2", "ThjoradMonk3": "Thjorad1",
                   "ThjoradMonk4": "Thjorad0"}                             # ThjoradMonk.scr ScriptParams p1
# The clip a monk loops whenever it stands (scene mm9_ai.idle_clip), never fidgeting: MM9's LoopAnim holds its animator
# in the script state, whose think has no fidget (devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md section 2.1).
# MonkGuardBasic.scr by its type p0: the prayer (0) waits between walks in a looped stand (BaseWanderStart:
# LoopAnim sPauseName), the hoe (1) and broom (2) monks hoe and sweep at each stop (BaseWanderStopTick), the hammer (3)
# and wash (4) monks stay at their work (StartWork); a chatting monk (-1) loops nothing and fidgets. ThjoradMonk.scr
# loops its p0 (Pray, Hammer) and, after the bells (GoToPray), prays.
MONK_IDLE_CLIPS = {0: "standing", 1: "hoe", 2: "sweep", 3: "hammer", 4: "wash"}
# The tool MonkGuardBasic.scr :AttachTool gives a working monk (AttachProp <model> on its socket; scene held_items).
# ThjoradMonk.scr attaches a hammer only to a monk without an NPC id, and all four have one.
MONK_TOOLS = {1: ("mm9_item_monkhoe", "Hoe"), 2: ("mm9_item_monkbroom", "Broom"),
              3: ("mm9_item_monkhammer", "Hammer"), 4: ("mm9_item_monkcloth", "Cloth")}


def bell_schedule() -> list[tuple[float, str]]:
    """A bell's use (LindisfarneBell.scr) as (seconds from the use, what): PlayAnim Ring, its model keys BellBing and
    BellBong (OnBellBing, OnBellBong: the note), at its end (RingDone) PlayAnim Stop, whose keys play the note again,
    and Wait 1,3,StopDone from Ring's end. Key times from the ABC's clips."""
    sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
    from convert_abc_model import read_abc
    clips = {a.name.lower(): a for a in read_abc(BELL_ABC).animations}

    def keys(clip: str, start: float) -> list[tuple[float, str]]:
        return [(start + k.time_ms / 1000, "note") for k in clips[clip].keyframes
                if k.event.lower() in ("bellbing", "bellbong")]

    ring = clips["ring"].keyframes[-1].time_ms / 1000
    out = [*keys("ring", 0.0), (ring, "stop"), *keys("stop", ring), (ring + BELL_WAIT, "done")]
    if not keys("ring", 0.0) or ring + clips["stop"].keyframes[-1].time_ms / 1000 > ring + BELL_WAIT:
        raise SystemExit(f"{BELL_ABC}: no bell keys in Ring, or Stop outlasts StopDone")
    return out


def rude_exit_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a dialogue with actor object `index` runs when it closes."""
    return 50000 + index


def rude_use_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a click on dialogue actor object `index` runs instead of opening it."""
    return 53000 + index


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


class LindisfarneMonastery(dungeon.Hooks):
    generator = "mm9r_lindisfarnemonastery"
    mover_events = {**{name: (event, "click") for name, event in EV_ROPE.items()},
                    **{"Organ" + note.replace("#", "s"): (event, "click") for note, event in EV_KEY.items()}}

    # --- geometry -------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        for polygon in polygons:
            if "skymarker" in polygon.texture.lower():
                # MM9's sky box (SnowMtns) round the courtyard and the hillside: sky04 stretched, one tile about
                # 2 500 LT wide (Verhoffin Ruins, Tasar Academy); ceilings across x and z, walls along and down
                origin = np.asarray(polygon.mapping[0], float)
                n = polygon.normal
                if abs(n[1]) > 0.7:
                    u, v = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
                else:
                    u = np.cross([0.0, 1.0, 0.0], n)
                    u /= np.linalg.norm(u)
                    v = np.array([0.0, -1.0, 0.0])
                polygon.mapping = (origin, u * SKY_TEXELS_PER_LT, v * SKY_TEXELS_PER_LT)
        return polygons

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content = build.content
        if PROPS.exists():
            events = {"thjorad": EV_THJORAD, **EV_LETTER, **EV_BELL}
            cogs = {"thjorad": COG_THJORAD, **{f"Bell{n}": COG_BELL + n for n in range(1, 6)}}
            content.props(PROPS, events=events, cogs=cogs)
        else:
            print("note: props.json is missing; no decorations placed")
        report = content.report["omitted"]
        report.append({"anchor": "BellControl", "class": "ScriptObject",
                       "reason": "LindisfarneBellController.scr: the bell order in the map Lua (README)"})
        report.append({"anchor": "MONK_HOSTILITY", "class": "ScriptObject",
                       "reason": "MonkHostility.inc's link object: the map variable MonksHostile (README)"})
        self.points = {}
        for name in (*THJORAD_MARKERS.values(), "E2"):
            p = build.source.properties(name)["Pos"]
            floor = content.floor_at(p[0], p[2], p[1] + 24)
            self.points[name] = build.project.native([p[0], floor, p[2]]).round().astype(int) + np.array([0, 0, 1])
        self.detail_faces(build)

    def detail_faces(self, build) -> None:
        """The BLV keeps at most 7 000 outlines (the 875-byte seen-lines bitset): every edge of an up-facing face counts.
        The hillside in front of the monastery (Terrain0, 1 531 polygons the party never walks: InvisibleBrush5 and the
        exit volume keep it in the porch) would take most of them. Its up-facing faces go to a TRIGGER_detail node
        compiled with the invisible flag, which the outline pass skips; scene() gives them their drawn attributes back
        at load (the Chasm of the Dead's route). Nothing outside appears on the minimap."""
        package = build.package
        self.detail_rings = []
        for node in [n for n in package.nodes if n.startswith("ROOM_")]:
            keep, detail = [], []
            for entry in package.nodes[node]:
                p = np.asarray(entry[0], float)
                n = np.cross(p[1] - p[0], p[2] - p[0]).astype(float)
                nz = n[2] / max(np.linalg.norm(n), 1e-9)
                outside = p[:, 1].mean() < OUTSIDE_Z_LT * SCALE
                (detail if nz > 0.05 and outside else keep).append(entry)
            if not detail:
                continue
            package.nodes[node] = keep
            target = f"TRIGGER_detail_{node[5:]}"
            package.nodes[target].extend(detail)
            self.detail_rings += [entry[0] for entry in detail]
            package.room_nodes[f"room_{node[5:]}"].append(target)
            package.metadata["surfaces"].append({"id": target, "source_node": target, "flags": ["invisible"]})
        build.stats["detail_faces_outside"] = len(self.detail_rings)

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor, self.object, self.rude, self.idle_clip = [], {}, {}, {}, {}
        self.robert = None
        for o in source.objects:
            if o["name"] not in bases:
                continue
            name, p = o["name"], o["properties"]
            script = str(p.get("ScriptName") or "").lower().replace("scripts\\", "")
            params = str(p.get("ScriptParams") or "").split()
            rude, immobile, group, hidden, idle_clip, tool = 0, False, GROUP_MONKS, False, "", None
            if script == "monkguardbasic.scr":       # p0 type (-1 chat, 0 pray, 1 hoe, 2 broom, 3 hammer, 4 wash), p1 rude
                rude = int(params[1])
                immobile = int(params[0]) in (-1, 3, 4)      # only types 0-2 wander (BaseWanderInit)
                idle_clip = MONK_IDLE_CLIPS.get(int(params[0]), "")
                tool = MONK_TOOLS.get(int(params[0]))
            elif script == "thjoradmonk.scr":        # p0 animation, p1 prayer marker, p2 rude id
                rude, immobile, group = int(params[2]), True, GROUP_THJORAD
                idle_clip = params[0].lower()
            elif script in NPC_SCRIPTS:
                rude, immobile = NPC_SCRIPTS[script], True
                if script == "npc284.scr":           # Robert Aefgil: hidden and not solid until key 254
                    group, hidden = GROUP_ROBERT, True
            half, tall = BODIES[str(p.get("Filename", "")).lower()]
            scale = float(p.get("Scale", 1.0) or 1.0)
            actor = content.actor(o, bases[name], sector_of_room, group=group, hidden=hidden, friendly=True,
                                  floor_query_lt=p["Pos"][1] + 24,
                                  radius=int(round(half * scale * SCALE)), height=int(round(2 * tall * scale * SCALE)))
            actor["mm9_source_object_index"] = o["index"]
            if idle_clip:
                actor["mm9_ai"]["idle_clip"] = idle_clip
            self.idle_clip[name] = idle_clip
            if tool:
                actor["held_items"] = [{"model": f"worlds/mm9/models/{tool[0]}.glb", "node": f"Socket_{tool[1]}"}]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = immobile
            self.actor[name], self.object[name], self.rude[name] = actor["actor_index"], o["index"], rude
            if group == GROUP_ROBERT:
                self.robert = name
            out.append(actor)
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Lindisfarne Monastery")
        script.doors()
        script.chests()
        actor, objects = self.actor, self.object
        monks = sorted(actor[name] for name in actor if name != self.robert)
        lines = [
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            "local function questSound() MM9.playSound(\"events/quest.wav\") end   -- MM9 quest.wav: the shared quest sound",
            "",
            "-- The monks' hostility (MonkHostility.inc, MONK_HOSTILITY): every monk is the party's friend (AddFriend Player)",
            "-- until the party hurts or kills one (_OnDamage, _OnDeath: TurnHostilityOn). Then alarmbell.wav rings, the link",
            "-- object is removed and every monk becomes hostile (BecomeHostile: AddEnemy Player, no more talk: BlockRude);",
            "-- Thjorad turns on (Thjorad.scr OnObjectLinkBroken). Robert Aefgil (NPC284.scr) has no MonkHostility.",
            f"local MONKS = {{{', '.join(f'[{a}] = true' for a in monks)}}}",
            "local function hostile() return var(\"MonksHostile\") == 1 end",
            "local function applyHostility()",
            "    local on = hostile()",
            f"    evt.SetMonGroupBit({GROUP_MONKS}, MonsterBits.Hostile, on)",
            f"    evt.SetMonGroupBit({GROUP_THJORAD}, MonsterBits.Hostile, on)",
            "    -- BecomeHostile's AddEnemy Player: MM9's monster AI walks the monks at the party, the ones placed still at",
            "    -- their chores and prayers too; the Thjorad monks' prayer after the bells ends (ThjoradMonk.scr OnDamage:",
            "    -- Playanim stand)",
            "    if on then for i in pairs(MONKS) do evt.SetActorImmobile(i, false) evt.ClearActorPresentation(i) end end",
            "end",
            "local function alarm()",
            "    if hostile() then return end",
            "    set(\"MonksHostile\", 1)",
            "    evt.PlaySoundName(\"events/alarmbell.wav\", 0, 0, 0)",
            "    applyHostility()",
            "end",
            f"handlers[{DAMAGE_HOOK}] = function(context) if context.actorIndex ~= nil and MONKS[context.actorIndex] then alarm() end end",
            f"handlers[{KILL_HOOK}] = function(context) if context.actorIndex ~= nil and MONKS[context.actorIndex] then alarm() end end",
            "",
            "-- A click on a monk opens its dialogue (MonkGuardBasic.scr ScriptParams p1, ThjoradMonk.scr p2) unless the monks",
            "-- are hostile (BlockRude); the Thjorad monks talk only while they guard Thjorad (OnUse: AtPrayer 0), the organ",
            "-- player not while he plays (NPC420.scr OnUse: bIsPlaying).",
        ]
        registrations = [(DAMAGE_HOOK, "Monks hurt", None), (KILL_HOOK, "Monks killed", None)]
        for name in sorted(actor, key=lambda n: actor[n]):
            if name == self.robert or not self.rude[name]:
                continue
            condition = "hostile()"
            if name in THJORAD_MARKERS:
                condition += " or var(\"AtPrayer\") == 1"
            if self.rude[name] == 420:
                condition += " or var(\"OrganPlaying\") == 1"
            event = rude_use_event(objects[name])
            lines.append(f"handlers[{event}] = function() if {condition} then return end MM9.openRude({self.rude[name]}) end"
                         f"   -- {name}")
            registrations.append((event, name, None))
        letter_title, letter_text = letter(473)
        lines += [
            "",
            "-- Thjorad (Thjorad.scr :OnUse): only once it is on (the bells rung, key 9507, or the monks hostile). With key 2",
            f"-- (the quest) and no key {KEY_THJORAD_A}: key {KEY_THJORAD_A}; else, without key {KEY_THJORAD_B}: key "
            f"{KEY_THJORAD_B}; either way item {ITEM_THJORAD} and 1000 experience, and the hammer is gone.",
            "local function thjoradOn() return hostile() or MM9.hasKey(" + str(KEY_BELLS) + ") == 1 end",
            "local function thjoradTaken() return MM9.hasKey(" + str(KEY_THJORAD_A) + ") == 1 or MM9.hasKey("
            + str(KEY_THJORAD_B) + ") == 1 end",
            f"handlers[{EV_THJORAD}] = function()",
            "    if not thjoradOn() or var(\"ThjoradTaken\") == 1 then return end",
            f"    if MM9.hasKey({KEY_THJORAD_QUEST}) == 1 and MM9.hasKey({KEY_THJORAD_A}) == 0 then",
            f"        MM9.giveKey({KEY_THJORAD_A})",
            "        questSound()",
            f"    elseif MM9.hasKey({KEY_THJORAD_B}) == 0 then",
            f"        MM9.giveKey({KEY_THJORAD_B})",
            "    else",
            "        return",
            "    end",
            f"    give({ITEM_THJORAD}, \"Thjorad.scr:Onuse\")",
            f"    {experience_lua(1000)}",
            "    set(\"ThjoradTaken\", 1)",
            f"    evt.SetSprite({COG_THJORAD}, false)",
            "end",
            "",
            "-- The bells (LindisfarneBell.scr; ScriptParams p2 picks the note): a pull on a rope (the rope Door's OpenTrigger0",
            "-- 'use') or a click on the bell uses it. :OnUse (only while Counter is 0: BellBusy<n>) plays Ring; its model keys",
            "-- BellBing and BellBong play the note; at its end (RingDone) Stop plays, whose keys play the note again, and",
            f"-- Wait 1,{BELL_WAIT},StopDone: Counter 0 and, until key {KEY_BELLS}, Trigger BellControl Bell<n>. Each step "
            "below is",
            "-- (seconds from the use, what), the key times read from BELL.abc. The bell part and its clapper swing with the clips.",
            "-- LindisfarneBellController.scr: :OnBell1 sets FirstBell; :OnBell<n> sets the next flag if the one before is set,",
            "-- else :Reset clears all five; Bell5 after Bell4 runs :Finish.",
            "local BELL_SOUND = {" + ", ".join(f"[{n}] = \"events/{BELL_SOUNDS[f'Bell{n}']}\"" for n in range(1, 6)) + "}",
            "local BELL_STEPS = {" + ", ".join(f"{{{t:.3f}, \"{what}\"}}" for t, what in bell_schedule()) + "}",
            "local BELL_ORDER = {\"FirstBell\", \"SecondBell\", \"ThirdBell\", \"FourthBell\", \"FifthBell\"}",
            "-- the Finish's peal: its waits before Bell2..Bell5 (wait 1 .5, 1 .5, 1 .25, 1 .25)",
            "local FINALE_WAITS = {" + ", ".join(f"[{n + 2}] = {w}" for n, w in enumerate(FINALE_WAITS)) + "}",
            "local useBell, peal",
            "local function finish()",
            f"    if MM9.hasKey({KEY_BELLS}) == 0 then MM9.giveExperience({balanced_experience(2000, KEY_BELLS)}) end",
            f"    MM9.giveKey({KEY_BELLS})",
            "    set(\"AtPrayer\", 1)",
            "    praying()",
            "    set(\"FinaleStep\", 1)",
            "    peal()",
            "end",
            "local function control(n)   -- BellControl :OnBell<n>",
            "    if n == 1 then set(BELL_ORDER[1], 1) return end",
            "    if var(BELL_ORDER[n - 1]) ~= 1 then",
            "        for k = 1, 5 do set(BELL_ORDER[k], 0) end   -- :Reset",
            "        return",
            "    end",
            "    set(BELL_ORDER[n], 1)",
            "    if n == 5 then finish() end",
            "end",
            "useBell = function(n)   -- :OnUse",
            "    if var(\"BellBusy\" .. n) ~= 0 then return end",
            "    set(\"BellBusy\" .. n, 1)",
            f"    evt.PlayDecorationClip({COG_BELL} + n, \"ring\")",
            f"    evt.StartTimer({T_BELL} + n, seconds(BELL_STEPS[1][1]))",
            "end",
            "local function swing(n)   -- the bell's timer: step BellBusy<n> of BELL_STEPS",
            "    local step = var(\"BellBusy\" .. n)",
            "    local at = BELL_STEPS[step]",
            "    if at == nil then",
            f"        evt.StopTimer({T_BELL} + n)",
            "        return",
            "    end",
            "    if at[2] == \"note\" then",
            "        evt.PlaySoundName(BELL_SOUND[n], 0, 0, 0)",
            "    elseif at[2] == \"stop\" then",
            f"        evt.PlayDecorationClip({COG_BELL} + n, \"stop\")",
            "    else   -- :StopDone (Stop has ended: back to rest)",
            "        set(\"BellBusy\" .. n, 0)",
            f"        evt.StopTimer({T_BELL} + n)",
            f"        evt.PlayDecorationClip({COG_BELL} + n, \"\")",
            f"        if MM9.hasKey({KEY_BELLS}) == 0 then control(n) end",
            "        return",
            "    end",
            "    set(\"BellBusy\" .. n, step + 1)",
            f"    evt.StartTimer({T_BELL} + n, seconds(BELL_STEPS[step + 1][1] - at[1]))",
            "end",
            "-- :Finish uses Bell1 to Bell5 again (Trigger use: a bell still swinging ignores it), FINALE_WAITS apart.",
            "peal = function()",
            "    local step = var(\"FinaleStep\")",
            "    if step < 1 or step > 5 then",
            f"        evt.StopTimer({T_FINALE})",
            "        return",
            "    end",
            "    useBell(step)",
            "    set(\"FinaleStep\", step + 1)",
            f"    if step < 5 then evt.StartTimer({T_FINALE}, seconds(FINALE_WAITS[step + 1])) else evt.StopTimer({T_FINALE}) end",
            "end",
            f"handlers[{T_FINALE}] = function() peal() end",
        ]
        # the Thjorad monks walk to their prayer markers (ThjoradMonk.scr :OnGoToPray: WalkTo L_Marker)
        # A slain monk takes no GoToPray (MM9.receives) and, on a load, stays where it fell (MM9.actorAlive)
        moves = [f"    if atLoad and MM9.actorAlive({actor[name]}) or not atLoad and MM9.receives("
                 f"\"lindisfarnemonastery\", \"{name}\", \"GoToPray\", {actor[name]}) then evt.SetMapActorPosition({actor[name]}, "
                 f"{', '.join(str(int(v)) for v in self.points[marker])}) end"
                 for name, marker in THJORAD_MARKERS.items()]
        # ... and pray there (OnGoToPray: set Anim_1 Pray), the hammering one too, until the monks turn hostile
        moves += [f"    if MM9.actorAlive({actor[name]}) and not hostile() then evt.PlayActorClip({actor[name]}, \"pray\", true) end"
                  for name in THJORAD_MARKERS if self.idle_clip[name] != "pray"]
        lines[lines.index("local function finish()"):lines.index("local function finish()")] = [
            "local function praying(atLoad)   -- ThjoradMonk.scr :OnGoToPray (MM9 walks them; here they stand at the "
            "markers)",
            *moves, "end"]
        for n in range(1, 6):
            lines.append(f"handlers[{EV_BELL[f'Bell{n}']}] = function() useBell({n}) end   -- Bell{n}")
            lines.append(f"handlers[{T_BELL + n}] = function() swing({n}) end   -- Bell{n} swings")
            registrations += [(EV_BELL[f"Bell{n}"], "Bell", "Bell"), (T_BELL + n, f"Bell{n} swing", None, "timer")]
        lines.append("-- The ropes: each pull lowers the rope (Door, 32 LT down; it rises again) and rings its bell.")
        for rope, bell in ROPES.items():
            lines.append(f"handlers[{EV_ROPE[rope]}] = function() press(DOORS.{rope}, 2) useBell({bell[4:]}) end   -- {rope}")
            registrations.append((EV_ROPE[rope], "Rope", "Rope"))
        press = [
            "-- Pressed movers (the organ keys, the ropes) rise again a second (a rope two: 32 LT at 25 LT/s) after the last",
            "-- press (MM9's Door closes after its wait).",
            "local PRESSED = {}",
            "local function press(door, hold)",
            "    evt.SetDoorState(door, DoorAction.Open)",
            "    PRESSED[door] = true",
            "    set(\"ReleaseArmed\", 1)",
            f"    evt.StartTimer({T_RELEASE}, seconds(hold or 1))",
            "end",
            f"handlers[{T_RELEASE}] = function()",
            "    if var(\"ReleaseArmed\") ~= 1 then return end",
            "    set(\"ReleaseArmed\", 0)",
            "    for door in pairs(PRESSED) do evt.SetDoorState(door, DoorAction.Close) end",
            "    PRESSED = {}",
            "end",
            "",
        ]
        lines += [
            "",
            "-- The organ's 25 keys (Door, MoveDir down, MoveDist 2 LT, OpenStartSound Sounds\\Music\\<note>.wav).",
        ]
        for note, event in EV_KEY.items():
            sound = note.lower()
            if note in ("D#1", "D#2"):
                sound = {"D#1": "d#2", "D#2": "d#1"}[note]    # MM9 swaps these two keys' sounds (D#2 plays d#1.wav)
            lines.append(f"handlers[{event}] = function() press(DOORS.Organ{note.replace('#', 's')}) "
                         f"evt.PlaySoundName(\"music/{sound}.wav\", 0, 0, 0) end   -- {note}")
            registrations.append((event, "Organ key", "Organ"))
        organist, grehgknak, abbot = objects["CommonerElfMaleA0"], objects["Grehgknak"], objects["Abbot Leffery"]
        robert = actor[self.robert]
        # every eligible member (MM9.promoteParty), not MM9's per-character keys (PALADIN_KEYS)
        promote = "        MM9.promoteParty(\"Paladin\")"
        lines += [
            "",
            f"-- The organ player (NPC420.scr :OnRude, :PlaySong, :Play): with key {KEY_HYMN} from his dialogue he turns to the",
            f"-- organ (FaceObject E2, 180 degrees a second) and plays the hymn (LoopAnim play, HeroesPipe441.wav, "
            f"{HYMN_SECONDS} s), the key taken;",
            "-- while he plays he does not talk (OnUse: bIsPlaying).",
            f"handlers[{rude_exit_event(organist)}] = function()",
            f"    if MM9.hasKey({KEY_HYMN}) == 0 then return end",
            f"    MM9.takeKey({KEY_HYMN})",
            "    evt.PlaySoundName(\"events/heroespipe441.wav\", 0, 0, 0)",
            f"    evt.FaceActorTo({actor['CommonerElfMaleA0']}, {int(self.points['E2'][0])}, {int(self.points['E2'][1])}, 1)",
            f"    evt.PlayActorClip({actor['CommonerElfMaleA0']}, \"play\", true)",
            "    set(\"OrganPlaying\", 1)",
            f"    evt.StartTimer({T_ORGAN}, seconds({HYMN_SECONDS}))",
            "end",
            f"handlers[{T_ORGAN}] = function()   -- :OnExit",
            f"    evt.StopTimer({T_ORGAN})",
            "    if var(\"OrganPlaying\") ~= 1 then return end",
            f"    evt.ClearActorPresentation({actor['CommonerElfMaleA0']})",
            "    set(\"OrganPlaying\", 0)",
            "end",
            "",
            f"-- Grehgknak the Right (NPC282.scr :OnRude): :giveletter (key {KEY_LETTER_ASKED} without {KEY_LETTER_GIVEN}: key "
            f"{KEY_LETTER_GIVEN}, item {ITEM_LETTER}); :paladins",
            f"-- (key {KEY_PALADIN_ASKED} without {KEY_PALADIN_DONE}: 63000 experience, :PromotePaladin for each character "
            f"holding key 421-424, 5000 gold, key {KEY_PALADIN_DONE}).",
            f"handlers[{rude_exit_event(grehgknak)}] = function()",
            f"    if MM9.hasKey({KEY_LETTER_GIVEN}) == 0 and MM9.hasKey({KEY_LETTER_ASKED}) == 1 then",
            f"        MM9.giveKey({KEY_LETTER_GIVEN})",
            f"        give({ITEM_LETTER}, \"NPC282.scr:giveletter\")",
            "        return",
            "    end",
            f"    if MM9.hasKey({KEY_PALADIN_DONE}) == 0 and MM9.hasKey({KEY_PALADIN_ASKED}) == 1 then",
            f"        {experience_lua(63000, KEY_PALADIN_DONE)}",
            "        questSound()",
            promote,
            "        MM9.giveGold(5000)",
            f"        MM9.giveKey({KEY_PALADIN_DONE})",
            "    end",
            "end",
            "",
            f"-- Abbot Leffery (NPC283.scr :OnRude :MissingRelic): key {KEY_RELIC_FOUND} without {KEY_RELIC_DONE}: item "
            f"{ITEM_RELIC} taken, 3000 gold, 80000 experience, key {KEY_RELIC_DONE}.",
            f"handlers[{rude_exit_event(abbot)}] = function()",
            f"    if MM9.hasKey({KEY_RELIC_DONE}) == 0 and MM9.hasKey({KEY_RELIC_FOUND}) == 1 then",
            f"        MM9.takeItem({ITEM_RELIC}, \"NPC283.scr:MissingRelic\")",
            "        MM9.giveGold(3000)",
            f"        {experience_lua(80000, KEY_RELIC_DONE)}",
            "        questSound()",
            f"        MM9.giveKey({KEY_RELIC_DONE})",
            "    end",
            f"    if MM9.hasKey({KEY_PRIEST_ASKED}) == 1 and var(\"PriestAskedAt\") == 0 then",
            "        set(\"PriestAskedAt\", evt.CurrentGameMinutes() + 1)",
            "    end",
            "end",
            "",
            f"-- Robert Aefgil (NPC284.scr): hidden and not solid without key {KEY_PRIEST_READY}, gone with "
            f"{KEY_PRIEST_GONE} (he left with",
            "-- the party). NPC283.scr's '@M 5 : 00 Givekey': the first 5:00 after the abbot agreed (key "
            f"{KEY_PRIEST_ASKED}) gives key {KEY_PRIEST_READY}",
            "-- and Robert appears (NPC284.scr :Appear, also '@M 6 : 00').",
            "local function robert()",
            f"    local shown = MM9.hasKey({KEY_PRIEST_READY}) == 1 and MM9.hasKey({KEY_PRIEST_GONE}) == 0",
            f"    evt.SetMonGroupBit({GROUP_ROBERT}, MonsterBits.Invisible, not shown)",
            "end",
            f"handlers[{T_CLOCK}] = function()",
            f"    if MM9.hasKey({KEY_PRIEST_ASKED}) == 1 and MM9.hasKey({KEY_PRIEST_READY}) == 0 "
            f"and MM9.hasKey({KEY_PRIEST_GONE}) == 0 then",
            "        local asked = var(\"PriestAskedAt\")",
            "        if asked == 0 then asked = evt.CurrentGameMinutes() set(\"PriestAskedAt\", asked) end",
            "        local five = math.floor((asked - 1) / 1440) * 1440 + 300",
            "        if five < asked - 1 then five = five + 1440 end",
            f"        if evt.CurrentGameMinutes() >= five then MM9.giveKey({KEY_PRIEST_READY}) end",
            "    end",
            "    robert()",
            "end",
            "",
        ]
        registrations += [(rude_exit_event(organist), "Organ player", None),
                          (rude_exit_event(grehgknak), "Grehgknak", None),
                          (rude_exit_event(abbot), "Abbot Leffery", None),
                          (EV_THJORAD, "Thjorad", "Thjorad"), (T_FINALE, "Bell peal", None, "timer"),
                          (T_RELEASE, "Release", None, "timer"), (T_CLOCK, "Robert", None, "timer"),
                          (T_ORGAN, "Hymn", None, "timer")]
        for name, event in EV_LETTER.items():
            title, text = letter(LETTER_ID[name])
            lines.append(f"handlers[{event}] = function() evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) "
                         f"end   -- {name}: BookLetter.scr \"{LETTER_ID[name]} Letter\"")
            registrations.append((event, "Letter", "Letter"))
        lines += [
            "",
            "-- Map load (Thjorad.scr :Init, ThjoradMonk.scr :Init, NPC284.scr :Init, MonkHostility.inc).",
            "handlers[1] = function()",
            "    applyHostility()",
            "    if thjoradTaken() then set(\"ThjoradTaken\", 1) end",
            f"    if var(\"ThjoradTaken\") == 1 then evt.SetSprite({COG_THJORAD}, false) end",
            f"    if MM9.hasKey({KEY_BELLS}) == 1 then set(\"AtPrayer\", 1) praying(true) end",
            "    robert()",
            "    set(\"OrganPlaying\", 0)   -- a hymn a save cut short is over",
            "    for n = 1, 5 do set(\"BellBusy\" .. n, 0) end   -- so is a bell's swing (its report to BellControl too)",
            "end",
            "",
        ]
        registrations.append((1, "Map load", None))
        script.add(press + lines, *registrations)
        script.hooks += [f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Monks hurt", handlers[{DAMAGE_HOOK}])',
                         f'RegisterMonsterKilledHook({KILL_HOOK}, "Monks killed", handlers[{KILL_HOOK}])']
        script.registrations = [r for r in script.registrations if r[0] not in (DAMAGE_HOOK, KILL_HOOK)]
        self.robert_actor = robert
        return script.finish(on_load=[1])

    def scene(self, build, scene: dict) -> None:
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], np.int64)

        def key(points) -> tuple:
            return tuple(sorted(tuple(int(round(c)) for c in p) for p in points))

        ids = {}
        for f in blv["faces"]:
            ids.setdefault(key(vertices[f["vertex_indices"]]), []).append(f)
        details = [f for ring in self.detail_rings for f in ids.get(key(ring), [])]
        scene["initial_state"].setdefault("face_attribute_overrides", []).extend(
            {"face_index": f["index"], "legacy_attributes": int(f["attributes"]) & ~INVISIBLE_FACE} for f in details)
        build.stats["detail_faces_restored"] = len(details)

    def report(self, build) -> dict:
        return {"scripted": {"actors": self.actor, "objects": self.object, "rude": self.rude, "robert": self.robert}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, LindisfarneMonastery()))
