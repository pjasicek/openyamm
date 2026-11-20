#!/usr/bin/env python3
"""
Thjorad Mine, MM9 rework: MM9's THJORADMINE.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_thjoradmine/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_thjoradmine/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the archway cuts (work/cuts/) and the excluded seeds; this file adds the mine's
water surface, its population (props.json from ../../props/mm9_thjoradmine_claude, 82 actors and 20 hidden spawns)
and its scripted objects as native Lua, each citing its .scr (README.md, "Scripted objects"):
- the hard rock (tm_hardrock.scr "10 36 5000" on `dw`, the twelve DestructableBrushes db12-db23) and Ebora behind it
  (EboraMines.scr :FreeAtLast);
- the cave-in (Trigger7 -> CaveIn DestructOn.scr, tm_hardrock.scr "1 35 5000" on CaveInControl);
- the slag extractor (SlagExtractor.scr, SlagBase.scr, Hjarrand: NPC7.scr "Refinery"), behind RotatingDoor0;
- the NPCs by RUDE dialogue (NPC7/8/9.scr, Shopkeeper.scr, DwarvenMiner.scr);
- the troglodyte spawns (SpawnMgr.scr "1 1 Troglodyte TriggerSpawn", SpawnLoc.scr, TriggerLocation*);
- the gnolls' bust-out (TriggerHardRock -> KingKong.scr ForceBreak, BustOutBrush0-2);
- the spiked barricades (BoardSpike.scr, SpikeDoorA/B.scr, SpikeDoorOpen.scr: BarWall0/1, ABDoorBoards0);
- the abandoned mine's machinery: the falling torch and the exploding barrels (TM_FallingTorch.scr, TM_TorchFlame.scr,
  BlowUpTheBoards.scr), the mine cart (TM_MineCarA.scr, TM_FirstFallingTorch.scr, TM_FirstFallingFlame.scr), the
  steam valve (TM_SteamWater.scr), the falling board;
- the refinery's sliding door and handle, the two lift gates and their levers (object wiring), the stalactite;
- the letters (BookLetter.scr 426, 486, 487, 571-574).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))

import dungeon  # noqa: E402
import review_root  # noqa: E402
from dungeon import ambient, lua, tables, water  # noqa: E402
from dungeon.objects import perception_light_lua  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402
from quest_xp import experience_lua  # noqa: E402
from script_text import speaker_line  # noqa: E402
import cutscenes  # noqa: E402

PROPS = PROJECT / "props.json"
LANTERN_SCALE = 0.75                # the BrightScale of the mine's 140 lanterns (scale_lights)
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/thjoradmine.scene.yml"
DESCRIPTORS = ROOT / "assets_dev/worlds/mm9/data_tables/monster_descriptors.txt"

# DirtyWater1 (BlueWater, ShowSurface 1, Sprites\Water\water125.spr, SurfaceAlpha 0.7, FogColor 0/91/91) floods the deep
# cavern under the cave-in from -1408 to -1152 LT. Its surface, cut to the cavern on a 64 LT grid (Dook's Castle's lake;
# the review root's liquid `water_mm9` draws it), is non-solid and swum since the shared water rule (2026-11-06,
# dungeon/water.py), its bed built; with overrides.yml `map: {swim: false}` a solid face the party wades on.
POOL_MODEL, POOL_TEXTURE, POOL_TILE = "DirtyWater1", "water:pool", 64.0
# Invisible ramps over the plank fence across the abandoned mine's west tunnel (PhysicsBSP planks, 72 LT tall at
# z -5824..-5808): MM9's player jumps it; the party's jump is 90 native (35 LT), so the room behind (AB_Troglodyte2-4,
# MineCar5) was out of reach (work/reach/probe_board_room.yml). A ramp up each side of the fence, in the window west of
# its diagonal plank and between the two posts south of it (x 2556-2604), 31-36 degrees, with a flat top over the
# fence (the party's body must clear the fence before its front reaches it). (name, x0, x1, z0, z1 LT, axis it rises along, (coordinate, y) low and high end).
RAMPS = [
    ("RampFenceNorth", 2556, 2604, -5800, -5696, "z", (-5696, -580), (-5800, -517)),
    ("RampFenceTop", 2556, 2604, -5832, -5800, "z", (-5832, -517), (-5800, -517)),
    ("RampFenceSouth", 2556, 2604, -5936, -5832, "z", (-5936, -592), (-5832, -517)),
]
# The other volumes: BlueWater0 is a 10 LT jet of water the steam valve pushes down a pipe (TM_SteamWater.scr) and
# `molten steel0` (Kato, Lava1.spr) the refinery's crucible: not built (README, Deviations).

# Perception hints (PerceptionBrush0-14, PerceptionValue 8): the red glow on the hard rock, the slag hatch and the
# spiked barricades.
PERCEPTION_TEXTURE = "sprites\\perception.spr"
PERCEPTION_COG = 300
PERCEPTION_SKILL = 29
PERCEPTION_OPACITY = 0.35
# MM9's animated surfaces (.spr and sprite-texture sequences): the thjorad ore glints (thjoradspriteb1/c1, 1 240 faces),
# the twinkles, the refinery's tank.
ANIMATED = ["sprites\\perception.spr", "sprites\\twinkle3.spr", "sprites\\twinkle2.spr", "sprites\\thjoradtank.spr",
            "spritetextures\\thjorad\\thjoradspriteb1.dtx", "spritetextures\\thjorad\\thjoradspritec1.dtx"]
FRAME_FLAGS = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}

# --- Events, timers, groups, cogs -------------------------------------------------------------------------------------
EV_LOAD = 1
EV_LOCKED, EV_HANDLE, EV_GATE0, EV_GATE1 = 60, 61, 62, 63
EV_BAR = {"BarWall0": 64, "BarWall1": 65, "ABDoorBoards0": 66}
EV_FALLBOARD, EV_VALVE, EV_SLAG_HATCH = 67, 68, 69
SPIKES = {f"Spike{k}": ("ABDoorBoards0" if k < 6 else "BarWall1" if k < 12 else "BarWall0") for k in range(18)}
EV_SPIKE = {name: 70 + k for k, name in enumerate(SPIKES)}
ROCKS = [f"db{k}" for k in range(12, 24)]
EV_ROCK = {name: 90 + k for k, name in enumerate(ROCKS)}
ROCK_HINT = {"db12": "PerceptionBrush4", "db13": "PerceptionBrush10", "db14": "PerceptionBrush5",
             "db15": "PerceptionBrush1", "db16": "PerceptionBrush3", "db17": "PerceptionBrush11",
             "db18": "PerceptionBrush7", "db19": "PerceptionBrush2", "db20": "PerceptionBrush12",
             "db21": "PerceptionBrush9", "db22": "PerceptionBrush6", "db23": "PerceptionBrush8"}
ROCKS_NEEDED, KEY_ROCK, ROCK_EXPERIENCE = 10, 36, 5000          # dw: tm_hardrock.scr ScriptParams "10 36 5000"
KEY_CAVEIN, CAVEIN_EXPERIENCE = 35, 5000                         # CaveInControl: "1 35 5000"
EV_CAVEWALL = {f"CaveWall{k}": 102 + k for k in range(5)}
EV_STALACTITE, EV_TORCH0, EV_TORCH1, EV_MINECART = 107, 108, 109, 110
# MM9's Off messages to the red PerceptionLights (scene pulsing lights, dungeon/lights.py perception_lights; the shared
# Lua shows them to a perceptive party), by the object whose handler sends them: ABDoorBoards0's and FallingBoard0's
# and SteamValve0's OpenTriggers, TorchHolder0's DeathTrigger TorchTrigger0, the stalactite's DamageTrigger
# plightofftrigger, MCarBlocker1's DeathTrigger, TorchHolder1's DamageTrigger.
LIGHTS_OFF = {"ABDoorBoards0": ["PerceptionLight2", "PerceptionLight3"], "FallingBoard0": ["PerceptionLight5"],
              "SteamValve0": ["PerceptionLight4"], "TorchHolder0": ["PerceptionLight6"],
              "DestructableBrush0": ["PerceptionLight7", "PerceptionLight8", "PerceptionLight9"],
              "MCarBlocker1": ["PerceptionLight1"], "TorchHolder1": ["PerceptionLight0"]}
EV_BUSTOUT = {"BustOutBrush0": 111, "BustOutBrush1": 112, "BustOutBrush2": 113}
EV_SLAG, EV_SLAGBASE = 130, 131
# MM9's breakable brushes (scene destructibles, overrides.yml `motion: break`): the destroyed event of each that has no
# event of its own above (the rocks: EV_ROCK, TorchHolder0: EV_TORCH0, the stalactite's holder: EV_STALACTITE); each sets
# the map variable Broken<name> and runs its DeathTrigger's consequence
BROKEN = {name: 210 + k for k, name in enumerate(
    [*[f"CaveWall{k}" for k in range(5)], "CaveIn", "ABMineBoards0", "ABMineBoards1", "ABMineBoards2", "ABMineBoards3",
     "MCarBlocker1", "TorchHolder1", "BustOutBrush0", "BustOutBrush1", "BustOutBrush2"])}
EV_PLAIN = {"RotatingDoor61": 170, "RotatingDoor62": 171, "RotatingDoor63": 172}   # plain doors (PushOpen, Sticky)
EV_LETTERS = {"Sign0": (120, 572), "Sign1": (121, 571), "Sign2": (122, 574), "Sign3": (123, 573),
              "Sign4": (124, 573), "Sign5": (125, 426), "Sign6": (126, 486), "Sign7": (127, 487)}
EV_CAVEIN, EV_HARDROCK = 140, 141
SPAWN_TRIGGERS = ["TriggerLocation0", "TriggerLocation1A", "TriggerLocation1B", "TriggerLocation1C",
                  "TriggerLocation2A", "TriggerLocation2B", "TriggerLocation3A", "TriggerLocation3B",
                  "TriggerLocation3C", "TriggerLocation4A", "TriggerLocation4B", "TriggerLocation4C",
                  "TriggerLocation5A", "TriggerLocation5B", "TriggerLocation5C", "TriggerLocation6A",
                  "TriggerLocation6B", "TriggerLocation6C"]
EV_SPAWN = {name: 150 + k for k, name in enumerate(SPAWN_TRIGGERS)}
SPAWN_CAP = 10                      # SpawnMgr.scr :SpawnCreature: no spawn once ten of its creatures died
DAMAGE_HOOK, KILL_HOOK = 196, 197              # clear of the rocks' click events (90-101)
T_POLL, T_BARRELS, T_CART, T_VALVE, T_HINTS, T_QUAKE = 201, 203, 204, 205, 206, 207   # 202: Ebora's old timer
T_REFINERY = 208                    # handletrigger05 locked until switch05 closes (its CloseWaitTime)
GROUP_CIVILIANS, GROUP_EBORA, GROUP_BUSTOUT, GROUP_CATS = 1, 2, 3, 4
SPAWN_GROUP0 = 10                   # SpawnMarker k's hidden troglodytes: group 10 + k
# Cogs (SetSprite keys) of the decorations the script shows and hides.
COG = {"slag": 400, "slag_whole": 401, "MineCarA": 402, "MineCarA_end": 403}
# TM_MineCarA.scr :MoveToMarker: MoveToPos MCarAMarker0 at 100 (LT/s), PlaySoundHandle Gears02.wav (radius 2500, looped,
# volume 70) until :StopHere's KillSound. The loop is a scene ambient sound keyed by the cart's DAT index (switched by
# the map variable AmbientSound<key>) at the track's middle.
CART_SPEED_LT, CART_SOUND_RADIUS_LT, CART_SOUND_VOLUME = 100.0, 2500.0, 70.0
# TM_TorchFlame.scr :StartSequence, :Barrel1 .. :Barrel8: DB_Barrel0..8 destroyed one after another (Exploding
# destructibles: the shared explode(), dungeon/objects.py), each after the wait before it; :StopHere waits 3 s first
BARREL_CHAIN = [f"DB_Barrel{k}" for k in range(9)]
BARREL_WAITS = [3.0, 1.0, 0.5, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1]     # seconds before DB_Barrel0 .. DB_Barrel8
# RUDE dialogue actors (NPCs, by DAT object): their RUDE id is NPCNbr (NPC7.scr etc. DoRude), as the old import's.
NPC_RUDE = {"CommonerDwarfMaleB4": 7, "CommonerDwarfMaleB1": 8, "CommonerDwarfMaleB0": 9, "CommonerDwarfMaleB2": 11,
            "DwarvenMiner0": 428, "DwarvenMiner1": 428, "DwarvenMiner2": 428, "DwarvenMiner3": 428,
            "DwarvenMiner4": 428, "DwarvenMiner5": 428}
NPC_ROW = 323                       # a dwarf commoner, the old import's row for the miners (DwarvenMiner0/3 have no record)
# DwarvenMiner.scr ("<mine marker> <dump marker>"): :GoMine attaches the axe (AttachProp dwarfaxe.abc on RHand1) and
# walks to the mine marker; :StartMine faces it and draws 0-9: 0 rub_beard, 1 rock, 3 :GoDump (the axe put away, a
# walk to the dump marker, faces it, dump, back to :GoMine), else hammer; each clip played once, then draws again.
# As a routine (scene mm9_ai.routines, devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md section 4 item 9): the
# 1 in 10 trip, else one of the nine other draws. FaceObject from WalkTo's 10 LT is the way it came.
MINER_DRAWS = ["hammer"] * 7 + ["rock", "rub_beard"]
MINER_DUMP_CHANCE = 0.1
MINER_CLEARANCE_LT = 24             # a miner's stand off the rock face (his body's 16 LT radius and a margin)
MINER_AXE = {"model": "worlds/mm9/models/mm9_item_dwarfaxe.glb", "node": "Socket_RHand1"}
# NPC8.scr (Gudrek) and NPC9.scr (Ketil) :Main: AttachProp MonkHammer.ABC on RHand1, for good (no loop: their p1 is "").
HAMMER_NPCS = {"npc8.scr", "npc9.scr"}
MONK_HAMMER = {"model": "worlds/mm9/models/mm9_item_monkhammer.glb", "node": "Socket_RHand1"}
EBORA_ROW, CAT_ROW = 9301, 9294
KEY_PAID, KEY_SHOWN = 362, 364                                   # NPC7.scr: paid Hjarrand / he showed the machine
KEY_EXTRACTOR, KEY_FIXED = 9512, 37                              # SlagExtractor.scr
ITEM_BROKEN, ITEM_REPLACEMENT, FIX_EXPERIENCE = 398, 399, 5000
KEY_LEAD, KEY_LED = 9510, 9511                                   # NPC8.scr: Gudrek leads the party to Marker3
EV_HJARRAND_ARRIVE, EV_GUDREK_ARRIVE = 180, 181                  # their evt.MoveActorTo arrivals
LEAD_DISTANCE = 655                 # NPC8.scr OnTargetBeyondDist / OnTargetWithinDist 256 LT
HJARRAND_PAUSE = 12                 # polls (0.25 s) at a stop: his clip (RubBeard 2.4 s, X 3.0 s) and :OnArrive2's .5 s
EBORA_WORDS = '{}: "{}"'.format(*speaker_line(8))          # EboraMines.scr RollOverText 8 (MMIXSCRIPTTEXT.csv)

# --- Cinematics and quakes (devdocs/mm9_rework/MM9_CUTSCENES.md; README "Cinematics") --------------------------------
STEM = "thjoradmine"
CINEMA_ID, CINEMA_EVENTS = "ebora_free", 36000          # done event 36000, steps 36001..
# The EarthQuake objects the barricades, boards and the stalactite trigger (their senders' handlers call quake()):
# DBEffectsTrigger0-5 are relays (no party reaches their 50 LT boxes, 220-760 LT over the floor) that the boards and
# barricades trigger on breaking or opening: ABMineBoards0 -> 0, ABDoorBoards0 -> 1, ABMineBoards2 -> 3, BarWall1 -> 4,
# BarWall0 -> 5; DBEffectsTrigger2 has no sender (FallingBoard0 triggers its DBQuakeObject2 itself). The Stalagtite
# door sends TunnelQuake2 On when it falls.
QUAKE_OBJECTS = [f"DBQuakeObject{k}" for k in range(6)] + ["TunnelQuake2"]
# ThjoradQuake.scr on QuakeObject: every 300-600 s a quake at the party of 3-8 s at ShakeAmount 2-5 (DecayRate 1).
# MM9 set its InnerRadius to 0, so it never fired there (MM9_CUTSCENES.md section 1); here it does, as designed.
AMBIENT_QUAKE = {"every": (300, 600), "duration": (3, 8), "amount": (2, 5), "decay": 1.0}


def quake_shake(amount: float, duration: float, decay: float) -> tuple[float, float]:
    """MM9_CUTSCENES.md section 5: an EarthQuake's (intensity, seconds) for evt.CameraShake."""
    amplitude = min(float(amount), 12.0)
    return round(amplitude / 12.0, 3), round(float(duration) + amplitude / float(decay), 2)


