#!/usr/bin/env python3
"""
Drangheim Prison, MM9 rework: MM9's DRANGHEIMPRISON.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_drangheimprison/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_drangheimprison/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules and archway cuts; this file adds the prison's population (props.json from
../../props/mm9_drangheimprison_claude, the sink's water, the trigger pads, 81 actors) and its scripted objects as
native Lua, each citing its .scr (README.md, "Scripted objects"):
- the visitor's pass and the alarm (GuardRude.scr, AlarmControl.scr, DrangheimHostility.inc, Guardhelp.scr,
  GuardToNegate.scr): keys 5007 (pass) and 5006 (hostile);
- the cook and his brother (NPC419.scr, NPC427.scr): keys 5004, 5005, 369, 370;
- Ivsar Forktooth (NPC90.scr): keys 17, 21, 194, 242;
- the prisoners (DrangheimPrisoner.scr) and the interrogation (DrangheimInterrogator.scr, DrangheimWarden.scr,
  DrangheimDoorman.scr);
- the cell levers (door object wiring), the well's lid, the smith (DrangheimSmith.scr).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
import review_root  # noqa: E402
from dungeon import lua, tables  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"
SINK_MODEL = "SinkWater0"
SINK_TEXTURE = "water:pool"         # overrides.yml textures: MM9's Water115.spr, first frame
DESCRIPTORS = ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt"
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/drangheimprison.scene.yml"

# MM9's PerceptionBrushes: the red glow on the secret doors and panels, seen by a party whose Perception reaches the
# PerceptionValue (12 on all six brushes here).
PERCEPTION_TEXTURE = "sprites\\perception.spr"
PERCEPTION_COG = 300                # brush k's faces: cog PERCEPTION_COG + k
PERCEPTION_SKILL = 29               # evt.CheckSkill's id: the party's best Perception value (mastery counted)
PERCEPTION_OPACITY = 0.35           # the brushes' Alpha (times the texture's own)
WATER_TEXTURE = "sprites\\water\\ocean4.spr"       # the quenching trough, WorldObject0
FRAME_FLAGS = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}

# The Nagate's body is MM9's (dungeon/bodies.py): nagate.abc's half extents (18, 10) LT times MONSTERS.txt Scale
# (Hatchling 1, Nagate 1.5, Elder 3), now carried by the rows 9081-9083, or times the DAT's own Scale (0.75-1.1 on
# eleven of them), which replaces the row's. The spider stand-in's 109 x 64 did not fit the 253 wide lane out of the
# hatchlings' room (README, "Can the monsters reach the party").

# --- Events, timers, groups ------------------------------------------------------------------------------------------
# DAT lever -> the cell door it unlocks and opens (OpenTrigger/CloseTrigger wiring of the lever objects).
LEVERS = {"lever0": "Celldoor1", "lever1": "Celldoor2", "lever2": "Celldoor3", "lever3": "Celldoor4",
          "lever4": "Celldoor5", "lever5": "Celldoor6", "lever6": "Celldoor8", "lever7": "Celldoor9",
          "lever8": "Celldoor11", "lever9": "Celldoor12", "lever10": "Celldoor10", "lever11": "Celldoor7",
          "lever12": "Celldoor17", "lever15": "Celldoor13", "lever17": "Celldoor18", "lever24": "Celldoor25",
          "lever25": "Celldoor26", "lever26": "Celldoor27", "lever27": "Celldoor28", "lever28": "Celldoor30",
          "blever0": "Celldoor14", "blever1": "Celldoor16", "blever2": "Celldoor15"}
EV_LEVER = {name: 200 + k for k, name in enumerate(LEVERS)}
EV_LOCKED, EV_COOK_CAGE, EV_GRATE, EV_INTERR_DOOR = 230, 231, 232, 233
EV_WELL_LID, EV_HATCH = 240, 241
EV_BEATINGS = {"TriggerBeatings0": 250, "TriggerBeatings1": 251}
EV_BARRACKS = 252                   # NagGuardTrigger0
EV_INTERR_ARRIVE, EV_PRISONER_ARRIVE = 254, 255                 # the interrogation's evt.MoveActorTo arrivals
T_BEATING, T_SMITH, T_HINTS, T_SMITH_ITEM = 260, 261, 262, 263
DAMAGE_HOOK, KILL_HOOK = 96, 97
# Cells MM9 locks with no lever (Locked, no key, no trigger).
SEALED_CELLS = ["Celldoor32", "Celldoor33", "Celldoor34", "Celldoor36", "Celldoor38"]

GROUP_GUARDS, GROUP_FRONT, GROUP_HELP, GROUP_BARRACKS, GROUP_SMITH = 1, 2, 3, 4, 5
GROUP_WARDEN, GROUP_DOORMAN, GROUP_INTERROGATOR, GROUP_CIVILIANS = 6, 7, 8, 9
GUARD_MONSTERS = (9111, 9112, 9113)   # DrangheimHostility.inc's guards (the smith, 9120, runs no hostility script)
NAGATE_MONSTERS = (9081, 9082, 9083)
RELATION_SHORT = 2                  # hostile, the "short" engagement range (GuardToNegate.scr: AddEnemy Nagate)
# DrangheimSmith.scr's round (LT): ten blows at the anvil 3 s apart, then 5 s at the anvil, the sword cooled 5 s at
# MarkerWater (WalkTo 40), put on the WeaponRack (WalkTo 5) and back to MarkerAnvil (WalkTo 10).
SMITH_STOPS = (("MarkerAnvil", 25.0, [30.0, 35.0], "attack_melee"), ("MarkerWater", 40.0, [5.0, 5.0], None),
               ("WeaponRack", 40.0, [1.0, 2.0], None))
# DrangheimSmith.scr :AttachHammer / :AttachSword (AttachProp hammer.abc / kirasword.abc on rhand1): the hammer at the
# anvil and on the way back to it, the sword from :CoolWeapon (leaving the anvil) until :OnReturnedWeapon at the rack.
SMITH_HAMMER = {"model": "worlds/mm9/models/mm9_item_hammer.glb", "node": "Socket_RHand1"}
SMITH_SWORD = {"model": "worlds/mm9/models/mm9_item_kirasword.glb", "node": "Socket_RHand1"}
# The interrogation's timing (DrangheimInterrogator.scr: CELL_OPEN_TIME and DOOR_OPEN_TIME are the doors' open times
# + 1 s; BeatdownMix8bit.wav plays about 8 s) and a prisoner's stop short of the interrogator (native units).
CELL_WAIT, DOOR_WAIT, BEAT_SECONDS, LEG_TIMEOUT, PICK_OFFSET = 3, 4, 8, 25, 110
GUARD_SLEEP_ODDS = 20               # GuardRude.scr :StartWork: GetRandomInt 1, 20 == 1 -> LoopAnim sleep

KEY_ON_MISSION, KEY_SENT_BY_BJARNI, KEY_MET_OUTSIDE, KEY_GOT_OUT = 12, 17, 194, 242
KEY_IVSAR_HOME = 21
KEY_DEAL, KEY_COOK_DONE, KEY_HOSTILE, KEY_PASS = 5004, 5005, 5006, 5007
KEY_BROTHER_FREED, KEY_BROTHER_REWARD = 369, 370
ITEM_PASS = 446
BROTHER_EXPERIENCE, RESCUE_EXPERIENCE = 4000, 500

RUDE_OBJECTS = {"Guard0": 425, "Guard1": 425, "Guard2": 426}     # GuardRude.scr: ScriptParams p0 is the dialogue
# NPC bodies by the object's MM9 model: the old import gave the prisoners and Ivsar row 366 (Peasant Human1 MaleC),
# whose sprite the indoor pick does not hit; Ivsar is MM9's CommonerHumanMaleA like Antoni, the prisoners PeasantMale.
BODY_ROWS = {"models\\commonerhumanmalea.abc": 358, "models\\peasantmale.abc": 367}
ANIMAL_ROWS = {"Cat": 9294, "Cow": 9267, "Rooster": 9270}          # MM9's own rows (their 3D models are in actors.yml)
# The animal rows (monster_data.txt: Move Med, AI Wimp, Hst 0) wander in their pens; other civilians stay put.
ANIMAL_RANGE = {*range(9267, 9274), 9293, 9294, 9295, 9297, 9299}
PASS_MARKERS = {"Guard0": "PassMarker2", "Guard1": "PassMarker1"}
PRISONERS = {"InterrPrisoner0": "blever0", "InterrPrisoner1": "blever2", "InterrPrisoner2": "blever1"}


def rude_exit_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a dialogue with actor object `index` runs when it closes."""
    return 50000 + index