def quakes_lua() -> list[str]:
    """QUAKES (each object's intensity, seconds, native point and OuterRadius) and quake(name), the ambient quake."""
    objects, frame = cutscenes.Objects.load(STEM), cutscenes.Frame(PROJECT)
    rows = []
    for name in QUAKE_OBJECTS:
        v = objects.named(name)["values"]
        intensity, seconds = quake_shake(v["ShakeAmount"], v["QuakeDuration"], v["DecayRate"])
        x, y, z = (int(round(c)) for c in frame.point(v["Pos"]))
        rows.append(f"{name} = {{{intensity}, {seconds}, {x}, {y}, {z}, {int(round(v['OuterRadius'] * cutscenes.SCALE))}}}")
    q = AMBIENT_QUAKE
    return [
        "-- MM9's EarthQuake objects as camera shakes (MM9_CUTSCENES.md section 5): intensity ShakeAmount / 12, seconds",
        "-- QuakeDuration + ShakeAmount / DecayRate, felt within OuterRadius of the object (MM9's range has no falloff).",
        f"local QUAKES = {{{', '.join(rows)}}}",
        "local function quake(name)",
        "    local q = QUAKES[name]",
        "    evt.CameraShake(q[1], q[2], q[3], q[4], q[5], q[6], q[6])",
        "end",
        f"-- ThjoradQuake.scr (QuakeObject): every {q['every'][0]}-{q['every'][1]} s a quake at the party, "
        f"{q['duration'][0]}-{q['duration'][1]} s at ShakeAmount {q['amount'][0]}-{q['amount'][1]}.",
        f"handlers[{T_QUAKE}] = function()",
        f"    local amount = evt.RandomBetween({q['amount'][0]}, {q['amount'][1]})",
        f"    evt.CameraShake(amount / 12, evt.RandomBetween({q['duration'][0]}, {q['duration'][1]}) + amount / "
        f"{q['decay']:g})",
        f"    evt.StartTimer({T_QUAKE}, seconds(evt.RandomBetween({q['every'][0]}, {q['every'][1]})))",
        "end",
    ]


def ebora_scenes(ebora_actor: int) -> list:
    """EboraMines.scr :FreeAtLast as the cinematic ebora_free (13 s, fixed waits): EboraCam (EboraCam1.scr :CameraOn
    snaps it to face Ebora; MM9 never aims it otherwise), Ebora turns to the camera at 180 degrees a second (FaceObject
    EboraCam 180), fidget2 (Wait 3), Taunt with RollOverText 8 for 7 s (Wait 5), Rattack1 (EBORA.abc has none: its
    ranged attack, Castspell = AttackRanged; Wait 2), the column of fire and column03.wav (Wait 3), RemoveObject.
    The overloaded :FreeAtLast's ScreenFadeIn 1 undoes its turn-based guard's fade out only: no fade here."""
    objects, frame = cutscenes.Objects.load(STEM), cutscenes.Frame(PROJECT)
    eye, forward = frame.camera(objects, "EboraCam")
    ebora = frame.point(objects.named("Ebora")["values"]["Pos"])
    aim, _ = cutscenes.face_toward(forward, eye, ebora, 0.0, 0.0)
    # Ebora's turn: from her DAT yaw to the camera at 180 degrees a second.
    _, turn_seconds = cutscenes.face_toward(frame.direction(objects.named("Ebora")["values"].get("Rotation")), ebora,
                                            eye, 180.0, 0.0)
    scene = cutscenes.Scene(CINEMA_ID, CINEMA_EVENTS, source="EboraMines.scr :FreeAtLast, EboraCam1.scr")
    cinema = scene.cinema
    cinema.fixed(13.0, eye, direction=aim, fov=cutscenes.MM9_CAMERA_FOV, note="EboraCam (FaceObject Ebora 0)")
    cinema._cue(0.0, "FaceObject EboraCam 180", actor=ebora_actor, action="face",
                look_at=[round(c, 1) for c in eye], seconds=round(turn_seconds, 2))
    cinema._cue(0.0, "PlayAnim fidget2", actor=ebora_actor, action="clip", clip="Fidget2", loop=False)
    cinema._cue(3.0, "OnFidgetDone: PlayAnim Taunt", actor=ebora_actor, action="clip", clip="Taunt", loop=False)
    cinema.subtitle(3.0, EBORA_WORDS, 7.0, note="RollOverText 8, 2, 7000 (MMIXSCRIPTTEXT.csv)")
    cinema._cue(8.0, "Disappear: PlayAnim Rattack1", actor=ebora_actor, action="clip", clip="AttackRanged",
                loop=False)
    cinema.sound(10.0, "sounds\\spells\\column03.wav", note="SpellDone")
    ex, ey, ez = (int(round(c)) for c in ebora)
    scene.step(10.0, "fire", "\n".join([
        f'evt.SpawnWorldEffect("mm9:column_of_fire", {ex}, {ey}, {ez}, 1)',
        'set("EboraFree", 3)']), note="SpellDone: DoClientFX spell-column of fire")
    scene.step(13.0, "removed", "\n".join([f"MM9.removeActor({ebora_actor})", 'set("EboraFree", 4)']),
               note="EboraDone: RemoveObject, LetterBox 0, EboraCam Off")
    return [scene]