def rude_use_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a click on dialogue actor object `index` runs instead of opening it."""
    return 53000 + index


class DrangheimPrison(dungeon.Hooks):
    generator = "mm9r_drangheimprison"
    own_water_surfaces = (SINK_MODEL,)      # sink() builds its surface (no shared drawn_surfaces face)
    mover_events = {
        **{name: (event, "click") for name, event in EV_LEVER.items()},
        "WellLid": (EV_WELL_LID, "click"), "Hatch": (EV_HATCH, "click"),
        **{f"Celldoor{n}": (EV_LOCKED, "click") for n in (*range(1, 19), 25, 26, 27, 28, 30, 32, 33, 34, 36, 38)},
        "Celldoor29": (EV_COOK_CAGE, "click"), "Door1": (EV_GRATE, "click"), "InterrDoor": (EV_INTERR_DOOR, "click"),
    }

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        if PROPS.exists():
            content.props(PROPS)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        for name in (*EV_BEATINGS, "NagGuardTrigger0"):
            p = source.properties(name)
            content.pad(name, p["Pos"], p["Dims"], EV_BEATINGS.get(name, EV_BARRACKS))
        self.sink(build)
        self.place_perception_hints(build)
        self.points = {name: self.foot(build, source.properties(name)["Pos"])
                       for name in ("PassMarker1", "PassMarker2", "MarkerBeating0", "MarkerBeating9", "MarkerAnvil")}
        self.points["Beaten"] = self.foot(build, (-1250, -860, -2144))

    def smith_round(self, build, actor: dict) -> None:
        """DrangheimSmith.scr's AnvilLoop, CoolWeapon and ReturnWeapon as a marker path: he stands his WalkTo distance
        short of each object, facing it, and hammers (HAttack1, looped) at the anvil."""
        source = build.source
        objects = [np.asarray(source.properties(name)["Pos"], float) for name, *_ in SMITH_STOPS]
        path, stops = [], []
        for k, (name, distance, wait, clip) in enumerate(SMITH_STOPS):
            target, previous = objects[k], objects[k - 1]
            away = previous - target
            away[1] = 0.0
            stand = target + away / np.linalg.norm(away) * distance
            path.append(self.foot(build, stand))
            face = math.degrees(math.atan2(target[2] - stand[2], target[0] - stand[0])) % 360.0
            stop = {"point": k, "face": round(face, 1), "wait": wait}
            if clip:
                stop.update(clip=clip, loop=True)
            stops.append(stop)
        actor.setdefault("mm9_ai", {}).update(wander="path", path=path, path_stops=stops)
        self.smith_anvil, self.smith_rack = path[0], path[2]

    def foot(self, build, point) -> list:
        """A native point on the floor under an LT point."""
        floor = build.content.floor_at(point[0], point[2], point[1] + 16)
        if floor is None:
            raise SystemExit(f"no floor under {point}")
        return build.project.native([point[0], floor, point[2]]).round().astype(int).tolist()

    def sink(self, build) -> None:
        """The sink's water: the top face of MM9's SinkWater0 volume as an untouchable face with its sprite's first
        frame, drawn at MM9's SurfaceAlpha 0.7 (the scene's translucent_faces, scene() below)."""
        project, package = build.project, build.package
        points = np.array(build.source.models[SINK_MODEL].points, float)
        top = points[:, 1].max()
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        ring = np.array([[x0, top, z0], [x0, top, z1], [x1, top, z1], [x1, top, z0]])
        native = np.round(project.native(ring)).astype(np.int64)
        if np.cross(native[1] - native[0], native[2] - native[0])[2] < 0:
            native, ring = native[::-1], ring[::-1]
        key = package.material(SINK_TEXTURE)[0]
        node = f"TRIGGER_water_{SINK_MODEL}"
        package.nodes[node].append((native, ring[:, [0, 2]] - ring[:, [0, 2]].min(0), key))
        room = build.content.owner(np.array([(x0 + x1) / 2, top - 4, (z0 + z1) / 2]))
        package.room_nodes[room].append(node)
        package.metadata["surfaces"].append({"id": SINK_MODEL, "source_node": node, "flags": ["untouchable"]})
        build.content.report["water"] = {"model": SINK_MODEL, "room": room, "z": int(native[0][2])}

    def place_perception_hints(self, build) -> None:
        """Each PerceptionBrush's visible polygons (MM9's Perception.spr, the rest of the brush is Invisible.dtx) as
        untouchable translucent faces with a cog: the map script shows them to a party with the Perception for it. They
        stand a few LT off walls and doors, some facing the wall, so each goes in the room of the air beside it and
        draws from both sides (scene() below)."""
        package, source = build.package, build.source
        self.hints = {}                 # brush name -> cog
        self.hint_faces = 0
        difficulties = perception_difficulties_by_model_name(source.world)
        names = sorted(difficulties, key=lambda n: int(n[len("perceptionbrush"):]))
        self.hint_difficulty = max(difficulties[n] for n in names)
        for k, lower in enumerate(names):
            name = next(model for model in source.models if model.lower() == lower)
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                # A strip along a floor has solid voxels on both sides: the nearest air is its room.
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

    def install_frames(self, build, texture: str) -> None:
        """An MM9 .spr as a texture frame sequence. The table is the engine's and only the review root's copy changes
        (as Anskram Keep's: a world contribution would take it at integration)."""
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

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        old = {a["mm9_source_object_index"]: a for a in
               yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]}
        groups = {"Interrogator": GROUP_INTERROGATOR, "InterrDoorman": GROUP_DOORMAN, "InterrWarden": GROUP_WARDEN,
                  "Help1": GROUP_HELP, "Help2": GROUP_HELP, "Help3": GROUP_HELP, "BarracksGuard0": GROUP_BARRACKS,
                  "BarracksGuard1": GROUP_BARRACKS, "BarracksGuard2": GROUP_BARRACKS, "DwarvenSmith0": GROUP_SMITH,
                  **{name: GROUP_FRONT for name in RUDE_OBJECTS}}
        descriptors = {int(cells[0]): (int(cells[2]), int(cells[3])) for cells in
                       (line.split("\t") for line in DESCRIPTORS.read_text(encoding="latin-1").splitlines())
                       if cells and cells[0].isdigit()}
        out, self.actor = [], {}
        for o in source.objects:
            if o["class"] not in build.project.monster_classes:
                continue
            name, p = o["name"], o["properties"]
            if name == "DwarvenSmith1":     # DrangheimSmith.scr Main: bBearer 0 removes itself at once
                content.report["omitted"].append({"anchor": name, "class": o["class"],
                                                  "reason": "DrangheimSmith.scr removes it at start"})
                continue
            guard = o["class"] in ("Guard", "GuardSegeant", "GuardCaptain", "DwarvenGuard")
            civilian = o["class"] not in bases and name not in bases
            base = bases.get(name)
            if base is None:                # NPCs and animals: the old import's records of their monster rows
                record = old[o["index"]]
                base = {key: record[key] for key in ("name", "attributes", "hp", "hostility_type", "monster_info_id",
                                                     "monster_id", "radius", "height", "move_speed")}
                row = BODY_ROWS.get(str(p.get("Filename", "")).lower(), base["monster_id"])
                row = ANIMAL_ROWS.get(o["class"], row)
                base["monster_id"] = base["monster_info_id"] = row
                if row in descriptors:
                    base["height"], base["radius"] = descriptors[row]
            group = groups.get(name, GROUP_GUARDS if guard else GROUP_CIVILIANS if civilian else 0)
            actor = content.actor(o, base, sector_of_room, group=group, friendly=guard or civilian,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            actor.update(placed_body(base["monster_id"], p))    # MM9's body at the DAT's own Scale (replaces the row's)
            rude = RUDE_OBJECTS.get(name) or old.get(o["index"], {}).get("mm9_rude_id", 0)
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = (civilian and base["monster_id"] not in ANIMAL_RANGE) or name in RUDE_OBJECTS
            if name == "DwarvenSmith0":
                self.smith_round(build, actor)
                actor["held_items"] = [dict(SMITH_HAMMER)]
            self.actor[name] = actor["actor_index"]
            out.append(actor)
        self.objects = {name: next(o["index"] for o in source.objects if o["name"] == name)
                        for name in ("Ivsar", "Antoni", "CommonerHuman2MaleA0", *RUDE_OBJECTS, *PRISONERS)}
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Drangheim Prison")
        points, actor, objects = self.points, self.actor, self.objects
        script.doors()
        script.chests()
        # The smith (DrangheimSmith.scr: no hostility script) is not among them: the alarm leaves him at his work.
        guards = [GROUP_GUARDS, GROUP_HELP, GROUP_BARRACKS, GROUP_WARDEN, GROUP_DOORMAN, GROUP_INTERROGATOR]
        lines = [
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            "",
            "-- The pass and the alarm (DrangheimHostility.inc, DP_CheckPass.inc, Guardhelp.scr, GuardToNegate.scr): a guard",
            f"-- lets the party be while it holds the visitor's pass (key {KEY_PASS}) and has not raised the alarm (key",
            f"-- {KEY_HOSTILE}); the gate guards (GuardRude.scr) mind only the alarm.",
            f"local INNER_GROUPS = {{{', '.join(map(str, guards))}}}",
            f"-- The gate guards (GuardRude.scr :StartWork): 1 in {GUARD_SLEEP_ODDS} sleeps from the map's start (LoopAnim sleep)",
            "-- until a click wakes him (:OnUse :Wakeup, PlayAnim Stand) or the alarm sounds.",
            "local GATE = {" + ", ".join(f"{name} = {{actor = {self.actor[name]}, rude = {rude}}}"
                                         for name, rude in RUDE_OBJECTS.items()) + "}",
            "local function wake(name)",
            "    if var(\"Asleep\" .. name) == 0 then return end",
            "    set(\"Asleep\" .. name, 0)",
            "    evt.ClearActorPresentation(GATE[name].actor)",
            "end",
            "local function rollSleep(name, step)",
            f"    local asleep = MM9.hasKey({KEY_HOSTILE}) == 0 and evt.RandomBetween(1, {GUARD_SLEEP_ODDS}, step) == 1",
            "    set(\"Asleep\" .. name, asleep and 1 or 0)",
            "    if asleep then evt.PlayActorClip(GATE[name].actor, \"sleep\", true) end",
            "end",
            "local function applyHostility()",
            f"    local alarm = MM9.hasKey({KEY_HOSTILE}) == 1",
            f"    local visitor = MM9.hasKey({KEY_PASS}) == 1 and not alarm",
            "    for _, group in ipairs(INNER_GROUPS) do evt.SetMonGroupBit(group, MonsterBits.Hostile, not visitor) end",
            f"    evt.SetMonGroupBit({GROUP_SMITH}, MonsterBits.Hostile, false)   -- the smith never turns (DrangheimSmith.scr)",
            f"    evt.SetMonGroupBit({GROUP_FRONT}, MonsterBits.Hostile, alarm)",
            "    -- the alarm's AddEnemy Player: MM9's monster AI walks the gate guards from their posts at the party",
            "    if alarm then",
            *[f"        evt.SetActorImmobile({self.actor[name]}, false); wake(\"{name}\")   -- {name}"
              for name in RUDE_OBJECTS if name in self.actor],
            "    end",
            "end",
            "local function alarm()    -- TurnHostilityOn, AlarmControl.scr OnAlarm",
            f"    if MM9.hasKey({KEY_HOSTILE}) == 0 then",
            f"        MM9.giveKey({KEY_HOSTILE})",
            "        evt.PlaySoundName(\"events/alarmbell.wav\", 0, 0, 0)",
            "    end",
            "    applyHostility()",
            "end",
            f"local GUARD_MONSTERS = {{{', '.join(f'[{m}] = true' for m in GUARD_MONSTERS)}}}",
            "-- DrangheimHostility.inc OnDamage/OnDeath: only the player's blow (IsPlayer) turns a guard on; a Nagate's does not",
            f"handlers[{DAMAGE_HOOK}] = function(context) if GUARD_MONSTERS[context.monsterId] and context.byParty then "
            "alarm() end end",
            f"handlers[{KILL_HOOK}] = function(context) if GUARD_MONSTERS[context.monsterId] and context.byParty then "
            "alarm() end end",
            "",
            "-- The gate guards (GuardRude.scr :OnRude, :OnMove): the alarm given in the talk goes off; with the pass Guard2",
            f"-- (dialogue 426) hands over the Visitor's Pass item ({ITEM_PASS}) and Guard0/1 step aside to their markers.",
        ]
        for name, rude in RUDE_OBJECTS.items():
            lines.append(f"handlers[{rude_use_event(objects[name])}] = function() wake(\"{name}\"); "
                         f"MM9.openRude({rude}, {actor[name]}) end   -- {name} :OnUse")
            script.add([], (rude_use_event(objects[name]), name, None))
            marker = PASS_MARKERS.get(name)
            lines.append(f"handlers[{rude_exit_event(objects[name])}] = function()   -- {name}")
            lines.append(f"    if MM9.hasKey({KEY_HOSTILE}) == 1 then alarm() return end")
            lines.append(f"    if MM9.hasKey({KEY_PASS}) == 0 then return end")
            lines.append("    applyHostility()")
            if marker:
                x, y, z = points[marker]
                lines += [f"    set(\"Aside{name}\", 1)",
                          f"    evt.SetMapActorPosition({actor[name]}, {x}, {y}, {z})"]
            else:
                lines.append(f"    if MM9.hasItem({ITEM_PASS}, \"drangheimprison:{name}\") == 0 then give({ITEM_PASS}, "
                             f"\"drangheimprison:{name}\") end")
            lines.append("end")
            script.add([], (rude_exit_event(objects[name]), name, None))
        cook, brother, ivsar = objects["CommonerHuman2MaleA0"], objects["Antoni"], objects["Ivsar"]
        lines += [
            "",
            f"-- The cook, Aymril Banito (NPC419.scr :OnRude, :Call, :Unlock): with the deal (key {KEY_DEAL}) he gives key",
            f"-- {KEY_COOK_DONE} and unlocks the cow pen's door (Celldoor29); any other end of the talk calls the guards.",
            f"handlers[{rude_exit_event(cook)}] = function()",
            f"    if MM9.hasKey({KEY_DEAL}) == 1 then MM9.giveKey({KEY_COOK_DONE}) else alarm() end",
            "end",
            f"handlers[{EV_COOK_CAGE}] = function()   -- Celldoor29: locked until the cook unlocks it (NPC419.scr :Main)",
            f"    if MM9.hasKey({KEY_COOK_DONE}) == 1 then evt.SetDoorState(DOORS.Celldoor29, DoorAction.Trigger) else "
            "evt.StatusText(\"The door is locked.\") end",
            "end",
            "",
            f"-- His brother Antoni (NPC427.scr :OnRude, :OnVanish): freed (key {KEY_BROTHER_FREED}), the reward once (key "
            f"{KEY_BROTHER_REWARD}, {BROTHER_EXPERIENCE} experience), then he is gone (MM9: runs to AntoniMarker, vanishes).",
            f"handlers[{rude_exit_event(brother)}] = function()",
            f"    if MM9.hasKey({KEY_BROTHER_FREED}) == 0 then return end",
            f"    if MM9.hasKey({KEY_BROTHER_REWARD}) == 0 then",
            f"        MM9.giveKey({KEY_BROTHER_REWARD})",
            f"        {experience_lua(BROTHER_EXPERIENCE, KEY_BROTHER_REWARD)}",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            "    end",
            f"    MM9.removeActor({actor['Antoni']})",
            "end",
            "",
            f"-- Ivsar Forktooth (NPC90.scr :Onrude, :FollowPlayer): key {KEY_MET_OUTSIDE} is taken, and unless he is home "
            f"(key {KEY_IVSAR_HOME}) walking out with him is the alarm. MM9 has him follow;",
            f"-- here, sent by Bjarni (key {KEY_SENT_BY_BJARNI}), he goes ahead (\"If we get separated I'll meet you outside\").",
            f"handlers[{rude_exit_event(ivsar)}] = function()",
            f"    if MM9.hasKey({KEY_MET_OUTSIDE}) == 1 and MM9.hasKey({KEY_GOT_OUT}) == 0 then MM9.openRude(90) return end",
            f"    MM9.takeKey({KEY_MET_OUTSIDE})",
            f"    if MM9.hasKey({KEY_IVSAR_HOME}) == 1 then return end",
            "    alarm()",
            f"    if MM9.hasKey({KEY_SENT_BY_BJARNI}) == 1 then MM9.removeActor({actor['Ivsar']}) end",
            "end",
            "",
            f"-- The prisoners (DrangheimPrisoner.scr :OnPlayerRescue): a party without the pass gets {RESCUE_EXPERIENCE} "
            "experience for each once; dialogue 431.",
        ]
        script.add([], (rude_exit_event(cook), "Aymril Banito", None), (EV_COOK_CAGE, "Cell door", "Door"),
                   (rude_exit_event(brother), "Antoni Banito", None), (rude_exit_event(ivsar), "Ivsar Forktooth", None),
                   (DAMAGE_HOOK, "Guards hurt", None), (KILL_HOOK, "Guards killed", None))
        for name in PRISONERS:
            event = rude_use_event(objects[name])
            lines += [f"handlers[{event}] = function()   -- {name}",
                      f"    if MM9.hasKey({KEY_PASS}) == 0 and var(\"Rescued{name}\") == 0 then",
                      f"        set(\"Rescued{name}\", 1)",
                      f"        {experience_lua(RESCUE_EXPERIENCE)}",
                      "    end",
                      "    MM9.openRude(431)",
                      "end"]
            script.add([], (event, name, None))
        lines += ["", "-- The cell levers (the lever objects' OpenTrigger/CloseTrigger): a lever unlocks and opens its cell,"
                      " back shuts and locks it.",
                  f"handlers[{EV_LOCKED}] = function() evt.StatusText(\"The door is locked.\") end"]
        script.add([], (EV_LOCKED, "Cell door", "Door"))
        for lever, cell in LEVERS.items():
            calls = [f"evt.SetDoorState(DOORS.{lever}, DoorAction.Trigger)"]
            if cell:
                calls.append(f"evt.SetDoorState(DOORS.{cell}, DoorAction.Trigger)")
            lines.append(f"handlers[{EV_LEVER[lever]}] = function() {' '.join(calls)} end")
            script.add([], (EV_LEVER[lever], "Lever", "Lever"))
        lines += [
            "",
            "-- The well's lid (Lid1, LidWheel1): a click swings it over the shaft and turns its wheel (their triggers).",
            f"handlers[{EV_WELL_LID}] = function() evt.SetDoorState(DOORS.Lid1, DoorAction.Trigger); "
            "evt.SetDoorState(DOORS.LidWheel1, DoorAction.Trigger) end",
            f"handlers[{EV_HATCH}] = function() evt.SetDoorState(DOORS.RotatingDoor3, DoorAction.Trigger) end   -- over Ladder0",
            "",
            "-- The smith (DrangheimSmith.scr :AnvilLoop, :PlayRandomSound, :CoolWeapon, :ReturnWeapon; the grate's"
            " Open/CloseTrigger turn him off and on):",
            "-- his round is his marker path (the scene); he hammers at the anvil, a blow's clang every 3 s while he is there",
            "-- and the grate is shut. Off (:TurnOff) he stops where he is.",
            f"local SMITH, ANVIL = {actor['DwarvenSmith0']}, {{{', '.join(map(str, self.smith_anvil))}}}",
            "local function smithAtWork() evt.SetActorImmobile(SMITH, var(\"SmithOff\") == 1) end",
            f"handlers[{EV_GRATE}] = function()",
            "    evt.SetDoorState(DOORS.Door1, DoorAction.Trigger)",
            "    set(\"SmithOff\", 1 - var(\"SmithOff\"))",
            "    smithAtWork()",
            "end",
            "local function smithAtAnvil()",
            "    local x, y = evt.GetMapActorPosition(SMITH)",
            "    return x ~= nil and (x - ANVIL[1]) ^ 2 + (y - ANVIL[2]) ^ 2 < 160 ^ 2",
            "end",
            f"handlers[{T_SMITH}] = function()",
            f"    if var(\"SmithOff\") == 0 and evt.IsMapActorWithinPartyDistance(SMITH, 1400) and smithAtAnvil()",
            f"        and not evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_SMITH}, 0, false) then",
            f"        evt.PlaySoundName(\"events/metalmetal0\" .. evt.RandomBetween(1, 5, 1) .. \".wav\", "
            f"{', '.join(map(str, points['MarkerAnvil']))})",
            "    end",
            "end",
            "-- His tool in his right hand (:AttachHammer, :AttachSword): the sword once he leaves the anvil (:CoolWeapon),",
            "-- the hammer again at the weapon rack (:OnReturnedWeapon). Polled every 0.5 s.",
            f"local RACK = {{{', '.join(map(str, self.smith_rack))}}}",
            f"local SMITH_TOOLS = {{[0] = \"{SMITH_HAMMER['model']}\", [1] = \"{SMITH_SWORD['model']}\"}}",
            f"handlers[{T_SMITH_ITEM}] = function()",
            f"    evt.StartTimer({T_SMITH_ITEM}, seconds(0.5))",
            f"    if evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_SMITH}, 0, false) then return end",
            "    local x, y = evt.GetMapActorPosition(SMITH)",
            "    if x == nil then return end",
            "    local atAnvil, sword = smithAtAnvil(), var(\"SmithSword\")",
            "    local want = sword",
            "    if sword == 0 and var(\"SmithAtAnvil\") == 1 and not atAnvil then want = 1 end",
            "    if sword == 1 and (x - RACK[1]) ^ 2 + (y - RACK[2]) ^ 2 < 160 ^ 2 then want = 0 end",
            "    set(\"SmithAtAnvil\", atAnvil and 1 or 0)",
            "    if want == sword then return end",
            "    set(\"SmithSword\", want)",
            f"    evt.DetachActorItem(SMITH, \"{SMITH_HAMMER['node']}\")",
            f"    evt.AttachActorItem(SMITH, SMITH_TOOLS[want], \"{SMITH_HAMMER['node']}\")",
            "end",
        ]
        script.add([], (EV_GRATE, "Grate", "Grate"), (T_SMITH, "Smith", None, "timer"),
                   (T_SMITH_ITEM, "Smith's tools", None, "timer"),
                   (EV_WELL_LID, "Well lid", "Lid"), (EV_HATCH, "Hatch", "Hatch"))
        lines += self.interrogation(script, build)
        hide = [f"    if MM9.hasKey({KEY_GOT_OUT}) == 1 or MM9.hasKey({KEY_SENT_BY_BJARNI}) == 1 then "
                f"MM9.removeActor({actor['Ivsar']}) end",
                f"    if MM9.hasKey({KEY_BROTHER_REWARD}) == 1 then MM9.removeActor({actor['Antoni']}) end"]
        for name, marker in PASS_MARKERS.items():
            x, y, z = points[marker]
            hide.append(f"    if var(\"Aside{name}\") == 1 then evt.SetMapActorPosition({actor[name]}, {x}, {y}, {z}) end")
        # GuardToNegate.scr :Main2 AddEnemy Nagate is the barracks guards' own, not every guard's: their group's rows.
        relations = [f"    evt.SetMonsterRelation({{group = {GROUP_BARRACKS}}}, {n}, {RELATION_SHORT}); "
                     f"evt.SetMonsterRelation({n}, {{group = {GROUP_BARRACKS}}}, {RELATION_SHORT})"
                     for n in NAGATE_MONSTERS]
        lines += [
            "",
            "-- The barracks guards (GuardToNegate.scr): enemies of the Nagate; the party at DDoor5 sets them off (MM9: they",
            "-- run to the barracks; here they call out and fight what they meet).",
            f"handlers[{EV_BARRACKS}] = function()",
            "    if var(\"BarracksCalled\") == 1 then return end",
            "    set(\"BarracksCalled\", 1)",
            "    -- the call is BarracksGuard2's (GuardToNegate.scr :FaceEachOther): dead, it takes no Hello",
            f"    if not MM9.receives(\"drangheimprison\", \"BarracksGuard2\", \"Hello\", {actor['BarracksGuard2']}) "
            "then return end",
            "    evt.PlaySoundName(\"vo/irequireassistance.wav\", 0, 0, 0)",
            "end",
            f"-- The PerceptionBrushes: the red glow on the secret doors shows to a party with Perception "
            f"{self.hint_difficulty} or better",
            "-- (MM9's PerceptionValue; the BLV holds them visible so that they are lightmapped). On load and every 3 s.",
            f"local HINTS = {{{', '.join(str(cog) for cog in self.hints.values())}}}",
            "local function updateHints()",
            f"    local want = evt.CheckSkill({PERCEPTION_SKILL}, 0, {self.hint_difficulty}) and 2 or 1",
            "    if var(\"PerceptionHints\") == want then return end",
            "    set(\"PerceptionHints\", want)",
            "    for _, cog in ipairs(HINTS) do evt.SetFacetBit(cog, FacetBits.Invisible, want == 1) end",
            "end",
            f"handlers[{T_HINTS}] = updateHints",
            "handlers[1] = function()   -- map load",
            "    applyHostility()",
            "    -- saves made before 2026-11-08 hold every guard row's AddEnemy Nagate: cleared (the group rows win)",
            *[f"    evt.SetMonsterRelation({g}, {n}, 0); evt.SetMonsterRelation({n}, {g}, 0)"
              for g in GUARD_MONSTERS for n in NAGATE_MONSTERS],
            *relations,
            *hide,
            "    smithAtWork()",
            f"    evt.StartTimer({T_SMITH_ITEM}, seconds(0.5))",
            *[f"    rollSleep(\"{name}\", {k + 1})" for k, name in enumerate(RUDE_OBJECTS)],
            "    updateHints()",
            "end",
        ]
        script.add(lines, (EV_BARRACKS, "NagGuardTrigger0", None), (T_HINTS, "Perception hints", None, "timer"),
                   (1, "Map load", None))
        script.hooks += [f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Guards hurt", handlers[{DAMAGE_HOOK}])',
                         f'RegisterMonsterKilledHook({KILL_HOOK}, "Guards killed", handlers[{KILL_HOOK}])']
        # The hooks' handlers are not events: leave their registrations to the hook lines.
        script.registrations = [r for r in script.registrations if r[0] not in (DAMAGE_HOOK, KILL_HOOK)]
        return script.finish(on_load=[1])

    def interrogation(self, script, build) -> list[str]:
        """DrangheimInterrogator.scr, DrangheimWarden.scr, DrangheimDoorman.scr, DrangheimPrisoner.scr: the interrogator
        walks MarkerBeating0-9 (ListTraverse.inc, pacing) with each prisoner in turn following him (evt.MoveActorTo),
        the warden works the cell levers, the doorman the interrogation room's doors, as a list of steps per prisoner
        run by map vars (BeatPrisoner, BeatStep) and one timer, which also finishes a walk not done in time."""
        points, actor, source = self.points, self.actor, build.source
        script.add([], *[(event, name, None) for name, event in EV_BEATINGS.items()],
                   (EV_INTERR_DOOR, "Door", "Door"), (T_BEATING, "Interrogation", None, "timer"),
                   (EV_INTERR_ARRIVE, "Interrogator arrives", None), (EV_PRISONER_ARRIVE, "Prisoner arrives", None))
        markers = [self.foot(build, source.properties(f"MarkerBeating{i}")["Pos"]) for i in range(10)]
        rows = []
        for name, lever in PRISONERS.items():
            k = len(rows)
            home = np.asarray(self.foot(build, source.properties(name)["Pos"]), float)
            cell = self.foot(build, source.properties(str(source.properties(name)["ScriptParams"]).split()[0])["Pos"])
            # where he stops before the interrogator at MarkerBeating<k> (DrangheimPrisoner.scr :LeaveCell WalkTo 5):
            # PICK_OFFSET toward his cell, so that the two bodies do not meet
            way = home - np.asarray(markers[k], float)
            way[2] = 0.0
            pick = np.asarray(markers[k], float) + way / np.linalg.norm(way) * PICK_OFFSET
            rows.append(f"{{prisoner = {actor[name]}, lever = DOORS.{lever}, cell = DOORS.{LEVERS[lever]}, "
                        f"pick = {lua.point(pick)}, home = {lua.point(cell)}}}")
        beat = ", ".join(map(str, markers[9]))
        return [
            "",
            "-- The interrogation (DrangheimInterrogator.scr; either TriggerBeatings pad, once). For each of the three",
            "-- prisoners: the interrogator walks to his cell's marker; the warden's lever opens the cell (aware); the",
            "-- interrogator calls him out (fidget2), he comes out and cowers; the interrogator signals (aware) and the cell",
            "-- shuts; the prisoner follows him along MarkerBeating<k+1>-9; the doorman opens the interrogation room at 8 and",
            "-- shuts it at 9; the beating sounds; the door opens and they walk back, the door shutting behind them; the",
            "-- cell opens, the interrogator sends him in (fidget1), he walks to his CellMarker and the cell shuts. It stops",
            "-- when the warden, the doorman or the interrogator is dead or the alarm is up (MM9: OnObjectLinkBroken,",
            f"-- hostility). A walk not done in {LEG_TIMEOUT} s (or under way when the game was saved) ends at its point at once.",
            f"local MARKERS = {{{', '.join(f'[{i}] = {lua.point(m)}' for i, m in enumerate(markers))}}}",
            f"local BEATEN = {{{', '.join(rows)}}}",
            f"local INTERR, WARDEN, IN_ROOM = {actor['Interrogator']}, {actor['InterrWarden']}, "
            f"{lua.point(points['Beaten'])}",
            f"local CELL_WAIT, DOOR_WAIT, BEAT_SECONDS, LEG_TIMEOUT = {CELL_WAIT}, {DOOR_WAIT}, {BEAT_SECONDS}, {LEG_TIMEOUT}",
            f"local function beatingOff() return MM9.hasKey({KEY_HOSTILE}) == 1 or "
            f"evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_WARDEN}, 0, false) or "
            f"evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_DOORMAN}, 0, false) or "
            f"evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUP_INTERROGATOR}, 0, false) end",
            "local function beatStep(delay) arm(" + str(T_BEATING) + ", delay) end",
            "local function openGroupInterr() open(\"RightDoor0\"); open(\"LeftDoor0\") end",
            "local function closeGroupInterr() close(\"RightDoor0\"); close(\"LeftDoor0\") end",
            "local function cellLever(b, opening)   -- DrangheimWarden.scr :OpenCell / :CloseCell",
            "    evt.PlayActorClip(WARDEN, \"aware\")",
            "    local action = opening and DoorAction.Open or DoorAction.Close",
            "    evt.SetDoorState(b.lever, action); evt.SetDoorState(b.cell, action)",
            "end",
            "local function route(from, to)   -- the markers between, one of two that stand on the same spot (1, 2) dropped",
            "    local out, step = {}, from <= to and 1 or -1",
            "    for i = from, to, step do",
            "        local m, last = MARKERS[i], out[#out]",
            "        if last == nil or m[1] ~= last[1] or m[2] ~= last[2] then out[#out + 1] = m end",
            "    end",
            "    return out",
            "end",
            "local function plan(k)   -- prisoner k (0-2): {run, wait} or a walk {i = point, p = point}",
            "    local b, steps = BEATEN[k + 1], {}",
            "    local function add(step) steps[#steps + 1] = step end",
            "    add({i = MARKERS[k]})",
            "    add({run = function() cellLever(b, true) end, wait = CELL_WAIT})",
            "    add({run = function() evt.PlayActorClip(INTERR, \"fidget2\") end, wait = 2})   -- ANIM_COMEOUT",
            "    add({p = b.pick})",
            "    add({run = function() evt.PlayActorClip(b.prisoner, \"cower\") end, wait = 1.2})",
            "    add({run = function() evt.PlayActorClip(INTERR, \"aware\"); cellLever(b, false) end, wait = CELL_WAIT})",
            "    local out = route(k, 8)",
            "    for n = 2, #out do add({i = out[n], p = out[n - 1]}) end",
            "    add({run = openGroupInterr, wait = DOOR_WAIT})",
            "    add({i = MARKERS[9], p = IN_ROOM})",
            "    add({run = closeGroupInterr, wait = DOOR_WAIT})",
            f"    add({{run = function() evt.PlaySoundName(\"events/beatdownmix8bit.wav\", {beat}) end, wait = BEAT_SECONDS}})",
            "    add({run = openGroupInterr, wait = DOOR_WAIT})",
            "    local back = route(9, k)",
            "    for n = 2, #back do",
            "        add({i = back[n], p = back[n - 1]})",
            "        if n == 3 then add({run = closeGroupInterr, wait = 0.5}) end   -- both past the door (8)",
            "    end",
            "    add({run = function() cellLever(b, true) end, wait = CELL_WAIT})",
            "    add({run = function() evt.PlayActorClip(INTERR, \"fidget\") end, wait = 2})   -- ANIM_GOBACK",
            "    add({p = b.home})",
            "    add({run = function() cellLever(b, false) end, wait = 4})",
            "    return steps",
            "end",
            "local function walker(step) return step.i and INTERR or nil, step.p and BEATEN[var(\"BeatPrisoner\")].prisoner or nil end",
            "local function runBeat()   -- the next step; each clip has ended by then (its step's wait): let them go",
            "    local k = var(\"BeatPrisoner\")",
            "    for _, a in ipairs({INTERR, WARDEN, BEATEN[k].prisoner}) do evt.ClearActorPresentation(a) end",
            "    if beatingOff() then set(\"Beatings\", 2) return end",
            "    local step = plan(k - 1)[var(\"BeatStep\")]",
            "    if step == nil then   -- this prisoner is back: the next",
            "        if k >= #BEATEN then set(\"Beatings\", 2) return end",
            "        set(\"BeatPrisoner\", k + 1); set(\"BeatStep\", 1)",
            "        return runBeat()",
            "    end",
            "    set(\"BeatWalk\", var(\"BeatStep\"))",
            "    set(\"BeatStep\", var(\"BeatStep\") + 1)",
            "    if step.run then step.run(); beatStep(step.wait) return end",
            "    local i, p = walker(step)",
            f"    set(\"WaitI\", i and 1 or 0); set(\"WaitP\", p and 1 or 0)",
            f"    if i then evt.ClearActorPresentation(i); evt.MoveActorTo(i, step.i[1], step.i[2], step.i[3], {EV_INTERR_ARRIVE}) end",
            f"    if p then evt.ClearActorPresentation(p); evt.MoveActorTo(p, step.p[1], step.p[2], step.p[3], {EV_PRISONER_ARRIVE}) end",
            "    beatStep(LEG_TIMEOUT)",
            "end",
            "local function startBeatings()",
            "    if var(\"Beatings\") ~= 0 then return end",
            "    set(\"Beatings\", 1)",
            "    set(\"BeatPrisoner\", 1)",
            "    set(\"BeatStep\", 1)",
            "    beatStep(1)",
            "end",
            f"handlers[{EV_BEATINGS['TriggerBeatings0']}] = function() startBeatings() end",
            f"handlers[{EV_BEATINGS['TriggerBeatings1']}] = function() startBeatings() end",
            f"handlers[{EV_INTERR_DOOR}] = function() evt.StatusText(\"The door is locked.\") end",
            f"handlers[{T_BEATING}] = function()",
            f"    if not fired({T_BEATING}) or var(\"Beatings\") ~= 1 then return end",
            "    if var(\"WaitI\") == 1 or var(\"WaitP\") == 1 then   -- the walk took too long, or a load ended it: there",
            "        local step = plan(var(\"BeatPrisoner\") - 1)[var(\"BeatWalk\")]",
            "        local i, p = walker(step)",
            "        if i and var(\"WaitI\") == 1 then evt.StopActorMove(i); evt.SetMapActorPosition(i, step.i[1], step.i[2], step.i[3]) end",
            "        if p and var(\"WaitP\") == 1 then evt.StopActorMove(p); evt.SetMapActorPosition(p, step.p[1], step.p[2], step.p[3]) end",
            "        set(\"WaitI\", 0); set(\"WaitP\", 0)",
            "    end",
            "    runBeat()",
            "end",
            "local function arrived(flag)",
            "    if var(\"Beatings\") ~= 1 or var(flag) == 0 then return end",
            "    set(flag, 0)",
            "    if var(\"WaitI\") == 1 or var(\"WaitP\") == 1 then return end",
            f"    evt.StopTimer({T_BEATING}); set(\"Armed{T_BEATING}\", 0)",
            "    runBeat()",
            "end",
            f"handlers[{EV_INTERR_ARRIVE}] = function() arrived(\"WaitI\") end",
            f"handlers[{EV_PRISONER_ARRIVE}] = function() arrived(\"WaitP\") end",
        ]

    def scene(self, build, scene: dict) -> None:
        """The sink's water at MM9's SurfaceAlpha 0.7, seen from above, and the perception hints at their brushes'
        Alpha (faces.yml lists static nodes only: the faces are found in the compiled BLV by texture)."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]

        def faces_of(texture: str) -> list[int]:
            alias = build.source.aliases[texture.lower()]["alias"].lower()
            return sorted(f["index"] for f in blv["faces"] if str(f.get("texture_name", "")).lower() == alias)

        water, hints = faces_of(SINK_TEXTURE), faces_of(PERCEPTION_TEXTURE)
        if len(water) != 1:
            raise SystemExit(f"the sink's water: {len(water)} faces with its texture")
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        scene.setdefault("translucent_faces", []).extend([
            {"faces": water, "opacity": 0.7, "tint": [1.0, 1.0, 1.0], "two_sided": False},
            {"faces": hints, "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0], "two_sided": True}])
        if build.project.install:
            self.install_frames(build, PERCEPTION_TEXTURE)
            self.install_frames(build, WATER_TEXTURE)
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)

    def report(self, build) -> dict:
        return {"scripted": {"actors": self.actor, "objects": self.objects, "points": self.points}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, DrangheimPrison()))