def rude_exit_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a dialogue with actor object `index` runs when it closes."""
    return 50000 + index


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


def in_air(polygons: list, x: float, y: float, z: float) -> bool:
    """Whether (x, y, z) LT lies in air: the first polygon straight above faces down (Dook's Castle's)."""
    best, facing = None, False
    for polygon in polygons:
        low, high = polygon.bounds
        if not (low[0] <= x <= high[0] and low[2] <= z <= high[2]) or high[1] < y:
            continue
        n = polygon.normal
        if abs(n[1]) < 1e-6:
            continue
        hit = y + float(np.dot(polygon.points[0] - np.array([x, y, z]), n)) / n[1]
        if hit < y or (best is not None and hit >= best):
            continue
        ring = polygon.points[:, [0, 2]]
        edges = np.roll(ring, -1, axis=0) - ring
        cross = edges[:, 0] * (z - ring[:, 1]) - edges[:, 1] * (x - ring[:, 0])
        if (cross >= -1e-6).all() or (cross <= 1e-6).all():
            best, facing = hit, n[1] < 0
    return best is not None and facing


def surface(points_xz, y: float, texture: str, width: int, height: int, model: str, role: str) -> Polygon:
    """A horizontal face over a ring of (x, z) points, front upward, mapped one texel per LT."""
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture,
                      (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), 0x1088, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, polygon.mapping, 0x1088,
                          model, role)
    polygon.notes.update(width=width, height=height)
    return polygon


class ThjoradMine(dungeon.Hooks):
    generator = "mm9r_thjoradmine"
    mover_events = {
        "Door2": (EV_LOCKED, "click"),
        "handletrigger05": (EV_HANDLE, "click"), "slidingdoor05": (EV_HANDLE, "click"),
        "Switch2": (EV_GATE0, "click"), "Switch3": (EV_GATE0, "click"),
        "Switch4": (EV_GATE1, "click"), "Switch5": (EV_GATE1, "click"),
        **{name: (event, "click") for name, event in EV_BAR.items()},
        "FallingBoard0": (EV_FALLBOARD, "click"), "SteamValve0": (EV_VALVE, "click"),
        "RotatingDoor0": (EV_SLAG_HATCH, "click"),
        **{name: (event, "click") for name, event in EV_SPIKE.items()},
        "FallingWallTorch0": (EV_TORCH0, "click"), "FallingWallTorch1": (EV_TORCH1, "click"),
        **{name: (event, "click") for name, event in EV_PLAIN.items()},
    }

    def destructible_events(self, build) -> dict:
        """The breakable brushes' destroyed and damaged events (dungeon/destructibles.py): the rocks', TorchHolder0's
        (the falling torch), the stalactite holder's and BROKEN; ABMineBoards0's DamageTrigger knocks FallingWallTorch1
        loose (EV_TORCH1)."""
        events = {name: (event, 0) for name, event in EV_ROCK.items()}
        events.update({name: (event, 0) for name, event in BROKEN.items()})
        events.update({"TorchHolder0": (EV_TORCH0, 0), "DestructableBrush0": (EV_STALACTITE, 0),
                       "ABMineBoards0": (BROKEN["ABMineBoards0"], EV_TORCH1)})
        return events

    # --- geometry -------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        """DirtyWater1's surface, cut to the cavern on a 64 LT grid (a tile is wet where any of nine samples is in air)."""
        source = build.source
        points = np.array(source.models[POOL_MODEL].points, float)
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        alias = source.aliases[POOL_TEXTURE]
        self.pool_y = y = float(points[:, 1].max())
        for polygon in polygons:
            polygon.bounds = (polygon.points.min(0), polygon.points.max(0))
        out, self.pool_faces = list(polygons), 0
        invisible = next(p for p in polygons if p.role == "invisible")
        for name, rx0, rx1, rz0, rz1, axis, low, high in RAMPS:
            def height(x, z, axis=axis, low=low, high=high):
                t = ((z if axis == "z" else x) - low[0]) / (high[0] - low[0])
                return low[1] + t * (high[1] - low[1])
            ring = np.array([[x, height(x, z), z] for x, z in ((rx0, rz0), (rx0, rz1), (rx1, rz1), (rx1, rz0))], float)
            ramp = Polygon(ring, [tuple(np.round(q, 1)) for q in ring], invisible.texture, invisible.mapping,
                           invisible.flags, name, "invisible")
            if ramp.normal[1] < 0:
                ramp = Polygon(ring[::-1].copy(), [tuple(np.round(q, 1)) for q in ring[::-1]], invisible.texture,
                               invisible.mapping, invisible.flags, name, "invisible")
            ramp.notes.update(invisible.notes)
            out.append(ramp)
        for row in np.arange(z0, z1, POOL_TILE):
            run = None
            for column in np.arange(x0, x1 + POOL_TILE, POOL_TILE):
                wet = column < x1 and any(in_air(polygons, column + u * POOL_TILE, y + 1, row + v * POOL_TILE)
                                          for u in (0.02, 0.5, 0.98) for v in (0.02, 0.5, 0.98))
                if wet and run is None:
                    run = column
                elif not wet and run is not None:
                    top = min(row + POOL_TILE, z1)
                    out.append(surface([(run, row), (run, top), (column, top), (column, row)], y, POOL_TEXTURE,
                                       alias["width"], alias["height"], POOL_MODEL,
                                       "nonsolid" if water.swimming(build.project) else "static"))
                    self.pool_faces += 1
                    run = None
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        events = {name: event for name, (event, _) in EV_LETTERS.items()}
        events.update({"slag": EV_SLAG, "slag_whole": EV_SLAG, "WorldObject0": EV_SLAGBASE, "MineCarA": EV_MINECART})
        self.placed = set()
        if PROPS.exists():
            entries = json.loads(PROPS.read_text())
            self.placed = {e["source_name"] for e in entries}
            content.props(PROPS, events=events, cogs={k: v for k, v in COG.items() if k in self.placed})
            cart = next((e for e in entries if e["source_name"] == "MineCarA"), None)
            if cart is not None:
                # TM_MineCarA.scr: hit, the cart rolls to MCarAMarker0 (MoveToPos at CART_SPEED_LT). It glides there
                # (evt.MoveDecoration, drawn only: its collision stays home), then a second cart standing hidden on the
                # floor at the marker takes its place, so the cart blocks the track at its end and not at its start.
                m = source.properties("MCarAMarker0")["Pos"]
                floor = content.floor_at(m[0], m[2], m[1] + 40)
                position = project.native([m[0], floor, m[2]])
                end = content.entity("MineCarA_end", cart["decoration"], position, cart["yaw_degrees"],
                                     primary=COG["MineCarA_end"])
                self.placed.add("MineCarA_end")
                start = next(e for e in content.report["decorations"] if e["anchor"] == "MineCarA")
                self.cart_glide = [b - a for a, b in zip(start["position"], end["position"])]
                self.cart_seconds = round(float(np.linalg.norm(self.cart_glide)) / (CART_SPEED_LT * cutscenes.SCALE), 2)
                self.cart_sound_key = int(cart["source_object"])
        else:
            print("note: props.json is missing; no decorations or chests placed")
        # MM9's touch Triggers as boxes polled four times a second (Chasm's, Dook's Castle's route).
        self.boxes = {}
        for name, event in [("Trigger7", EV_CAVEIN), ("TriggerHardRock", EV_HARDROCK), *EV_SPAWN.items()]:
            p = source.properties(name)
            centre, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
            low, high = project.native(centre - dims), project.native(centre + dims)
            self.boxes[name] = (event, [np.minimum(low, high).round().astype(int).tolist(),
                                        np.maximum(low, high).round().astype(int).tolist()])
        self.points = {}
        for name in ("MMarker1", "MMarker2", "MMarker3", "Machine", "slag", "Marker3", "FallingTorchMarker0", "FallingTorchMarker1", "MCarAMarker0",
                     "Ebora", *[f"DustObject{k}" for k in range(6, 18)], "DustObject2", "DustObject3",
                     "PressuredWater0", "DustObject4", "DustObject0", "DustObject1", "DustObject18", "DustObject19",
                     "DustOjbect5" if source.by_name.get("dustojbect5") else "DustObject5"):
            p = source.properties(name)["Pos"]
            self.points[name] = project.native(p).round().astype(int).tolist()
        for name in ("MMarker1", "MMarker2", "MMarker3", "Machine", "Marker3"):   # the dwarves' walks end on the floor
            p = source.properties(name)["Pos"]
            floor = content.floor_at(p[0], p[2], p[1] + 40)
            self.points[name] = project.native([p[0], floor, p[2]]).round().astype(int).tolist()
        self.place_perception_hints(build)
        self.scale_lights(build)
        content.report["omitted"] += [
            {"anchor": "Bin2", "class": "Prop", "reason": "Mine.scr exits at once (TELP 1.3 de-activated it)"},
        ]

    def scale_lights(self, build) -> None:
        """MM9 weights each Light by its BrightScale: the mine's lanterns (255/255/128) at 0.75, the old halls' and the
        north tunnels' orange lamps (230/164/26) at 0.2-0.5. The shared converter writes the colour as authored, which
        made the orange lamps 1.5-3.75 times too strong against the lanterns: the north-west halls baked 1.57 times
        MM9's lightmaps and far too orange (README, Baked lighting). The BLV lights carry colour x BrightScale / 0.75 (the
        lanterns as authored, so the model lighting keeps light_scale 1 for them)."""
        scale = {light["name"]: light["bright_scale"] for light in build.lights}
        for record in build.package.metadata["lights"]:
            factor = min(1.0, scale.get(record["id"], LANTERN_SCALE) / LANTERN_SCALE)
            record["color"] = [int(round(c * factor)) for c in record["color"]]
        for light in build.lights:
            light["colour_in_blv"] = [int(round(c * min(1.0, light["bright_scale"] / LANTERN_SCALE)))
                                      for c in light["colour"]]

    def place_perception_hints(self, build) -> None:
        """Each PerceptionBrush's visible polygons as untouchable translucent faces with a cog (Drangheim Prison's)."""
        package, source = build.package, build.source
        self.hints, self.hint_faces = {}, 0
        difficulties = perception_difficulties_by_model_name(source.world)
        names = sorted(difficulties, key=lambda n: int(n[len("perceptionbrush"):]))
        self.hint_difficulty = max(difficulties[n] for n in names)
        for lower in names:
            name = next(model for model in source.models if model.lower() == lower)
            k = int(lower[len("perceptionbrush"):])
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
    def miner_routine(self, build, monster_id: int, mine: str, dump: str) -> list:
        """DwarvenMiner.scr as a routine (MINER_DRAWS): to the mine marker with the axe, a clip, and 1 in 10 a trip
        without it to the dump marker."""
        seconds = lua.model_clip_seconds(monster_id)
        mine_lt, dump_lt = (np.asarray(build.source.properties(name)["Pos"], float) for name in (mine, dump))
        points = []
        for target, other in ((mine_lt, dump_lt), (dump_lt, mine_lt)):
            # The mine markers stand inside the rock face (MM9's WalkTo stops at it): the first floor from the marker
            # back toward the other one, MINER_CLEARANCE_LT further from the face.
            way = other - target
            way[1] = 0.0
            length = float(np.linalg.norm(way))
            for t in np.arange(0.0, length, 4.0):
                spot = target + way / length * t
                if build.content.floor_at(spot[0], spot[2], target[1] + 24) is not None:
                    break
            else:
                raise SystemExit(f"{mine}/{dump}: no floor between them")
            if t > 0:
                spot = target + way / length * min(length, t + MINER_CLEARANCE_LT)
            floor = build.content.floor_at(spot[0], spot[2], target[1] + 24)
            points.append(build.project.native([spot[0], floor, spot[2]]).round().astype(int).tolist())
        (mx, my, _), (dx, dy, _) = points
        to_mine = round(float(np.degrees(np.arctan2(my - dy, mx - dx))) % 360.0, 1)
        to_dump = round((to_mine + 180.0) % 360.0, 1)
        return [{"items": "show"}, {"walk": points[0]}, {"face": to_mine},
                {"clips": [{"clip": clip, "seconds": round(seconds[clip], 2)} for clip in MINER_DRAWS]},
                {"chance": MINER_DUMP_CHANCE, "steps": [
                    {"items": "hide"}, {"walk": points[1]}, {"face": to_dump},
                    {"clip": "dump", "seconds": round(seconds["dump"], 2)}]}]

    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        content.report["omitted"] = [o for o in content.report["omitted"]
                                     if o["anchor"] not in NPC_RUDE and o["class"] not in ("SuccEbora", "Cat")]
        descriptors = {int(cells[0]): (int(cells[2]), int(cells[3])) for cells in
                       (line.split("\t") for line in DESCRIPTORS.read_text(encoding="latin-1").splitlines())
                       if cells and cells[0].isdigit()}
        # the old import's records by DAT object (the installed scene also holds pack-grown copies, which name none)
        old = {a["mm9_source_object_index"]: a for a in
               yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]
               if "mm9_source_object_index" in a}
        troglodyte = next(b for n, b in bases.items() if b["name"] == "Troglodyte")
        out, self.actor, self.objects = [], {}, {}
        self.spawned, self.gnolls = {}, []
        for o in source.objects:
            if o["class"] not in build.project.monster_classes:
                continue
            name, p, cls = o["name"], o["properties"], o["class"]
            scale = float(p.get("Scale", 1.0) or 1.0)
            group, friendly, changes, dormant = 0, False, {}, False
            if name in bases:
                base = bases[name]
                changes = placed_body(base["monster_id"], p)    # MM9's body: the row's, or at the DAT's own Scale
                if "kingkong" in str(p.get("ScriptName", "")).lower():
                    group, dormant = GROUP_BUSTOUT, True          # KingKong.scr: waits in its cage for ForceBreak
            else:
                if name in NPC_RUDE:
                    # The old import left out two of the six miners (DwarvenMiner0/3): MM9's own name for them.
                    record = old.get(o["index"], {"name": "Peasant", "hp": 6, "monster_id": NPC_ROW})
                    row = record.get("monster_id", NPC_ROW)     # the old import's dwarf rows (322, 323, 325)
                    group, friendly = GROUP_CIVILIANS, True
                elif cls == "SuccEbora":
                    record, row = {"name": "Ebora", "hp": 1}, EBORA_ROW
                    group, friendly = GROUP_EBORA, True
                elif cls == "Cat":
                    record, row = old.get(o["index"], {"name": "Cat", "hp": 3}), CAT_ROW
                    group, friendly = GROUP_CATS, True
                else:
                    continue
                height, radius = descriptors.get(row, (record.get("height", 85), record.get("radius", 42)))
                base = {"name": record["name"], "attributes": 0, "hp": max(1, int(record.get("hp", 1))),
                        "hostility_type": 0, "monster_info_id": row, "monster_id": row, "radius": radius,
                        "height": height, "move_speed": record.get("move_speed", 0)}
            # AB_Troglodyte24 and the mine-cart chest stand sunk into the floor (seed_exclude): query from higher up.
            query = p["Pos"][1] + (96 if name == "AB_Troglodyte24" else 24)
            actor = content.actor(o, base, sector_of_room, group=group, friendly=friendly, floor_query_lt=query,
                                  **changes)
            actor["mm9_source_object_index"] = o["index"]
            if name in NPC_RUDE:
                actor["mm9_rude_id"] = NPC_RUDE[name]
                actor["immobile"] = True
                script = str(p.get("ScriptName", "")).lower().replace("scripts\\", "")
                if script == "dwarvenminer.scr":
                    actor["immobile"] = False              # a routine walker
                    actor.setdefault("mm9_ai", {})["routines"] = {
                        "default": self.miner_routine(build, actor["monster_id"], *str(p["ScriptParams"]).split())}
                    actor["held_items"] = [dict(MINER_AXE)]
                elif script in HAMMER_NPCS:
                    actor["held_items"] = [dict(MONK_HAMMER)]
            if cls == "SuccEbora":
                actor["immobile"] = True                       # EboraMines.scr: SetIdle until FreeAtLast
            if dormant:
                actor["dormant"] = True
                self.gnolls.append(actor["actor_index"])
            self.actor[name] = actor["actor_index"]
            self.objects[name] = o["index"]
            out.append(actor)
        # SpawnMgr.scr: each TriggerLocation sends `spawn` to its SpawnLoc (SpawnMarker<k>), which has the manager spawn
        # one Troglodyte there that hunts the party (SpawnCreature.scr); TriggerLocation0 sends it three times. Hidden
        # placed troglodytes at each marker, one per `spawn`, shown and set hostile by the map script.
        template = next(o for o in source.objects if o["name"] == "Troglodyte0")
        count = {}
        for trigger in SPAWN_TRIGGERS:
            marker = "SpawnMarker" + trigger[len("TriggerLocation")]
            count[marker] = count.get(marker, 0) + (3 if trigger == "TriggerLocation0" else 1)
        for marker, n in count.items():
            pos = source.properties(marker)["Pos"]
            group = SPAWN_GROUP0 + int(marker[-1])
            for k in range(n):
                angle = 2 * np.pi * k / max(n, 1)
                spot = [pos[0] + 24 * np.cos(angle), pos[1], pos[2] + 24 * np.sin(angle)]
                if content.floor_at(spot[0], spot[2], pos[1] + 40) is None:
                    spot = list(pos)                               # a narrow tunnel: all on the marker
                clone = dict(template, name=f"{marker}Troglodyte{k}",
                             properties=dict(template["properties"], Pos=spot,
                                             Scale=1.0, Rotation=source.properties(marker)["Rotation"]))
                record = content.actor(clone, troglodyte, sector_of_room, group=group, hidden=True,
                                       floor_query_lt=pos[1] + 40)      # Scale 1: the row's body
                self.spawned.setdefault(marker, []).append(record["actor_index"])
                out.append(record)
        return out

    # --- scene ------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """The perception hints at their brushes' Alpha, two-sided; the animated MM9 surfaces' frames."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        alias = build.source.aliases[PERCEPTION_TEXTURE]["alias"].lower()
        hints = sorted(f["index"] for f in blv["faces"] if str(f.get("texture_name", "")).lower() == alias)
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        scene.setdefault("translucent_faces", []).append(
            {"faces": hints, "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        if hasattr(self, "cart_glide"):
            # the cart's Gears02.wav loop (CART_SPEED_LT), off until the map Lua switches it on for the ride; inner
            # radius a quarter of MM9's, as the fires' (ambient.fire_sounds)
            start = next(e for e in build.content.report["decorations"] if e["anchor"] == "MineCarA")
            middle = [round(a + d / 2) for a, d in zip(start["position"], self.cart_glide)]
            radius = CART_SOUND_RADIUS_LT * cutscenes.SCALE
            scene.setdefault("ambient_sounds", []).append(
                {"key": self.cart_sound_key, "sound": "events/gears02.wav", "position": [*middle[:2], middle[2] + 48],
                 "inner_radius": round(radius / 4), "outer_radius": round(radius),
                 "volume": ambient.ambient_volume(CART_SOUND_VOLUME), "loop": True, "start_on": False})
        if build.project.install:
            # The old map's outdoor overlay (thjoradmine_authored.scene.yml, kind outdoor_scene_overlay) would be read
            # as the BLV's indoor overlay and fail the load, and its Lua (thjoradmine_authored.lua) would be appended to the
            # map's and replace its handlers: the shared OLD_SIDECARS list names neither.
            review_root.remove(Path("worlds/mm9/maps") / f"{build.project.stem}_authored.scene.yml")
            review_root.remove(Path("worlds/mm9/events/maps") / f"{build.project.stem}_authored.lua")
            for texture in ANIMATED:
                if texture in build.source.aliases and build.source.aliases[texture].get("animation_frames"):
                    self.install_frames(build, texture)

    def install_frames(self, build, texture: str) -> None:
        """An MM9 .spr as a texture frame sequence in the review root's frame table (Drangheim Prison's)."""
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

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Thjorad Mine")
        script.doors()
        script.chests()
        actor, points, objects = self.actor, self.points, self.objects
        has = lambda name: name in self.placed                                       # noqa: E731
        spawned = ", ".join(f"{m} = {{{', '.join(map(str, ids))}}}" for m, ids in self.spawned.items())
        spawn_actors = ", ".join(f"[{i}] = true" for ids in self.spawned.values() for i in ids)
        hint = self.hints
        names = [*ROCKS, *BROKEN, "TorchHolder0", "DestructableBrush0", *BARREL_CHAIN, "DB_Barrel9"]
        breakable = {n: build.source.by_name[n.lower()]["index"] for n in names}
        L = []
        L += [
            "local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end",
            "local function dust(p, scale) evt.SpawnWorldEffect(\"mm9:smoke\", p[1], p[2], p[3], scale or 1) end",
            "local function hideHint(brush) evt.SetFacetBit(brush, FacetBits.Invisible, true) set(\"HintOff\" .. brush, 1) end",
            f"local function sprite(cog, shown) evt.SetSprite(cog, shown) end",
            "-- MM9's breakable brushes and barrels: scene destructibles by DAT name (evt.DestroyDestructible)",
            "local BREAKABLE = {" + ", ".join(f"{lua.lua_key(n)} = {breakable[n]}" for n in sorted(breakable)) + "}",
            "local function destroy(name) evt.DestroyDestructible(BREAKABLE[name]) end",
            *quakes_lua(),
            "",
            "-- The entrance door (RotatingDoor Door2, Locked 1, no key): it only jiggles (doorlock02.wav); the exit volume",
            "-- stands in front of it.",
            f"handlers[{EV_LOCKED}] = function() sound(\"door/doorlock02.wav\") end",
            "",
            "-- The refinery's sliding door (doorportal05): its handle (handletrigger05, PushOpen) opens switch05, draws both",
            "-- deadbolts and locks itself; switch05's OpenTrigger slides the door open (it shuts after 2.75 s), and switch05",
            "-- unlocks the handle when it closes 10 s later: the door opens again from either side (a click on the door is",
            "-- one on its handle). A map load ends a cycle a save cut short.",
            f"handlers[{EV_HANDLE}] = function()",
            "    if var(\"RefineryBusy\") == 1 then return end",
            "    set(\"RefineryBusy\", 1)",
            "    open(\"handletrigger05_INV\") open(\"deadbolttop05\") open(\"deadboltbottom05\") open(\"switch05\")",
            "    open(\"slidingdoor05\")",
            f"    evt.StartTimer({T_REFINERY}, seconds(10))",
            "end",
            f"handlers[{T_REFINERY}] = function() evt.StopTimer({T_REFINERY}) set(\"RefineryBusy\", 0) end",
            "",
            "-- The lift gates either side of the refinery: Switch2/Switch3 raise and lower Door0 (Portal0), Switch4/Switch5",
            "-- Door1 (Portal1); both levers of a gate swing with it (OpenTrigger/CloseTrigger wiring).",
            f"handlers[{EV_GATE0}] = function() evt.SetDoorState(DOORS.Door0, DoorAction.Trigger) "
            "evt.SetDoorState(DOORS.Switch2, DoorAction.Trigger) evt.SetDoorState(DOORS.Switch3, DoorAction.Trigger) end",
            f"handlers[{EV_GATE1}] = function() evt.SetDoorState(DOORS.Door1, DoorAction.Trigger) "
            "evt.SetDoorState(DOORS.Switch4, DoorAction.Trigger) evt.SetDoorState(DOORS.Switch5, DoorAction.Trigger) end",
            "",
            "-- The spiked barricades (SpikeDoorA.scr on BarWall1, SpikeDoorB.scr on BarWall0, SpikeDoorOpen.scr on",
            "-- ABDoorBoards0): Locked until six BoardSpikes are pulled (BoardSpike.scr: a click, metalwood04.wav, the spike",
            "-- is gone and sends OnePulled); the sixth unlocks and opens it (Sticky). Its OpenTriggers: the barricade locks,",
            "-- DBEffectsTrigger dust and a quake (not built), the perception light off.",
        ]
        effects = {"BarWall0": "DustObject19", "BarWall1": "DustObject18", "ABDoorBoards0": "DustObject1"}
        quakes = {"BarWall0": "DBQuakeObject5", "BarWall1": "DBQuakeObject4", "ABDoorBoards0": "DBQuakeObject1"}
        hints_for = {"BarWall0": "PerceptionBrush13", "BarWall1": "PerceptionBrush14"}
        for wall, event in EV_BAR.items():
            spikes = [s for s, w in SPIKES.items() if w == wall]
            hint_line = f"    hideHint({hint[hints_for[wall]]})" if wall in hints_for and hints_for[wall] in hint else ""
            L += [f"local function pulled{wall}()",
                  "    local n = 0",
                  *[f"    if var(\"{s}\") == 1 then n = n + 1 end" for s in spikes],
                  "    return n",
                  "end",
                  f"local function open{wall}()",
                  f"    if var(\"{wall}Open\") == 1 then return end",
                  f"    set(\"{wall}Open\", 1)",
                  f"    open(\"{wall}\")",
                  f"    dust({{{', '.join(map(str, points[effects[wall]]))}}}, 1.5)" if effects[wall] in points else "",
                  f"    quake(\"{quakes[wall]}\")",
                  hint_line,
                  *([f"    {perception_light_lua(build, light, False)}" for light in LIGHTS_OFF.get(wall, [])]),
                  "end",
                  f"handlers[{event}] = function()   -- {wall}",
                  f"    if pulled{wall}() == {len(spikes)} then open{wall}() else sound(\"door/doorlock02.wav\") end",
                  "end"]
            for s in spikes:
                L += [f"handlers[{EV_SPIKE[s]}] = function()   -- {s}",
                      f"    if var(\"{s}\") == 1 then return end",
                      f"    set(\"{s}\", 1)",
                      "    sound(\"events/metalwood04.wav\")",
                      f"    open(\"{s}\")",
                      f"    if pulled{wall}() == {len(spikes)} then open{wall}() end",
                      "end"]
        L += [f"handlers[{e}] = function() evt.SetDoorState(DOORS.{d}, DoorAction.Trigger) end   -- {d}"
              for d, e in EV_PLAIN.items()]
        L += [
            "",
            "-- The hard rock (DestructableBrushes db12-db23, 1 HP, stonecrumble.wav; DamageTrigger: its PerceptionBrush off;",
            f"-- DeathTrigger: dw OneDown). dw runs tm_hardrock.scr \"{ROCKS_NEEDED} {KEY_ROCK} {ROCK_EXPERIENCE}\": the "
            f"{ROCKS_NEEDED}th block gives key {KEY_ROCK},",
            "-- the quest sound and the experience, and frees Ebora (FreeAtLast). Scene destructibles: the party's weapons",
            "-- break them, a click too (the shared click); these are their destroyed events.",
            "local function rocksBroken()",
            "    local n = 0",
            *[f"    if var(\"{r}\") == 1 then n = n + 1 end" for r in ROCKS],
            "    return n",
            "end",
            "local function freeEbora()   -- FreeAtLast to Ebora: a dead Ebora takes none (MM9.receives)",
            "    if var(\"EboraFree\") ~= 0 then return end",
            f"    if not MM9.receives(\"thjoradmine\", \"Ebora\", \"FreeAtLast\", {self.actor['Ebora']}) then return end",
            "    set(\"EboraFree\", 1)",
            f"    MM9Cinematic.start({lua_string(CINEMA_ID)})",
            "end",
        ]
        for r in ROCKS:
            L += [f"handlers[{EV_ROCK[r]}] = function()   -- {r}",
                  f"    if var(\"{r}\") == 1 then return end",
                  f"    set(\"{r}\", 1)",
                  f"    hideHint({hint[ROCK_HINT[r]]})" if ROCK_HINT[r] in hint else "",
                  f"    if rocksBroken() == {ROCKS_NEEDED} and MM9.hasKey({KEY_ROCK}) == 0 then",
                  f"        MM9.giveKey({KEY_ROCK})",
                  "        MM9.playSound(\"sounds\\\\events\\\\quest.wav\")",
                  f"        {experience_lua(ROCK_EXPERIENCE, KEY_ROCK)}",
                  "        freeEbora()",
                  "    end",
                  "end"]
        L += [
            "-- EboraMines.scr :FreeAtLast (also on damage): the cinematic ebora_free (thjoradmine.cinematics.yml): the",
            "-- camera on her, she taunts and vanishes in a column of fire; its gameplay steps are events 36001-36002.",
            "",
            "-- The cave-in (Trigger7: CaveIn DamageOn, Destroy): the floor over the flooded cavern gives way under the party",
            f"-- (CaveIn's DeathTrigger: CaveInControl OneDown, tm_hardrock.scr \"1 {KEY_CAVEIN} {CAVEIN_EXPERIENCE}\").",
            f"handlers[{EV_CAVEIN}] = function()",
            "    if var(\"CaveIn\") == 1 then return end",
            "    set(\"CaveIn\", 1)",
            "    destroy(\"CaveIn\")",
            "end",
            f"handlers[{BROKEN['CaveIn']}] = function()   -- CaveIn destroyed",
            "    set(\"BrokenCaveIn\", 1)",
            f"    if MM9.hasKey({KEY_CAVEIN}) == 0 then",
            f"        MM9.giveKey({KEY_CAVEIN})",
            "        MM9.playSound(\"sounds\\\\events\\\\quest.wav\")",
            f"        {experience_lua(CAVEIN_EXPERIENCE, KEY_CAVEIN)}",
            "    end",
            "end",
            "",
            "-- The gnolls' cages (TriggerHardRock -> TroglodyteGnoll0-2 ForceBreak, KingKong.scr: dragonredrattack3.wav,",
            "-- the cage wall BustOutBrush<k> destroyed, the gnoll hunts the party). A click on a cage wall breaks it too.",
            "-- Each gnoll breaks only its own wall (ScriptParams p0); a dead one takes no ForceBreak (MM9.receives) and",
            "-- leaves its wall standing. :BreakCage swings at the wall as it breaks (PlayAnim hattack1: the model's",
            "-- attack_melee); their ScriptParams name no ANIM_NAME, so nothing loops while they wait.",
            f"local GNOLLS = {{{', '.join(map(str, self.gnolls))}}}",
            "local BUSTOUT = {" + ", ".join(f"{{\"TroglodyteGnoll{w[-1]}\", {self.actor['TroglodyteGnoll' + w[-1]]}, \"{w}\"}}"
                                         for w in EV_BUSTOUT) + "}   -- gnoll, its actor, its wall",
            "local function bustOut(wall)",
            "    if var(wall) == 1 then return end",
            "    set(wall, 1)",
            "    destroy(wall)",
            "end",
            f"handlers[{EV_HARDROCK}] = function()",
            "    if var(\"BustOut\") == 1 then return end",
            "    set(\"BustOut\", 1)",
            "    for _, g in ipairs(BUSTOUT) do",
            "        if MM9.receives(\"thjoradmine\", g[1], \"ForceBreak\", g[2]) then",
            "            sound(\"animsounds/dragonredrattack3.wav\")",
            "            bustOut(g[3])",
            "            evt.PlayActorClip(g[2], \"attack_melee\")",
            "        end",
            "    end",
            f"    evt.WakeGroup({GROUP_BUSTOUT})",
            f"    evt.SetMonGroupBit({GROUP_BUSTOUT}, MonsterBits.Hostile, true)",
            "end",
            *[f"handlers[{e}] = function() sound(\"events/crate_smash.wav\") bustOut(\"{w}\") end   -- {w}"
              for w, e in EV_BUSTOUT.items()],
            "",
            "-- The cave wall (CaveWall0-4, DestructableBrush, 10 HP each; DeathTrigger: AITrk528 On, an AI rail): weapons",
            "-- break the pieces one by one; a click on any breaks all five.",
            f"handlers[{EV_CAVEWALL['CaveWall0']}] = function()",
            "    if var(\"CaveWall\") == 1 then return end",
            "    set(\"CaveWall\", 1)",
            *[f"    destroy(\"CaveWall{k}\")" for k in range(5)],
            "end",
            "",
            "-- The stalactite (DestructableBrush0, 1 HP; DamageTrigger plightofftrigger: PerceptionLight7-9 off;",
            "-- DeathTrigger: Stalagtite toggle, a Door falling 160 LT at 300 LT/s): its destroyed event.",
            f"handlers[{EV_STALACTITE}] = function()",
            "    if var(\"Stalactite\") == 1 then return end",
            "    set(\"Stalactite\", 1)",
            "    open(\"Stalagtite\")",
            *[f"    {perception_light_lua(build, light, False)}" for light in LIGHTS_OFF["DestructableBrush0"]],
            "    quake(\"TunnelQuake2\")   -- the Stalagtite door's OpenTrigger: TunnelQuake2 On",
            "end",
            "",
        ]
        # The breakable brushes' destroyed events (BROKEN): MM9's DeathTrigger consequences, whoever broke them.
        torch_dust = points.get("DustOjbect5", points.get("DustObject5"))
        consequence = {
            "ABMineBoards0": [f"dust({lua.point(points['DustObject0'])}, 1.5)", "quake(\"DBQuakeObject0\")"],
            "ABMineBoards1": ["sound(\"events/crate_smash.wav\")", f"dust({lua.point(points['DustObject3'])}, 1.5)"],
            "ABMineBoards2": ["quake(\"DBQuakeObject3\")", f"dust({lua.point(points['DustObject16'])}, 1.5)"],
            "ABMineBoards3": [f"dust({lua.point(points['DustObject15'])}, 1.5)"],
            "TorchHolder1": [f"dust({lua.point(torch_dust)}, 0.5)"],
        }
        L += ["-- The breakable brushes' destroyed events (scene destructibles; ABMineBoards0's DBEffectsTrigger0, ABMineBoards1's",
              "-- DustObject3, ABMineBoards2's DBEffectsTrigger3, ABMineBoards3's DustObject15, TorchHolder1's DustOjbect5): each",
              "-- marks Broken<name>."]
        for name, event in BROKEN.items():
            if name == "CaveIn":
                continue
            body = " ".join([f"set(\"Broken{name}\", 1)", *consequence.get(name, [])])
            L.append(f"handlers[{event}] = function() {body} end   -- {name} destroyed")
        L.append("")
        # The abandoned mine's machinery.
        barrels = [b for b in BARREL_CHAIN if has(b)]
        if not hasattr(self, "cart_glide"):
            raise SystemExit("MineCarA is not placed (props.json): the mine cart's script needs it")
        cart_glide, cart_seconds, cart_key = self.cart_glide, self.cart_seconds, self.cart_sound_key
        dust_at = {b: points[f"DustObject{6 + k}"] for k, b in enumerate(BARREL_CHAIN)}
        tf0, tf1 = points["FallingTorchMarker0"], points["FallingTorchMarker1"]
        L += [
            "-- The falling torch (TM_FallingTorch.scr on FallingWallTorch0; TorchHolder0, 1 HP, DeathTrigger TorchTrigger0:",
            "-- broken by a hit or a click, and the torch falls to FallingTorchMarker0). Its flame, TM_TorchFlame.scr, waits",
            "-- 3 s there (:StopHere), then destroys DB_Barrel0 .. DB_Barrel8 one after another (:StartSequence, :Barrel1-8;",
            "-- DustObject6-14, EQHammerImpact.wav, crate_smash.wav), each an Exploding destructible: the shared explode()",
            "-- deals its ExplodeDamage round it. DB_Barrel6/7 run BlowUpTheBoards.scr: ABMineBoards3/2 are destroyed.",
            f"local BARRELS = {{{', '.join(lua_string(b) for b in barrels)}}}",
            f"local BARREL_WAIT = {{{', '.join(f'{w:g}' for b, w in zip(BARREL_CHAIN, BARREL_WAITS) if has(b))}}}",
            f"local BARREL_AT = {{{', '.join(f'{b} = {{' + ', '.join(map(str, dust_at[b])) + '}' for b in barrels)}}}",
            f"handlers[{EV_TORCH0}] = function()   -- also TorchHolder0's destroyed event",
            "    if var(\"Torch0\") ~= 0 then return end",
            "    set(\"Torch0\", 1)",
            "    destroy(\"TorchHolder0\") open(\"FallingWallTorch0\")",
            *[f"    {perception_light_lua(build, light, False)}" for light in LIGHTS_OFF["TorchHolder0"]],
            f"    dust({{{', '.join(map(str, tf0))}}}, 0.5)",
            "    sound(\"events/steam_burst04.wav\")",
            f"    evt.StartTimer({T_BARRELS}, seconds(BARREL_WAIT[1]))",
            "end",
            f"handlers[{T_BARRELS}] = function()",
            "    local step = var(\"Torch0\")",
            "    if step == 0 or step > #BARRELS then evt.StopTimer(" + str(T_BARRELS) + ") return end",
            "    local b = BARRELS[step]",
            "    destroy(b)",
            "    dust(BARREL_AT[b], 1)",
            "    sound(\"weapons/eqhammerimpact.wav\") sound(\"events/crate_smash.wav\")",
            "    if b == \"DB_Barrel7\" then destroy(\"ABMineBoards2\") end   -- BlowUpTheBoards.scr \"ABMineBoards2\"",
            "    if b == \"DB_Barrel6\" then destroy(\"ABMineBoards3\") end   -- BlowUpTheBoards.scr \"ABMineBoards3\"",
            "    set(\"Torch0\", step + 1)",
            f"    if step + 1 <= #BARRELS then evt.StartTimer({T_BARRELS}, seconds(BARREL_WAIT[step + 1])) else "
            f"evt.StopTimer({T_BARRELS}) end",
            "end",
            "",
            "-- The mine cart (TM_MineCarA.scr, hit): Gears02.wav, MCarBlocker1 destroyed (PerceptionLight1 off, DustObject2),",
            "-- the cart rolls to MCarAMarker0 at 100 LT/s, doorslammetal01.wav, ABMineBoards0 destroyed; its DamageTrigger",
            "-- knocks FallingWallTorch1 loose (TM_FirstFallingTorch.scr, 0.6 s: TorchHolder1 destroyed), whose flame",
            "-- (TM_FirstFallingFlame.scr \"DB_Barrel9\") lands, steam_burst04.wav, and 2 s later sets off DB_Barrel9.",
            "-- The cart glides along the track (evt.MoveDecoration; MM9 plays none of its clips), its Gears02.wav loop the",
            f"-- scene's AmbientSound{cart_key} (on for the ride); at the marker its twin, standing there hidden, takes its",
            "-- place: a moved decoration's collision stays where it was placed, the twin's blocks the track's end.",
            f"local CART_GLIDE, CART_SECONDS = {{{', '.join(map(str, cart_glide))}}}, {cart_seconds:g}   -- 100 LT/s",
            f"handlers[{EV_MINECART}] = function()",
            "    if var(\"Cart\") ~= 0 then return end",
            "    set(\"Cart\", 1)",
            f"    set(\"AmbientSound{cart_key}\", 1)",
            "    destroy(\"MCarBlocker1\")",
            *[f"    {perception_light_lua(build, light, False)}" for light in LIGHTS_OFF["MCarBlocker1"]],
            f"    dust({{{', '.join(map(str, points['DustObject2']))}}}, 0.5)",
            f"    evt.MoveDecoration({COG['MineCarA']}, CART_GLIDE[1], CART_GLIDE[2], CART_GLIDE[3], CART_SECONDS)",
            f"    evt.StartTimer({T_CART}, seconds(CART_SECONDS))",
            "end",
            f"handlers[{EV_TORCH1}] = function()",
            "    if var(\"Torch1\") ~= 0 then return end",
            "    set(\"Torch1\", 1)",
            "    destroy(\"TorchHolder1\") open(\"FallingWallTorch1\")",
            *[f"    {perception_light_lua(build, light, False)}" for light in LIGHTS_OFF["TorchHolder1"]],
            "    sound(\"events/steam_burst04.wav\")",
            f"    evt.StartTimer({T_CART}, seconds(2))",
            "end",
            f"handlers[{T_CART}] = function()",
            "    if var(\"Cart\") == 1 then",
            "        set(\"Cart\", 2)",
            f"        set(\"AmbientSound{cart_key}\", 2)   -- :StopHere: KillSound",
            f"        sprite({COG['MineCarA']}, false) sprite({COG['MineCarA_end']}, true)",
            "        sound(\"door/doorslammetal01.wav\")",
            "        destroy(\"ABMineBoards0\")   -- its destroyed event: the dust and the quake (DBEffectsTrigger0)",
            "        handlers[" + str(EV_TORCH1) + "]()",
            "        return",
            "    end",
            "    if var(\"Torch1\") == 1 then",
            "        set(\"Torch1\", 2)",
            "        destroy(\"DB_Barrel9\")   -- TM_FirstFallingFlame.scr \"DB_Barrel9\": Destroy (it explodes)",
            f"        dust({{{', '.join(map(str, points['DustObject17']))}}}, 1)",
            "        sound(\"weapons/eqhammerimpact.wav\") sound(\"events/crate_smash.wav\")",
            "    end",
            f"    evt.StopTimer({T_CART})",
            "end",
            "",
            "-- The falling board (FallingBoard0, PushOpen, Sticky, no closing): it falls once (OpenTriggers: lock,",
            "-- DustObject4, DBQuakeObject2, PerceptionLight5 off).",
            f"handlers[{EV_FALLBOARD}] = function()",
            "    if var(\"FallingBoard\") == 1 then return end",
            "    set(\"FallingBoard\", 1)",
            "    open(\"FallingBoard0\")",
            *[f"    {perception_light_lua(build, light, False)}" for light in LIGHTS_OFF["FallingBoard0"]],
            f"    dust({{{', '.join(map(str, points['DustObject4']))}}}, 1)",
            "    quake(\"DBQuakeObject2\")",
            "end",
            "",
            "-- The steam valve (SteamValve0; OpenTriggers: PressuredWater0/1 On, BlueWater0 MoveWater): the jet of water",
            "-- (TM_SteamWater.scr) shoots down the pipe to WaterMarker0 and smashes ABMineBoards1 (DustObject3); the valve",
            "-- then locks open. The jet is not built: the boards break after its run (about a second).",
            f"handlers[{EV_VALVE}] = function()",
            "    if var(\"Valve\") ~= 0 then return end",
            "    set(\"Valve\", 1)",
            "    open(\"SteamValve0\")",
            *[f"    {perception_light_lua(build, light, False)}" for light in LIGHTS_OFF["SteamValve0"]],
            "    sound(\"events/steam_burst04.wav\")",
            f"    evt.SpawnWorldEffect(\"mm9:smokestack\", {', '.join(map(str, points['PressuredWater0']))}, 0.4)",
            f"    evt.StartTimer({T_VALVE}, seconds(1))",
            "end",
            f"handlers[{T_VALVE}] = function()",
            "    if var(\"Valve\") ~= 1 then evt.StopTimer(" + str(T_VALVE) + ") return end",
            "    set(\"Valve\", 2)",
            "    destroy(\"ABMineBoards1\")   -- its destroyed event: crate_smash.wav, DustObject3",
            f"    evt.StopTimer({T_VALVE})",
            "end",
            "",
        ]
        # The slag extractor and Hjarrand.
        hj, gud = objects.get("CommonerDwarfMaleB4"), objects.get("CommonerDwarfMaleB1")
        gx, gy, gz = points["Marker3"]
        slag_hint = hint.get("PerceptionBrush0")
        L += [
            "-- The slag extractor's hatch (RotatingDoor0; OpenTrigger PerceptionBrush0 off, CloseTrigger on).",
            f"handlers[{EV_SLAG_HATCH}] = function()",
            "    evt.SetDoorState(DOORS.RotatingDoor0, DoorAction.Trigger)",
            f"    hideHint({slag_hint})" if slag_hint else "",
            "end",
            "-- The broken slag extractor (SlagExtractor.scr :OnUse): without key 9512 it gives item 398 and key 9512 and is",
            "-- gone. :OnShow (sent by the base, SlagBase.scr, to a party holding item 399): 5000 experience, the quest sound,",
            "-- the whole part in its place (SetModelFilenames Machine-Part_Whole), item 399 taken, key 37.",
            "local function showSlag()",
            f"    local taken, fixed = MM9.hasKey({KEY_EXTRACTOR}) == 1, MM9.hasKey({KEY_FIXED}) == 1",
            f"    sprite({COG['slag']}, not taken and not fixed)" if has("slag") else "",
            f"    sprite({COG['slag_whole']}, fixed)" if has("slag_whole") else "",
            "end",
            f"handlers[{EV_SLAG}] = function()",
            f"    if MM9.hasKey({KEY_EXTRACTOR}) == 1 or MM9.hasKey({KEY_FIXED}) == 1 then return end",
            f"    if MM9.giveItem({ITEM_BROKEN}, \"thjoradmine:slag\") then",
            f"        MM9.giveKey({KEY_EXTRACTOR})",
            "        showSlag()",
            "    end",
            "end",
            f"handlers[{EV_SLAGBASE}] = function()",
            f"    if MM9.hasKey({KEY_FIXED}) == 1 then return end",
            f"    if MM9.hasItem({ITEM_REPLACEMENT}, \"thjoradmine:slagbase\") == 0 then return end",
            f"    {experience_lua(FIX_EXPERIENCE, KEY_FIXED)}",
            "    MM9.playSound(\"sounds\\\\events\\\\quest.wav\")",
            f"    MM9.takeItem({ITEM_REPLACEMENT}, \"thjoradmine:slagbase\")",
            f"    MM9.giveKey({KEY_FIXED})",
            "    showSlag()",
            "end",
            "-- Hjarrand the Fixer (NPC7.scr, Location \"Refinery\"): in the mine only once paid (key 362; :Init clears",
            "-- visible, solid and gravity otherwise). When his dialogue closes, without key 364, he walks to MMarker1 and",
            "-- paces to MMarker2, MMarker1 and MMarker2, rubbing his beard at each, walks to the Machine, gives key 364, looks",
            "-- at the slag extractor (clip x) and walks off to MMarker3. HjarrandStop is the leg he walks (1-6, 7: done);",
            "-- HjarrandMoving holds the poll off until the leg's arrival event runs (a map load drops the walk: the poll",
            "-- sends him on the same leg again).",
        ]
        if hj is not None:
            stops = [points[n] for n in ("MMarker1", "MMarker2", "MMarker1", "MMarker2", "Machine", "MMarker3")]
            sx, sy, _ = points["slag"]
            L += [f"local HJARRAND = {actor['CommonerDwarfMaleB4']}",
                  "local HJARRAND_STOPS = {" + ", ".join(lua.point(p) for p in stops) + "}",
                  "local function showHjarrand()",
                  f"    evt.SetMonsterBit(HJARRAND, MonsterBits.Invisible, MM9.hasKey({KEY_PAID}) == 0)",
                  "end",
                  "local function hjarrandWalk()   -- the poll",
                  "    local k = var(\"HjarrandStop\")",
                  "    if k == 0 or k > #HJARRAND_STOPS or var(\"HjarrandMoving\") == 1 then return end",
                  "    local wait = var(\"HjarrandWait\")",
                  "    if wait > 0 then set(\"HjarrandWait\", wait - 1) return end",
                  "    local p = HJARRAND_STOPS[k]",
                  "    evt.ClearActorPresentation(HJARRAND)",
                  f"    if evt.MoveActorTo(HJARRAND, p[1], p[2], p[3], {EV_HJARRAND_ARRIVE}) then set(\"HjarrandMoving\", 1) end",
                  "end",
                  f"handlers[{rude_exit_event(hj)}] = function()   -- Hjarrand: :OnRude, wait .5, :Refinery2",
                  f"    if MM9.hasKey({KEY_PAID}) == 0 or MM9.hasKey({KEY_SHOWN}) == 1 or var(\"HjarrandStop\") ~= 0 then return end",
                  "    set(\"HjarrandStop\", 1) set(\"HjarrandWait\", 2)",
                  "end",
                  f"handlers[{EV_HJARRAND_ARRIVE}] = function()   -- :OnArrive, :OnMarkMachine, :WalkAway's OnExit",
                  "    local k = var(\"HjarrandStop\")",
                  "    set(\"HjarrandMoving\", 0)",
                  "    if k == 0 or k > #HJARRAND_STOPS then return end",
                  "    set(\"HjarrandStop\", k + 1)",
                  "    if k <= 4 then",
                  "        evt.PlayActorClip(HJARRAND, \"rub_beard\")",
                  f"        set(\"HjarrandWait\", {HJARRAND_PAUSE})",
                  "    elseif k == 5 then",
                  f"        MM9.giveKey({KEY_SHOWN})",
                  f"        evt.FaceActorTo(HJARRAND, {sx}, {sy}, 0.4)",
                  "        evt.PlayActorClip(HJARRAND, \"x\")",
                  f"        set(\"HjarrandWait\", {HJARRAND_PAUSE})",
                  "    end",
                  "end"]
            script.add([], (rude_exit_event(hj), "Hjarrand", None), (EV_HJARRAND_ARRIVE, "Hjarrand arrives", None))
        if gud is not None:
            L += ["-- Gudrek the Miner (NPC8.scr :OnRude): with key 9510 he walks to Marker3, by the cave-in, and gives key 9511",
                  f"-- on arrival. While the party is more than 256 LT ({LEAD_DISTANCE}) away he stops and faces it (OnTargetBeyondDist),",
                  "-- and walks on once it is within (OnTargetWithinDist). GudrekLead: 1 leading, 2 arrived; GudrekMoving as",
                  "-- HjarrandMoving.",
                  f"local GUDREK = {actor['CommonerDwarfMaleB1']}",
                  "local function gudrekLead()   -- the poll",
                  "    if var(\"GudrekLead\") ~= 1 then return end",
                  "    local x, y = evt.GetMapActorPosition(GUDREK)",
                  "    if x == nil then return end",
                  "    local px, py = evt.GetPartyPosition()",
                  f"    if (x - px) ^ 2 + (y - py) ^ 2 > {LEAD_DISTANCE} ^ 2 then",
                  "        if var(\"GudrekMoving\") == 1 and evt.StopActorMove(GUDREK) then set(\"GudrekMoving\", 0) end",
                  "        if var(\"GudrekMoving\") == 0 then evt.FaceActorTo(GUDREK, px, py, 0.25) end",
                  "    elseif var(\"GudrekMoving\") == 0 then",
                  "        evt.ClearActorPresentation(GUDREK)",
                  f"        if evt.MoveActorTo(GUDREK, {gx}, {gy}, {gz}, {EV_GUDREK_ARRIVE}) then set(\"GudrekMoving\", 1) end",
                  "    end",
                  "end",
                  f"handlers[{rude_exit_event(gud)}] = function()   -- Gudrek",
                  f"    if MM9.hasKey({KEY_LEAD}) == 0 or MM9.hasKey({KEY_LED}) == 1 or var(\"GudrekLead\") ~= 0 then return end",
                  "    set(\"GudrekLead\", 1)",
                  "end",
                  f"handlers[{EV_GUDREK_ARRIVE}] = function()   -- :OnExit",
                  "    set(\"GudrekMoving\", 0)",
                  "    if var(\"GudrekLead\") ~= 1 then return end",
                  "    set(\"GudrekLead\", 2)",
                  "    evt.ClearActorPresentation(GUDREK)",
                  f"    MM9.giveKey({KEY_LED})",
                  "end"]
            script.add([], (rude_exit_event(gud), "Gudrek", None), (EV_GUDREK_ARRIVE, "Gudrek arrives", None))
        L += [
            "",
            f"-- The troglodyte spawns (SpawnMgr.scr \"1 1 Troglodyte TriggerSpawn\", SpawnLoc.scr on SpawnMarker0-6): each",
            "-- TriggerLocation sends `spawn` to its marker (TriggerLocation0 three times, then the manager Off), one troglodyte",
            f"-- appears there and hunts the party; none once {SPAWN_CAP} of them have died. Each trigger fires once.",
            f"local SPAWNED = {{{spawned}}}",
            f"local SPAWN_ACTOR = {{{spawn_actors}}}",
            "local function spawnAt(marker, count)",
            f"    if var(\"SpawnKilled\") >= {SPAWN_CAP} then return end",
            "    local list = SPAWNED[marker]",
            "    for _, index in ipairs(list) do",
            "        if count == 0 then return end",
            "        local key = \"Spawned\" .. index",
            "        if var(key) == 0 then",
            "            set(key, 1)",
            "            evt.SetMonsterBit(index, MonsterBits.Invisible, false)",
            "            evt.SetMonsterBit(index, MonsterBits.Hostile, true)",
            "            count = count - 1",
            "        end",
            "    end",
            "end",
            f"handlers[{KILL_HOOK}] = function(context)",
            "    if SPAWN_ACTOR[context.actorIndex] then set(\"SpawnKilled\", var(\"SpawnKilled\") + 1) end",
            "end",
            f"handlers[{DAMAGE_HOOK}] = function(context)",
            f"    if context.actorIndex == {actor['Ebora']} then freeEbora() end   -- EboraMines.scr: OnDamage FreeAtLast",
            "end",
        ]
        for trigger, event in EV_SPAWN.items():
            marker = "SpawnMarker" + trigger[len("TriggerLocation")]
            L.append(f"handlers[{event}] = function() spawnAt(\"{marker}\", {3 if trigger == 'TriggerLocation0' else 1}) end"
                     f"   -- {trigger}")
        L += [
            "",
            "-- The touch Triggers, polled four times a second (fire on any part of the party in the box, once).",
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z + 170 >= b[1][3] and z <= b[2][3] end",
            "local BOXES = {" + ", ".join(
                f"{{name = \"{n}\", event = {e}, box = {{{lua.point(b[0])}, {lua.point(b[1])}}}}}"
                for n, (e, b) in self.boxes.items()) + "}",
            "local BLOWUP = {" + ", ".join(f"{b} = \"{boards}\"" for b, boards in
                                          (("DB_Barrel7", "ABMineBoards2"), ("DB_Barrel6", "ABMineBoards3"))
                                          if has(b)) + "}   -- BlowUpTheBoards.scr ScriptParams",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    hjarrandWalk()" if hj is not None else "",
            "    gudrekLead()" if gud is not None else "",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for _, b in ipairs(BOXES) do",
            "        if var(\"Fired\" .. b.name) == 0 and inBox(b.box, x, y, z) then",
            "            set(\"Fired\" .. b.name, 1)",
            "            handlers[b.event]()",
            "        end",
            "    end",
            "    -- BlowUpTheBoards.scr: DB_Barrel7/6's own DeathTrigger sends them HitMe however they broke (a shot, a",
            "    -- neighbour's blast, the torch chain): a destroyed barrel keeps its script and breaks its boards.",
            "    for barrel, boards in pairs(BLOWUP) do",
            "        if evt.IsDestructibleDestroyed(BREAKABLE[barrel]) and not evt.IsDestructibleDestroyed(BREAKABLE[boards]) then",
            "            sound(\"weapons/eqhammerimpact.wav\") sound(\"events/crate_smash.wav\")",
            "            destroy(boards)",
            "        end",
            "    end",
            "end",
            "",
            f"-- The PerceptionBrushes (PerceptionValue {self.hint_difficulty}): the red glow shows to a party with that "
            "Perception;",
            "-- a hint whose object was used stays off. On load and every 3 s.",
            f"local HINTS = {{{', '.join(str(c) for c in hint.values())}}}",
            "local function updateHints()",
            f"    local want = evt.CheckSkill({PERCEPTION_SKILL}, 0, {self.hint_difficulty}) and 2 or 1",
            "    for _, cog in ipairs(HINTS) do",
            "        evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or var(\"HintOff\" .. cog) == 1)",
            "    end",
            "end",
            f"handlers[{T_HINTS}] = updateHints",
            "",
        ]
        for name, (event, number) in EV_LETTERS.items():
            title, text = letter(number)
            L += [f"-- {name}: BookLetter.scr \"{number} Letter\" (DoLetter {number}).",
                  f"handlers[{event}] = function() sound(\"events/bookopen.wav\") "
                  f"evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end"]
        # Map load: restore what MM9 restores (OnPostMiniSaveLoad) and what the native world keeps only as variables.
        hide = []
        for wall in EV_BAR:
            hide.append(f"    if var(\"{wall}Open\") == 1 then open(\"{wall}\") end")
        for s in SPIKES:
            hide.append(f"    if var(\"{s}\") == 1 then open(\"{s}\") end")
        L += [
            f"handlers[{EV_LOAD}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    set(\"RefineryBusy\", 0) set(\"HjarrandMoving\", 0) set(\"GudrekMoving\", 0)",
            "    showSlag()",
            "    showHjarrand()" if hj is not None else "",
            f"    if var(\"EboraFree\") == 1 or var(\"EboraFree\") == 2 then MM9Cinematic.finish({lua_string(CINEMA_ID)}) end",
            f"    if var(\"EboraFree\") >= 3 then MM9.removeActor({actor['Ebora']}) end",
            f"    evt.StartTimer({T_QUAKE}, seconds(evt.RandomBetween({AMBIENT_QUAKE['every'][0]}, {AMBIENT_QUAKE['every'][1]})))",
            f"    sprite({COG['MineCarA_end']}, var(\"Cart\") >= 2)",
            f"    sprite({COG['MineCarA']}, var(\"Cart\") < 2)",
            "    -- the glide is runtime only: a cart on its way (or gone) stands at its end again",
            f"    if var(\"Cart\") >= 1 then evt.MoveDecoration({COG['MineCarA']}, CART_GLIDE[1], CART_GLIDE[2], CART_GLIDE[3], 0) end",
            "    updateHints()",
            "end",
            "",
        ]
        events = [(e, "Locked door", "Door") for e in (EV_LOCKED,)]
        events += [(EV_HANDLE, "Handle", "Door"), (EV_GATE0, "Lever", "Lever"), (EV_GATE1, "Lever", "Lever")]
        events += [(e, w, "Door") for w, e in EV_BAR.items()]
        events += [(e, "Spike", "Spike") for e in EV_SPIKE.values()]
        events += [(e, "Hard rock", "Rock") for e in EV_ROCK.values()]
        events += [(EV_CAVEWALL["CaveWall0"], "Cave wall", "Rock"), (EV_STALACTITE, "Stalactite", "Rock"),
                   (EV_TORCH0, "Torch", "Torch"), (EV_TORCH1, "Torch", "Torch"), (EV_MINECART, "Mine cart", "Mine cart"),
                   (EV_FALLBOARD, "Board", "Board"), (EV_VALVE, "Valve", "Valve"), (EV_SLAG_HATCH, "Hatch", "Hatch"),
                   (EV_SLAG, "Slag extractor", "Slag extractor"), (EV_SLAGBASE, "Machine", "Machine"),
                   (EV_CAVEIN, "Cave-in", None), (EV_HARDROCK, "TriggerHardRock", None)]
        events += [(e, w, "Wall") for w, e in EV_BUSTOUT.items()]
        events += [(e, f"{n} destroyed", None) for n, e in BROKEN.items()]
        events += [(e, "Door", "Door") for e in EV_PLAIN.values()]
        events += [(e, t, None) for t, e in EV_SPAWN.items()]
        events += [(e, "Letter", "Letter") for e, _ in EV_LETTERS.values()]
        events += [(T_POLL, "Trigger volumes", None, "timer"), (T_QUAKE, "Quake", None, "timer"),
                   (T_BARRELS, "Barrels", None, "timer"), (T_CART, "Mine cart", None, "timer"),
                   (T_VALVE, "Valve", None, "timer"), (T_HINTS, "Perception hints", None, "timer"),
                   (T_REFINERY, "Refinery handle", None, "timer"),
                   (EV_LOAD, "Map load", None)]
        script.add(L, *events)
        script.hooks += [f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Ebora hurt", handlers[{DAMAGE_HOOK}])',
                         f'RegisterMonsterKilledHook({KILL_HOOK}, "Spawn killed", handlers[{KILL_HOOK}])']
        self.scenes = ebora_scenes(actor["Ebora"])
        return script.finish(on_load=[EV_LOAD]) + cutscenes.lua_block(self.scenes)

    def report(self, build) -> dict:
        return {"pool_faces": getattr(self, "pool_faces", 0), "pool_y_lt": getattr(self, "pool_y", None),
                "scripted": {"actors": self.actor, "spawned": self.spawned, "gnolls": self.gnolls,
                             "points": self.points, "boxes": {k: v for k, v in self.boxes.items()},
                             "hints": self.hints}}


if __name__ == "__main__":
    hooks = ThjoradMine()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv) and getattr(hooks, "scenes", None):
        print(f"cinematics installed: {cutscenes.install(STEM, hooks.scenes)} (ebora_free)")
    sys.exit(code)
